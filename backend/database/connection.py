from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Validate that DATABASE_URL exists
if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment variables")
    raise ValueError(
        "DATABASE_URL not found in environment variables. "
        "Please check your .env file."
    )

logger.info("Database URL configured successfully")

print(f" Using DATABASE_URL: {DATABASE_URL}")

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting DB session"""
    logger.debug("Creating database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        logger.debug("Closing database session")
        db.close()
