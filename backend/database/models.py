from sqlalchemy import Column, String, Integer
from database.connection import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'auth'}
    
    email = Column(String(150), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    password_hash = Column(String, nullable=False)
