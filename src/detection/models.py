# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import cv2
from uuid import UUID
from typing import List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from functools import cached_property
from typing import Optional
import numpy as np


def sort_values(corners:Optional[np.ndarray]) -> Optional[np.ndarray]:
    if corners is None or len(corners) <= 0:
        return None
    corners = np.unique(corners, axis=0)
    corners = corners.reshape(-1, 2)    
    center = np.mean(corners, axis=0)
    angles = np.arctan2(corners[:, 1] - center[1], corners[:, 0] - center[0])
    sorted_indices = np.argsort(angles)
    corners = corners[sorted_indices]
    distances = np.linalg.norm(corners, axis=1)
    top_left_idx = np.argmin(distances)
    corners = np.roll(corners, -top_left_idx, axis=0)    
    return corners.reshape(-1, 1, 2)


class Clp(BaseModel):
    model_config = ConfigDict(extra="ignore")
    execution_id: UUID
    box_id: UUID
    x: float
    y: float
    z: float
    created_on: datetime = Field(default=datetime.now())
    modified_on: datetime = Field(default=datetime.now())

    @cached_property
    def short_id(self) -> str:
        return str(self.box_id)[-12:]


class GeneratedClpPlan(BaseModel):
    plan:List[Clp]
    left_over_boxes:List[UUID]
    remarks:str


class IdentifiedCornersPoints(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    front:np.ndarray
    back:np.ndarray

    @cached_property
    def sorted_front_by_y(self) -> np.ndarray:
        return self.front[np.argsort(self.front[:, 1])]

    @cached_property
    def sorted_back_by_y(self) -> np.ndarray:
        return self.back[np.argsort(self.back[:, 1])]

    @cached_property
    def lowest_front_point(self) -> np.ndarray:
        return self.sorted_front_by_y[-1]
    
    @cached_property
    def lowest_back_point(self) -> np.ndarray:
        return self.sorted_back_by_y[-1]
    
    @cached_property
    def highest_front_point(self) -> np.ndarray:
        return self.sorted_front_by_y[0]
    
    @cached_property
    def highest_back_point(self) -> np.ndarray:
        return self.sorted_back_by_y[0]
    
    @cached_property
    def middle_highest_front_point(self) -> np.ndarray:
        return self.sorted_front_by_y[1]
    
    @cached_property
    def middle_highest_back_point(self) -> np.ndarray:
        return self.sorted_back_by_y[1]
    
    @cached_property
    def middle_front_point(self) -> np.ndarray:
        y = self.lowest_front_point[1] - (self.middle_highest_front_point[1] - self.highest_front_point[1])
        return np.array([self.lowest_front_point[0], y])
    
    @classmethod
    def build(cls, corners:np.ndarray):
        if corners is None or len(corners) != 6:
            return None

        corners:np.ndarray = corners.reshape(-1, 2)
        
        sorted_by_y = corners[np.argsort(corners[:, 1])]
        lowest_point = sorted_by_y[-1]
        second_lowest_point = sorted_by_y[-2]

        candidates = corners[
            (corners != lowest_point).all(axis=1) & 
            (corners != second_lowest_point).all(axis=1)
        ]
        pair_to_seccond_lowest_point = candidates[np.argmin(np.abs(candidates[:, 0] - second_lowest_point[0]))]

        front = sort_values(np.array([lowest_point, second_lowest_point, pair_to_seccond_lowest_point]))
        back=corners[
            (corners != lowest_point).all(axis=1) & 
            (corners != second_lowest_point).all(axis=1) &
            (corners != pair_to_seccond_lowest_point).all(axis=1)
        ]
        back = sort_values(np.array(back))
        return cls(front=front.squeeze(), back=back.squeeze())
    

class Dimensions(BaseModel):
    width:float
    height:float
    depth:float

    @property
    def volume(self):
        return self.width * self.height * self.depth


class Prediction(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: UUID
    frame: np.ndarray
    bbox:Optional[np.ndarray] = Field(default=None)
    mask:Optional[np.ndarray] = Field(default=None)
    dimensions:Optional[Dimensions] = Field(default=None)
    corners:Optional[IdentifiedCornersPoints]  = Field(default=None)
    draw_bbox:bool = Field(default=True)
    draw_corners:bool = Field(default=True)
    draw_labels:bool = Field(default=False)
    draw_mask:bool = Field(default=True)
    draw_edges:bool = Field(default=False)
    draw_dimensions:bool = Field(default=True)

    @cached_property
    def size(self) -> tuple[int, int]:
        return int(self.frame.shape[1]), int(self.frame.shape[0])

    @cached_property
    def short_id(self) -> str:
        return str(self.id)[-12:]

    @cached_property
    def painted_frame(self) -> np.ndarray:
        return plot_prediction(self.frame.copy(), self)


def plot_prediction(frame: np.ndarray, prediction: Optional[Prediction]) -> np.ndarray:
    thickness:int = 4
    font:int = cv2.FONT_HERSHEY_PLAIN
    scale:float = 2
    line_type:int = cv2.LINE_AA
    blue:tuple[int, int, int] = (255, 0, 0)
    green:tuple[int, int, int] = (0, 255, 0)
    red:tuple[int, int, int] = (0, 0, 255)
    white:tuple[int, int, int] = (255, 255, 255)
    circle_size = 5

    if prediction.draw_bbox and prediction.bbox is not None:
        x1, y1, x2, y2 = prediction.bbox
        frame = cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color=green,
            thickness=thickness,
            lineType=line_type
        )

    if prediction.draw_mask and prediction.mask is not None:
        mask2:np.ndarray = np.zeros_like(frame)
        mask2[prediction.mask == True] = red
        frame:np.ndarray = cv2.addWeighted(frame, 1, mask2, 0.5, 0)

        if mask2.dtype != np.uint8:
            mask2:np.ndarray = mask2.astype(np.uint8)
    
        if len(mask2.shape) > 2:
            mask2:np.ndarray = cv2.cvtColor(mask2, cv2.COLOR_BGR2GRAY)
        
        if prediction.draw_edges:
            contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(frame, contours, -1, red, thickness, line_type)
            if prediction.corners is not None:
                cv2.line(frame, prediction.corners.middle_front_point, prediction.corners.lowest_front_point, red, thickness, line_type)
                cv2.line(frame, prediction.corners.middle_front_point, prediction.corners.highest_front_point, red, thickness, line_type)
                cv2.line(frame, prediction.corners.middle_front_point, prediction.corners.middle_highest_back_point, red, thickness, line_type)

    if prediction.draw_corners and prediction.corners is not None:
        for i, corner in enumerate(prediction.corners.front):
            x, y = corner.ravel()
            cv2.circle(frame, (x, y), circle_size, blue, -1, line_type)
            if prediction.draw_labels:
                cv2.putText(frame, f'{i} - F - ({x},{y})', (x+5, y), font, scale*2, blue, thickness, line_type)
        for i, corner in enumerate(prediction.corners.back):
            x, y = corner.ravel()
            cv2.circle(frame, (x, y), circle_size, blue, -1, line_type)
            if prediction.draw_labels:
                cv2.putText(frame, f'{i} - B - ({x},{y})', (x+5, y), font, scale*2, blue, thickness, line_type)
        
        x, y = prediction.corners.middle_front_point.ravel()
        cv2.circle(frame, (x, y), circle_size, blue, -1, line_type)
        if prediction.draw_labels:
            cv2.putText(frame, f'MF - ({x},{y})', (x+5, y), font, scale*2, blue, thickness, line_type)

    if prediction.draw_dimensions and prediction.dimensions is not None:
        text = f'w={prediction.dimensions.width:.02f}, h={prediction.dimensions.height:.02f}, d={prediction.dimensions.depth:.02f}'
        cv2.rectangle(frame, (0,0), (frame.shape[1], 20), white, -1, line_type)
        cv2.putText(frame, text, (10,15), cv2.FONT_HERSHEY_PLAIN, 1, blue, 1, line_type)
        
    return frame