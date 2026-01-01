from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

import logging

from services.auth_service import register_user, login_user  # ✅ CHANGED: authservice → auth_service
from database.connection import get_db
from auth.jwt_handler import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])
from database.connection import get_db
from auth.jwt_handler import create_access_token

router = APIRouter(tags=["Authentication"])

# Schemas
class UserRegister(BaseModel):
    name: str
    age: int
    gender: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: dict | None = None
    access_token: str | None = None

@router.post("/register", response_model=AuthResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
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
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user_data.email})
        
        logger.info(f"User {user_data.email} registered successfully")
        return AuthResponse(
            success=True,
            message="Registration successful",
            user={
                "name": user["name"],
                "email": user["email"],
                "age": user["age"],
                "gender": user["gender"]
            },
            access_token=access_token
        )
    except ValueError as e:
        logger.warning(f"Registration failed for {user_data.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=AuthResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT"""
    logger.info(f"Login attempt for email: {credentials.email}")
    try:
        user = login_user(db, credentials.email, credentials.password)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": credentials.email})
        
        logger.info(f"User {credentials.email} logged in successfully")
        return AuthResponse(
            success=True,
            message="Login successful",
            user=user,
            access_token=access_token
        )
    except ValueError as e:
        logger.warning(f"Login failed for {credentials.email}: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
