from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, field_validator
from typing import Optional, Dict
from pydantic import Field


class Job(BaseModel):
    id: Optional[str] = Field(None, alias='_id')
    status: str = "Pending"
    start_time: datetime = Field(default_factory=datetime.now)
    url: str
    end_time: Optional[datetime] = None
    result: Optional[Dict] = Field(default_factory=dict)
    error: Optional[Dict] = Field(default_factory=dict)

    @field_validator("id")
    def set_id(cls, v):
        if v:
            return str(v)
        return str(ObjectId())

    class Config:
        arbitrary_types_allowed = True
        # This config allows the model's attributes to be accessed using both the attribute name and its alias.
        populate_by_name = True
        # Assuming you want to serialize/deserialize datetime to ISO format strings
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_decoders = {
            datetime: lambda v: datetime.fromisoformat(v),
        }
