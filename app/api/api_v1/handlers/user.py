from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from app.models.user_model import User
from app.schemas.user_schema import UserOut, Auth0User
from app.services.user_service import UserService
from app.core.logger import logger
from app.api.deps.user_deps import get_current_user
from app.core.security import auth

user_router = APIRouter(dependencies=[Depends(HTTPBearer())])


@user_router.get("/", summary="Get all users", response_model=List[UserOut] or HTTPException)
async def get_users(request: Request) -> List[UserOut]:
    return await UserService.get_users()


@user_router.get("/by-email/{email}", summary="Get user by email", response_model=UserOut)
async def get_user_by_email(request: Request, email: str):
    try:
        current_user = request.state.user
        user = await UserService.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# @user_router.get("/admin", summary="Get all admin users", response_model=List[UserOut] or HTTPException)
# async def get_admin_users(user: User = Depends(is_admin_user)):
#     return await UserService.get_admin_users()


@user_router.get("/{user_id}", summary="Get user by id", response_model=UserOut or HTTPException)
async def get_user(request: Request,  user_id: str):
    try:
        user = await UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@user_router.post("/", summary="Create user", response_model=UserOut or HTTPException)
async def create_user(auth_result: dict = Depends(auth.verify)):
    try:
        auth0_user = Auth0User(**auth_result)
        return await UserService.create_user(auth0_user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
