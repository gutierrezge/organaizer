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


class DimSide(BaseModel):
    value:float
    point1:tuple[int, int]
    point2:tuple[int, int]


class Dimensions(BaseModel):
    sides:List[DimSide]

    @computed_field
    @property
    def side1(self) -> DimSide:
        return self.sides[0]
    
    @computed_field
    @property
    def side2(self) -> DimSide:
        return self.sides[1]

    @computed_field
    @property
    def side3(self) -> DimSide:
        return self.sides[2]
    
    @computed_field
    @property
    def side4(self) -> DimSide:
        return self.sides[3]
    
    @computed_field
    @property
    def side5(self) -> DimSide:
        return self.sides[4]

    @computed_field
    @property
    def side6(self) -> DimSide:
        return self.sides[5]

    @computed_field
    @property
    def volume(self) -> float:
        if not self.sides:
            return 0
        volume = 1
        for side in self.sides:
            volume *= side.value
        return volume


class Prediction(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: UUID
    frame: np.ndarray
    painted_frame:np.ndarray
    bbox:Optional[np.ndarray] = Field(default=None)
    mask:Optional[np.ndarray] = Field(default=None)
    corners:Optional[np.ndarray]  = Field(default=None)
    dimensions:Optional[Dimensions] = Field(default=None)

    @cached_property
    def size(self) -> tuple[int, int]:
        return int(self.frame.shape[1]), int(self.frame.shape[0])

    @cached_property
    def short_id(self) -> str:
        return str(self.id)[-12:]
    
    def is_complete(self) -> bool:
        return self.frame is not None and self.bbox is not None and self.painted_frame is not None \
            and self.mask is not None and self.corners is not None and self.dimensions is not None
    