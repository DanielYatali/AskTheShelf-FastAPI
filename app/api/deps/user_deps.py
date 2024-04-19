from fastapi import Depends, HTTPException, status, Security
from app.models.user_model import User
from app.services.user_service import UserService
from app.schemas.user_schema import Auth0User
from app.core.security import auth


async def get_current_user(auth_result: dict, token: str) -> User:
    email = auth_result["email"]
    user = await UserService.get_user_by_email(email)
    if not user:
        user_profile = await auth.get_user_profile(token)
        new_user = Auth0User(**user_profile)
        user = await UserService.create_user(new_user)
        return user
    return user


# async def is_admin_user(user: User = Depends(get_current_user)):
#     if "admin" not in user.roles:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not admin")
#     return user

