from sqlalchemy.orm import Session
from database.models import User
from utils.password import PasswordHasher

import logging

logger = logging.getLogger(__name__)

def register_user(db: Session, name: str, age: int, gender: str, email: str, password: str) -> dict:
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
        name=name,
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
        "name": new_user.name,
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
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "gender": user.gender
    }
