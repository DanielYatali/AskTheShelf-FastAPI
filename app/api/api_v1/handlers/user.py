from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from app.api.deps.user_deps import is_admin_user
from app.models.user_model import User
from app.schemas.user_schema import UserAuth, UserOut
from app.services.user_service import UserService
from app.core.logger import logger

user_router = APIRouter()


@user_router.get("/", summary="Get all users", response_model=List[UserOut] or HTTPException)
async def get_users():
    return await UserService.get_users()


@user_router.get("/by-email/{email}", summary="Get user by email", response_model=UserOut)
async def get_user_by_email(email: str):
    try:
        user = await UserService.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@user_router.get("/admin", summary="Get all admin users", response_model=List[UserOut] or HTTPException)
async def get_admin_users(user: User = Depends(is_admin_user)):
    return await UserService.get_admin_users()


@user_router.get("/{user_id}", summary="Get user by id", response_model=UserOut or HTTPException)
async def get_user(user_id: str):
    try:
        user = await UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@user_router.post("/", summary="Create user", response_model=UserOut or HTTPException)
async def create_user(data: UserAuth) -> UserOut or HTTPException:
    try:
        user = await UserService.create_user(data)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
