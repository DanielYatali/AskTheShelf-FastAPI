from datetime import datetime
from beanie import Document, Indexed
from typing import Optional

from pydantic import Field


class Job(Document):
    job_id: Indexed(str, unique=True)
    status: str = "Pending"
    query: Optional[str] = ""
    user_query: Optional[str] = ""
    start_time: datetime = Field(default_factory=datetime.now)
    action: Optional[str] = ""
    user_id: Indexed(str)
    scraper_id: Optional[str] = ""
    url: str
    end_time: Optional[datetime] = None
    result: Optional[list] = []
    error: Optional[dict] = {}

    def __repr__(self) -> str:
        return f'<Job {self.job_id}>'

    def __str__(self) -> str:
        return self.job_id

    def __hash__(self) -> int:
        return hash(self.job_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return False
        return self.job_id == other.job_id

    @property
    def create(self) -> datetime:
        return self.id.generation_time

    @classmethod
    async def by_id(self, job_id: str) -> "Job":
        return await self.find_one(self.job_id == job_id)

    class Settings:
        name = "jobs"

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
