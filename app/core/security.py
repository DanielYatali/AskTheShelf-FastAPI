import base64
from datetime import datetime, timedelta
from typing import Union, Any
from app.core.config import settings
from jose import jwt

import bcrypt

from app.models.user_model import User


def hash_password(password):
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    hashed_password_base64 = base64.b64encode(hashed_password).decode('utf-8')
    return hashed_password_base64


def check_password(stored_hash_base64, password_to_check):
    stored_hash_bytes = base64.b64decode(stored_hash_base64)
    password_bytes = password_to_check.encode('utf-8')
    return bcrypt.checkpw(password_bytes, stored_hash_bytes)


def create_access_token(user: User, expires_delta: int = None):
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expires_delta, "sub": str(user.user_id), "roles": user.roles, "username": user.username,
                 "email": user.email}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(user: User, expires_delta: int = None):
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expires_delta, "sub": str(user.user_id), "roles": user.roles, "username": user.username,
                 "email": user.email}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
