from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from api.schemas.auth import UserRegister, UserLogin, AuthResponse
from services.auth_service import register_user, login_user
from database.connection import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = register_user(
            db=db,
            name=user_data.name,
            age=user_data.age,
            gender=user_data.gender,
            email=user_data.email,
            password=user_data.password
        )
        return AuthResponse(
            success=True,
            message="Registration successful",
            user=user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=AuthResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    try:
        user = login_user(
            db=db,
            email=credentials.email,
            password=credentials.password
        )
        return AuthResponse(
            success=True,
            message="Login successful",
            user=user
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
