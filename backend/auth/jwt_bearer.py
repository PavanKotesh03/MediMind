from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_handler import verify_token

import logging

logger = logging.getLogger(__name__)

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        logger.debug("Initializing JWTBearer")
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        logger.debug("JWTBearer called for request authentication")
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                logger.warning("Invalid authentication scheme")
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            email = self.verify_jwt(credentials.credentials)
            logger.info(f"Authenticated user: {email}")
            return email
        else:
            logger.warning("Invalid authorization code")
            raise HTTPException(status_code=403, detail="Invalid authorization code")

    def verify_jwt(self, jwtoken: str) -> str:
        try:
            email = verify_token(jwtoken)
            return email
        except Exception as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
