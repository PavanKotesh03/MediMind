from sqlalchemy.orm import Session
from database.models import User
from utils.password import PasswordHasher

def register_user(db: Session, name: str, age: int, gender: str, 
                  email: str, password: str) -> dict:
    """Register a new user"""
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
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
    
    return {
        "name": new_user.name,
        "email": new_user.email,
        "age": new_user.age,
        "gender": new_user.gender
    }

def login_user(db: Session, email: str, password: str) -> dict:
    """Validate login credentials"""
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("Invalid email or password")
    
    # Verify password
    if not PasswordHasher.verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    
    return {
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "gender": user.gender
    }
