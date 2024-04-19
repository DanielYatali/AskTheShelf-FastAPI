from typing import Optional

from app.models.user_model import User
from app.schemas.user_schema import Auth0User


class UserService:
    @staticmethod
    async def create_user(auth0_user: Auth0User) -> Optional[User]:
        username = auth0_user.nickname
        if not username:
            username = auth0_user.email.split('@')[0]
        user = User(
            username=username,
            email=auth0_user.email,
            user_id=auth0_user.sub,
            first_name=auth0_user.given_name,
            last_name=auth0_user.family_name,
            picture=auth0_user.picture,
        )
        await user.save()
        return user

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        user = await User.find_one(User.user_id == user_id)
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
