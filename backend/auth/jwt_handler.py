from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv

import logging

logger = logging.getLogger(__name__)

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-minimum-32-characters-long-for-security")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # ✅ CHANGED: 30 → 480 (8 hours)

def create_access_token(data: dict):
    """Create JWT token"""
    logger.debug(f"Creating access token for: {data.get('sub', 'unknown')}")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info("Access token created successfully")
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token and return payload"""
    logger.debug("Verifying JWT token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token missing email in payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing email",
                headers={"WWW-Authenticate": "Bearer"}
            )
        logger.info(f"Token verified for user: {email}")
        return email
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired - please login again",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
