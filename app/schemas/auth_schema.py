from pydantic import BaseModel, EmailStr, Field


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str = None
    exp: int = None
    roles: list = None
    username: str = None
    email: EmailStr = None
