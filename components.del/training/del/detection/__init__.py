# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from datetime import datetime
from uuid import UUID
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, computed_field


ExecutionStatus = Literal["PROCESSING", "DONE", "ERROR"]


class Clp(BaseModel):
    model_config = ConfigDict(extra="ignore")
    execution_id: UUID
    box_id: int
    x: float
    y: float
    z: float
    created_on: datetime = Field(default=datetime.now())
    modified_on: datetime = Field(default=datetime.now())


class Box(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:Optional[int] = None
    execution_id: UUID
    image_key:str
    x1: int
    x2: int
    y1: int
    y2: int
    width: float
    height: float
    depth: float
    inplan: bool = Field(default=False)
    created_on: datetime = Field(default=datetime.now())
    modified_on: datetime = Field(default=datetime.now())

    @computed_field
    @property
    def volume(self) -> float:
        return self.width * self.height * self.depth

    @computed_field
    @property
    def bbox(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return (self.x1, self.y1), (self.x2, self.y2)


class PredictedImage(BaseModel):
    id:UUID
    url:str
    boxes:List[Box]


class Execution(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    container_width: float
    container_height: float
    container_depth: float
    status: ExecutionStatus = Field(default="PROCESSING")
    status_message: Optional[str] = None
    plan_remarks: Optional[str] = None
    predicted_images:List[PredictedImage] = Field(default=[])
    plan: List[Clp] = Field(default=[])
    created_on: datetime = Field(default=datetime.now())
    modified_on: datetime = Field(default=datetime.now())


    @computed_field
    @property
    def total_boxes(self) -> int:
        return sum([len(pi.boxes) for pi in self.predicted_images ]) if self.predicted_images is not None else 0

    @computed_field
    @property
    def total_volume(self) -> float:
        return sum([b.volume for pi in self.predicted_images for b in pi.boxes]) if self.predicted_images is not None else 0


class Executions(BaseModel):
    executions: List[Execution]


class UploadImageRequest(BaseModel):
    id: UUID
    filename: str


class UploadImagesRequest(BaseModel):
    files:List[UploadImageRequest]


class UploadImageResponse(BaseModel):
    id:UUID
    url:str


class UploadImagesResponse(BaseModel):
    id: UUID
    urls: List[UploadImageResponse]


class DownloadImagesRequest(BaseModel):
    id:UUID


class DownloadImagesResponse(BaseModel):
    urls: List[str]


class GeneratedClpPlan(BaseModel):
    plan:List[Clp]
    left_over_boxes:List[int]
    remarks:str

class DetectionConfig(BaseModel):
    box_model: str = Field(default="best.pt")
    sam_model: str = Field(default="sam2_t.pt")
    confidence_threshold: float = Field(default=0.5)
    iou_threshold: float = Field(default=0.45)
