from sqlalchemy import Column, String, Integer
from database.connection import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'auth'}
    
    email = Column(String(150), primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True) # Changed to nullable per potential OAuth flow or keeping consistent
    gender = Column(String(10), nullable=True)
    password_hash = Column(String, nullable=False)

