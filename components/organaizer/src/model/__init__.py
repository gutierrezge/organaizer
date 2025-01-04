from datetime import datetime
from uuid import UUID
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, computed_field


ExecutionStatus = Literal["PROCESSING", "DONE", "ERROR"]


class Clp(BaseModel):
    model_config = ConfigDict(extra="ignore")
    execution_id: UUID
    box_id: int
    x: int
    y: int
    z: int
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


class DetectedBoxResult(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int
    class_name: str


class DetetionConfig(BaseModel):
    model: str = Field(default="best.pt")
    confidence_threshold: float = Field(default=0.5)
    iou_threshold: float = Field(default=0.45)
