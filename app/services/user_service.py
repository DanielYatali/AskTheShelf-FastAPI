from typing import Optional
from uuid import UUID

from app.models.user_model import User
from app.schemas.user_schema import UserAuth, UserOut
from app.core.security import hash_password, check_password


class UserService:
    @staticmethod
    async def create_user(data: UserAuth):
        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        await user.save()
        return user

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        user = await User.by_email(email)
        if not user:
            return None
        valid = check_password(stored_hash_base64=user.hashed_password, password_to_check=password)
        if not valid:
            return None
        return user

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        uuid_user_id = UUID(user_id)
        user = await User.find_one(User.user_id == uuid_user_id)
        if not user:
            return None
        return user

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        user = await User.by_email(email)
        if not user:
            return None
        return user

    @staticmethod
    async def get_users():
        users = await User.all().to_list()
        return users

    @staticmethod
    async def get_admin_users():
        users = await User.find(User.roles == 'admin').to_list()
        return users
