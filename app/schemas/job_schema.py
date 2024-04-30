from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobIn(BaseModel):
    job_id: str = Field(..., description="The id of the job")
    user_id: str = Field(..., description="The id of the user")
    status: str = Field(..., description="The status of the job")
    start_time: datetime = Field(..., description="The start time of the job")
    query: Optional[str] = Field(None, description="The query of the job")


class JobRequest(BaseModel):
    url: str


class JobUpdate(BaseModel):
    job_id: str
    status: str
    url: Optional[str] = ""
    user_id: str
    user_query: Optional[str] = ""
    scraper_id: Optional[str] = ""
    end_time: Optional[datetime] = Field(None, description="The end time of the job")
    result: Optional[list] = Field([], description="The result of the job")
    error: Optional[dict] = Field(None, description="The error of the job")
    action: Optional[str] = Field(None, description="The action of the job generated by the llm model")
    query: Optional[str] = Field(None, description="The query generated by the llm model")


class JobOut(BaseModel):
    job_id: str
    user_id: str
    status: str
    user_query: Optional[str] = ""
    query: Optional[str] = ""
    action: Optional[str] = ""
    start_time: datetime
    url: Optional[str] = ""
    end_time: Optional[datetime] = Field(None, description="The end time of the job")
    result: Optional[list] = Field([], description="The result of the job")
    error: Optional[dict] = Field(None, description="The error of the job")
