# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from datetime import datetime
import numpy as np
from functools import cached_property
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field
import utils

class Box(BaseModel):
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)
    id:UUID
    execution_id: UUID
    frame:np.ndarray
    x1: int
    x2: int
    y1: int
    y2: int
    width: float
    height: float
    depth: float
    inplan: bool = Field(default=False)
    created_on: datetime = Field(default=datetime.now())

    @computed_field
    @property
    def volume(self) -> float:
        return self.width * self.height * self.depth

    @computed_field
    @property
    def bbox(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return (self.x1, self.y1), (self.x2, self.y2)
    
    @computed_field
    @cached_property
    def short_id(self) -> str:
        return str(self.id)[-12:]


class Execution(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    container_width: float = Field(default=0.0)
    container_height: float = Field(default=0.0)
    container_depth: float = Field(default=0.0)
    boxes:List[Box] = Field(default=[])
    created_on: datetime = Field(default=datetime.now())

    @computed_field
    @property
    def total_boxes(self) -> int:
        return len(self.boxes) if self.boxes is not None else 0

    @computed_field
    @property
    def total_volume(self) -> float:
        return sum([b.volume for b in self.boxes]) if self.boxes is not None else 0


class ClpItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    box_id: UUID
    x: float
    y: float
    z: float
    created_on: datetime = Field(default=datetime.now())

    @cached_property
    def short_id(self) -> str:
        return str(self.box_id)[-12:]


class GeneratedClpPlan(BaseModel):
    plan:List[ClpItem] = Field(default=[])
    left_over_boxes:List[UUID] = Field(default=[])
    remarks:str = Field(default='')



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

        front = utils.sort_values(np.array([lowest_point, second_lowest_point, pair_to_seccond_lowest_point]))
        back=corners[
            (corners != lowest_point).all(axis=1) & 
            (corners != second_lowest_point).all(axis=1) &
            (corners != pair_to_seccond_lowest_point).all(axis=1)
        ]
        back = utils.sort_values(np.array(back))
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
    painted_frame:np.ndarray
    bbox:Optional[np.ndarray] = Field(default=None)
    mask:Optional[np.ndarray] = Field(default=None)
    corners:Optional[IdentifiedCornersPoints]  = Field(default=None)
    dimensions:Optional[Dimensions] = Field(default=None)

    @cached_property
    def size(self) -> tuple[int, int]:
        return int(self.frame.shape[1]), int(self.frame.shape[0])

    @cached_property
    def short_id(self) -> str:
        return str(self.id)[-12:]