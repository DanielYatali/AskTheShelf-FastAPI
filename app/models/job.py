from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional, List, Dict


class Job(SQLModel, table=True):
    id: str = Field(primary_key=True)
    status: str = Field(default="pending")  # pending, running, completed, error
    url: str
    start_time: datetime
    end_time: Optional[datetime]
    #need to figure out how to store the result
    result: Optional[Dict]
    error: Optional[str]
