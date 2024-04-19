from datetime import datetime
from beanie import Document, Indexed
from typing import Optional

from pydantic import Field, BaseModel


class Message(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    role: str
    content: str
    products: Optional[list] = []


class Conversation(Document):
    user_id: Indexed(str, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: list[Message] = []

