from typing import Any
from fastapi import APIRouter, HTTPException, Depends, Body, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from app.api.deps.user_deps import get_current_user
from app.core.config import settings
from app.models.user_model import User
from app.schemas.auth_schema import TokenSchema, TokenPayload
from app.schemas.user_schema import UserOut
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token
from jose import jwt
auth_router = APIRouter()


@auth_router.post("/login", summary="Create access and refresh tokens", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    try:
        user = await UserService.authenticate_user(email=form_data.username, password=form_data.password)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        return {
            "access_token": create_access_token(user),
            "refresh_token": create_refresh_token(user),
        }
    except Exception as e:
        return HTTPException(status_code=400, detail="Invalid credentials")


@auth_router.post("/test-token", summary="Test access token", response_model=UserOut)
async def test_token(user: User = Depends(get_current_user)) -> Any:
    return user


@auth_router.post("/refresh", summary="Refresh access token", response_model=TokenSchema)
async def generate_refresh_token(refresh_token: str = Body(...)):
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except(jwt.JWTError, jwt.ExpiredSignatureError, ValidationError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    user = await UserService.get_user_by_id(user_id=token_data.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
    }



