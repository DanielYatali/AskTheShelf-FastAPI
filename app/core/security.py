from typing import Union, Any, Optional

import aiohttp
from fastapi import HTTPException, status, Depends
from fastapi.security import SecurityScopes, HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
import jwt


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        """Returns HTTP 403"""
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Requires authentication"
        )


# 👇 new code
class VerifyToken:
    """Does all the token verification using PyJWT"""

    def __init__(self):
        self.config = settings

        # This gets the JWKS from a given URL and does processing so you can
        # use any of the keys available
        jwks_url = f'https://{self.config.AUTH0_DOMAIN}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def get_user_profile(self, token):
        url = f"https://{self.config.AUTH0_DOMAIN}/userinfo"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise UnauthorizedException("Failed to get user profile")
        except Exception as e:
            raise UnauthorizedException(str(e))

    async def verify_token(self, token: str) -> Union[dict, Any]:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))

        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.config.AUTH0_ALGORITHMS,
                audience=self.config.AUTH0_AUDIENCE,
                issuer=self.config.AUTH0_ISSUER,
            )
        except Exception as error:
            raise UnauthorizedException(str(error))

        return payload

    async def verify(self,
                     security_scopes: SecurityScopes,
                     token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())
                     ):
        if token is None:
            raise UnauthenticatedException

        # This gets the 'kid' from the passed token
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(
                token.credentials
            ).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))

        try:
            payload = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=self.config.AUTH0_ALGORITHMS,
                audience=self.config.AUTH0_AUDIENCE,
                issuer=self.config.AUTH0_ISSUER,
            )
        except Exception as error:
            raise UnauthorizedException(str(error))

        return payload


auth = VerifyToken()
