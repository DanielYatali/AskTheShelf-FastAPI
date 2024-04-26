from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobIn(BaseModel):
    job_id: str = Field(..., description="The id of the job")
    user_id: str = Field(..., description="The id of the user")
    status: str = Field(..., description="The status of the job")
    start_time: datetime = Field(..., description="The start time of the job")


class JobRequest(BaseModel):
    url: str


class JobUpdate(BaseModel):
    job_id: str
    status: str
    url: Optional[str] = ""
    end_time: Optional[datetime] = Field(None, description="The end time of the job")
    result: Optional[dict] = Field(None, description="The result of the job")
    error: Optional[dict] = Field(None, description="The error of the job")


class JobSchema(BaseModel):
    job_id: str
    user_id: Optional[str] = ""
    status: str
    start_time: datetime
    product_id: Optional[str] = ""
    url: str
    end_time: Optional[datetime] = Field(None, description="The end time of the job")
    result: Optional[dict] = Field(None, description="The result of the job")
    error: Optional[dict] = Field(None, description="The error of the job")


class JobOut(BaseModel):
    job_id: str
    product_id: str
    user_id: str
    status: str
    start_time: datetime
    url: str
    end_time: Optional[datetime] = Field(None, description="The end time of the job")
    result: Optional[dict] = Field(None, description="The result of the job")
    error: Optional[dict] = Field(None, description="The error of the job")
