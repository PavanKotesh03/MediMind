from sqlalchemy.orm import Session
from database.models import User
from utils.password import PasswordHasher

import logging

logger = logging.getLogger(__name__)

def register_user(db: Session, first_name: str, last_name: str, age: int, gender: str, email: str, password: str) -> dict:
    """Register a new user"""
    logger.debug(f"Attempting to register user: {email}")
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        logger.warning(f"Registration failed: Email {email} already exists")
        raise ValueError("Email already registered")
    
    # Hash password
    password_hash = PasswordHasher.hash_password(password)
    
    # Create user
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        age=age,
        gender=gender,
        email=email,
        password_hash=password_hash
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User {email} registered successfully")
    return {
        "name": f"{new_user.first_name} {new_user.last_name}",
        "email": new_user.email,
        "age": new_user.age,
        "gender": new_user.gender
    }

def login_user(db: Session, email: str, password: str) -> dict:
    """Validate login credentials"""
    logger.debug(f"Login attempt for user: {email}")
    # Find user
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        logger.warning(f"Login failed: User {email} not found")
        raise ValueError("Invalid email or password")
    
    # Verify password
    if not PasswordHasher.verify_password(password, user.password_hash):
        logger.warning(f"Login failed: Invalid password for {email}")
        raise ValueError("Invalid email or password")
    
    logger.info(f"User {email} logged in successfully")
    return {
        "name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "age": user.age,
        "gender": user.gender
    }

def register_oauth_user(db: Session, email: str, name: str) -> dict:
    """Register or Get existing user from OAuth"""
    logger.debug(f"Processing OAuth login for: {email}")
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    
    if existing_user:
        logger.info(f"OAuth: User {email} already exists, logging in")
        return {
            "name": f"{existing_user.first_name} {existing_user.last_name}",
            "email": existing_user.email,
            "age": existing_user.age,
            "gender": existing_user.gender
        }
    
    # Create new user with dummy values for missing fields
    logger.info(f"OAuth: Registering new user {email}")
    
    # Simple split for name
    parts = name.split()
    first_name = parts[0] if parts else "User"
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        age=0,  # Default for OAuth
        gender="Other",  # Default for OAuth
        password_hash="oauth_user_no_password" # Unusable password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "name": f"{new_user.first_name} {new_user.last_name}",
        "email": new_user.email,
        "age": new_user.age,
        "gender": new_user.gender
    }
