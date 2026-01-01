from passlib.context import CryptContext

import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordHasher:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain password"""
        logger.debug("Hashing password")
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        logger.debug("Verifying password")
        result = pwd_context.verify(plain_password, hashed_password)
        if not result:
            logger.warning("Password verification failed")
        return result
#bycript hashing