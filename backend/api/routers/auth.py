from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from services.auth_service import register_user, login_user  # ✅ CHANGED: authservice → auth_service
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
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=AuthResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT"""
    try:
        user = login_user(db, credentials.email, credentials.password)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": credentials.email})
        
        return AuthResponse(
            success=True,
            message="Login successful",
            user=user,
            access_token=access_token
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
