from fastapi import FastAPI, Request, HTTPException, Security, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.api.deps.user_deps import get_current_user
from app.core.security import auth
from app.core.logger import logger


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allow_routes=None):
        super().__init__(app)
        self.allow_routes = allow_routes or []

    async def dispatch(self, request: Request, call_next):
        if request.url.path not in self.allow_routes:
            authorization: str = request.headers.get("Authorization")
            if not authorization:
                return JSONResponse(content={"detail": "Authorization header is missing"}, status_code=401)
            try:
                token_parts = authorization.split("Bearer ")
                if len(token_parts) != 2:
                    # Return a 401 response directly for malformed Authorization header
                    return JSONResponse(
                        content={"detail": "Authorization header must be in the 'Bearer <token>' format"},
                        status_code=401)
                token = token_parts[1]
                auth_result = await auth.verify_token(token)
                user = await get_current_user(auth_result)
                request.state.user = user

            except Exception as e:
                logger.error(e)
                return JSONResponse(content={"detail": "Invalid token"}, status_code=401)

        response = await call_next(request)
        return response
