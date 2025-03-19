from pydantic import BaseModel, ConfigDict, Field
from functools import cached_property
from typing import Optional, List
import numpy as np
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s",
)

def sort_values(corners:Optional[np.ndarray]) -> Optional[np.ndarray]:
    if corners is None and len(corners) == 0:
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


class Prediction(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    bbox:Optional[np.ndarray]
    mask:Optional[np.ndarray] = Field(default=None)
    dimensions:Optional[Dimensions] = Field(default=None)
    corners:Optional[IdentifiedCornersPoints]  = Field(default=None)
    draw_bbox:bool = Field(default=False)
    draw_corners:bool = Field(default=True)
    draw_labels:bool = Field(default=False)
    draw_mask:bool = Field(default=True)
    draw_edges:bool = Field(default=True)
    draw_dimensions:bool = Field(default=True)