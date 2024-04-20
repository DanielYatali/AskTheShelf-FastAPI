from datetime import datetime
from beanie import Document, Indexed
from typing import Optional

from pydantic import Field, BaseModel


class Message(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    role: str
    content: str
    products: Optional[list] = []
    related_products: Optional[list] = []


class Conversation(Document):
    user_id: Indexed(str, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: list[Message] = []

    def __repr__(self) -> str:
        return f'<Conversation {self.user_id}>'

    def __str__(self) -> str:
        return self.user_id

    def __hash__(self) -> int:
        return hash(self.user_id)

    class Settings:
        name = "conversations"
