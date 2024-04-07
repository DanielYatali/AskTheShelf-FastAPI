from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserAuth(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    username: str = Field(..., description="The username of the user", min_length=5, max_length=20)
    password: str = Field(..., description="The password of the user", min_length=5, max_length=20)


class UserOut(BaseModel):
    user_id: UUID
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: bool = False
    roles: Optional[list] = None


