from fastapi import Depends, HTTPException, status, Security
from app.models.user_model import User
from app.services.user_service import UserService
from app.core.security import auth


async def get_current_user(auth_result: dict) -> User:
    email = auth_result["email"]
    user = await UserService.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def is_admin_user(user: User = Depends(get_current_user)):
    if "admin" not in user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not admin")
    return user
