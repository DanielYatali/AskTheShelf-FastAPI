from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserAuth(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    username: str = Field(..., description="The username of the user", min_length=5, max_length=20)


class UserNew(BaseModel):
    user_id: str = Field(..., description="The id of the user")
    email: EmailStr = Field(..., description="The email of the user")
    username: str = Field(..., description="The username of the user", min_length=5, max_length=20)
    first_name: Optional[str] = Field(None, description="The first name of the user")
    last_name: Optional[str] = Field(None, description="The last name of the user")
    disabled: Optional[bool] = Field(False, description="The status of the user")


class UserOut(BaseModel):
    user_id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: bool = False
    roles: Optional[list] = None


class Auth0User(BaseModel):
    email: str
    sub: str
    nickname: Optional[str] = Field(None, description="The nickname of the user")
    name: Optional[str] = Field(None, description="The name of the user")
    picture: Optional[str] = Field(None, description="The picture of the user")
    email_verified: Optional[bool] = Field(None, description="The email verification status of the user")
    created_at: Optional[str] = Field(None, description="The creation date of the user")
    family_name: Optional[str] = Field(None, description="The family name of the user")
    given_name: str = Field(None, description="The given name of the user")
