from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import logging

from services.auth_service import register_user, login_user
from database.connection import get_db
from auth.jwt_handler import create_access_token
from api.schemas.response import APIResponse  # ✅ COMMON RESPONSE WRAPPER

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================================================
# REQUEST SCHEMAS
# =====================================================
class UserRegister(BaseModel):
    first_name: str
    last_name: str
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
            first_name=user_data.first_name,
            last_name=user_data.last_name,
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
# =====================================================
# OAUTH SETUP
# =====================================================
from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from starlette.responses import RedirectResponse
import os
from services.auth_service import register_user, login_user, register_oauth_user

oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


# =====================================================
# GOOGLE LOGIN
# =====================================================
# =====================================================
# GOOGLE LOGIN
# =====================================================
@router.get("/google/login")
async def login_google(request: Request):
    """Refirects user to Google Login"""
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        logger.error("Missing Google Client ID or Secret in environment variables")
        return APIResponse(
            success=False,
            message="Server configuration error: Google Auth not configured",
            error="Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET"
        )
    
    # Force localhost to match typical Google Console config
    # This prevents 127.0.0.1 vs localhost mismatches
    redirect_uri = "http://localhost:8000/api/auth/google/callback"
    logger.info(f"Initiating Google Login with redirect_uri: {redirect_uri}")
    
    return await oauth.google.authorize_redirect(request, redirect_uri)


# =====================================================
# GOOGLE CALLBACK
# =====================================================
@router.get("/google/callback", name='auth_google_callback')
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle callback from Google"""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            # Fallback if userinfo not in token (depends on scope/provider)
            # manually fetch userinfo
            user_info = await oauth.google.userinfo(token=token)

        email = user_info.get('email')
        name = user_info.get('name')
        
        if not email:
            raise ValueError("Email not found in OAuth provider")

        # Create or Get User
        user = register_oauth_user(db, email, name)
        
        # Generate JWT
        access_token = create_access_token(data={"sub": email})
        
        # Redirect to Frontend with Token
        frontend_url = "http://localhost:4200/login-success"
        return RedirectResponse(url=f"{frontend_url}?token={access_token}")
        
    except Exception as e:
        logger.error(f"OAuth Callback Error: {str(e)}")
        # Redirect to login with error
        return RedirectResponse(url="http://localhost:4200/login?error=oauth_failed")
