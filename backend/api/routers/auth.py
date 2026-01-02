from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import logging

from services.auth_service import register_user, login_user
from database.connection import get_db
from auth.jwt_handler import create_access_token
from api.schemas.response import APIResponse  # ✅ COMMON RESPONSE WRAPPER

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


# =====================================================
# REQUEST SCHEMAS
# =====================================================
class UserRegister(BaseModel):
    name: str
    age: int
    gender: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# =====================================================
# DOMAIN RESPONSE (DATA ONLY)
# =====================================================
class AuthData(BaseModel):
    user: dict
    access_token: str


# =====================================================
# REGISTER
# =====================================================
@router.post("/register", response_model=APIResponse[AuthData])
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for email: {user_data.email}")

    try:
        user = register_user(
            db,
            name=user_data.name,
            age=user_data.age,
            gender=user_data.gender,
            email=user_data.email,
            password=user_data.password
        )

        access_token = create_access_token(data={"sub": user_data.email})

        return APIResponse(
            success=True,
            message="Registration successful",
            data=AuthData(
                user={
                    "name": user["name"],
                    "email": user["email"],
                    "age": user["age"],
                    "gender": user["gender"]
                },
                access_token=access_token
            )
        )

    except ValueError as e:
        logger.warning(f"Registration failed for {user_data.email}: {str(e)}")

        return APIResponse(
            success=False,
            message="Registration failed",
            error=str(e)
        )


# =====================================================
# LOGIN
# =====================================================
@router.post("/login", response_model=APIResponse[AuthData])
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for email: {credentials.email}")

    try:
        user = login_user(db, credentials.email, credentials.password)
        access_token = create_access_token(data={"sub": credentials.email})

        return APIResponse(
            success=True,
            message="Login successful",
            data=AuthData(
                user=user,
                access_token=access_token
            )
        )

    except ValueError as e:
        logger.warning(f"Login failed for {credentials.email}: {str(e)}")

        return APIResponse(
            success=False,
            message="Login failed",
            error=str(e)
        )
