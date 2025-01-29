from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime

# Create base model class
Base = declarative_base()

# Import models
from .user import User
from .conversation import Conversation

# Create database engine
engine = create_engine('sqlite:///bot_data.db')

# Create session factory
Session = sessionmaker(bind=engine)

# Database initialization function
def init_db():
    Base.metadata.create_all(engine)

# Create tables
def create_tables():
    Base.metadata.create_all(engine)

# Export models
__all__ = ['Base', 'User', 'Conversation']