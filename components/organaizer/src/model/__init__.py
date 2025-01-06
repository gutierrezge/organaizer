from datetime import datetime
from uuid import UUID
import numpy as np
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

class EstimatedDimensions(BaseModel):
    width: float
    height: float
    depth: float


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


class DetectedBoxResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    x1: int
    y1: int
    x2: int
    y2: int
    mask:Optional[np.ndarray] = None


class GenAIConfig(BaseModel):
    model:str = Field(default="claude-3-5-sonnet-20241022")
    max_tokens:int = Field(default=300)
    image_instructions:str = Field(default=""""Goal: Provide the approximated values for the width, height, depth in centimeters of the box in the image using the aruco of 3.5 by 3.5 centimeters that comes in it. Do not return anything else but a JSON string. Example json return {\"width\": 45.3, \"height\":5.56, \"depth\":6.72}""")
    clp_instructions:str = Field(default="""Goal: Create a container loading plan for a container of width={width}, height={height} and depth={depth} returning a JSON object having the following attributes:
 plan: a list of objects having the execution_id ({execution_id}), box_id, x, y and z box order coordinates, for example: [{{ \"exeution_id\": \"4a41abd9-69dd-4da4-af97-9a6178992591\", \"box_id\": 1, \"x\": 0, \"y\":0, \"z\":0}}, {{ \"exeution_id\": \"4a41abd9-69dd-4da4-af97-9a6178992591\", \"box_id\": 2, \"x\": 1, \"y\":0, \"z\":0}}, ...]
 left_over_boxes: a list of integers containing the box_id that did not fit due to overload
 remarks: a string to comment if all boxes fitted in the container or the total amount of boxes that did not fit.
The order of the boxes must be from left to right (x), bottom to top (y), back to forth (z)
The x,y and z values are not coordinates but the box order a value of 4,0,0,0 means box 4 goes the very first where the 5,1,0,0 means that box 5 goes next to box 4.
Make sure that as boxes are planed into order they do not overflow the containers dimension.
Boxes in y-axis must have boxes below to support it. Boxes in z-axis must have boxes behind to support them.
Take your time to validate the plan and Do not return a response until the plan has been validated.
Do not return anything else but a JSON string.
The following data is a CSV format with the box_id, box_width, box_height and box_depth.
{boxes}""")


class GenerateClpPlanRequest(BaseModel):
    execution_id:UUID
    width:float
    height:float
    depth:float
    boxes:List[Box]

class GeneratedClpPlan(BaseModel):
    plan:List[Clp]
    left_over_boxes:List[int]
    remarks:str

class DetetionConfig(BaseModel):
    box_model: str = Field(default="best.pt")
    sam_model: str = Field(default="sam2_t.pt")
    confidence_threshold: float = Field(default=0.5)
    iou_threshold: float = Field(default=0.45)
