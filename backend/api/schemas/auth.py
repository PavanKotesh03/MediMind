from pydantic import BaseModel
from typing import Optional

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    age: int
    gender: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    access_token: Optional[str] = None  # Add this field
