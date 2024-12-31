from datetime import datetime
from pydantic import BaseModel, Field


HTTP_STATUS_OK = 200
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_NOT_FOUND = 404


class HealthStatus(BaseModel):
    current_datetime:str = Field(default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))