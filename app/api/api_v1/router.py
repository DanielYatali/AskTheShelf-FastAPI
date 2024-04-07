from fastapi import APIRouter
from app.api.auth.jwt import auth_router
from app.api.api_v1.handlers import user

router = APIRouter()

router.include_router(user.user_router, prefix="/users", tags=["users"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])


