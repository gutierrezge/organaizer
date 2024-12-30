from datetime import datetime
from uuid import UUID
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, computed_field


ExecutionStatus = Literal['PROCESSING', 'DONE', 'ERROR'] 



class Box(BaseModel):
    model_config = ConfigDict(extra='ignore')
    execution_id:UUID
    x1:int
    x2:int
    y1:int
    y2:int
    width:float
    height:float
    depth:float
    created_on:datetime = Field(default=datetime.now())
    modified_on:datetime = Field(default=datetime.now())

    @computed_field
    @property
    def volume(self) -> float:
        return self.width*self.height*self.depth
    
    @computed_field
    @property
    def bbox(self) -> tuple[tuple[int,int], tuple[int, int]]:
        return (self.x1, self.y1), (self.x2, self.y2)


class Execution(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id:UUID
    key:str
    container_width:float
    container_height:float
    container_depth:float
    status:ExecutionStatus = Field(default="PROCESSING")
    status_message:Optional[str] = None
    created_on:datetime = Field(default=datetime.now())
    modified_on:datetime = Field(default=datetime.now())
    boxes:list[Box] = Field(default=[])

    @computed_field
    @property
    def total_boxes(self) -> int:
        return len(self.boxes) if self.boxes is not None else 0
    
    @computed_field
    @property
    def total_volume(self) -> float:
        return sum([b.volume for b in self.boxes]) if self.boxes is not None else 0


class Executions(BaseModel):
    executions:List[Execution]


class PresignedUrlRequest(BaseModel):
    key: str
    expiration: int = Field(
        default=3600,
        description="Expiration time in seconds. Defaults to 1 hour."
    )


class PresignedUrlResponse(BaseModel):
    id:UUID
    key:str
    url: str
    expiration: int