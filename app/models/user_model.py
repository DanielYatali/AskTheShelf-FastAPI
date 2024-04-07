from datetime import datetime
from uuid import UUID, uuid4

import pymongo
from beanie import Document, Indexed
from pydantic import Field, EmailStr
from typing import Optional


class User(Document):
    user_id: UUID = Field(default_factory=uuid4)
    username: Indexed(str, unique=True)
    email: Indexed(str, unique=True)
    hashed_password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: Optional[list] = ['user']
    disabled: Optional[bool] = False

    def __repr__(self) -> str:
        return f'<User {self.email}>'

    def __str__(self) -> str:
        return self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.email == other.email

    @property
    def create(self) -> datetime:
        return self.id.generation_time

    @classmethod
    async def by_email(self, email: str) -> "User":
        return await self.find_one(self.email == email)

    @classmethod
    async def by_username(self, username: str) -> "User":
        return await self.find_one(self.username == username)

    @classmethod
    async def by_id(self, user_id: UUID) -> "User":
        return await self.find_one(self.user_id == user_id)

    class Settings:
        name = "users"
