from .database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    verification_code = Column(String, nullable=True)
    code_expiry = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)