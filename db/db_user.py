from routers.schemas import UserBase
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from db.models import User
from resources.logger import Logger
from datetime import datetime, timedelta, timezone
from db.hashing import Hash

logger = Logger()

def create_user(db: Session, request: UserBase, verification_code: str): 
    password = Hash.bcrypt(request.password)
    #hashed_code = Hash.bcrypt(verification_code)
    #hashed_email = Hash.bcrypt(request.email)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=1)
    new_user = User(username=request.username, email=request.email, hashed_password=password,
                    verification_code=verification_code, code_expiry=expiry, is_verified=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User created: {new_user.username} with email: {new_user.email}")
    return new_user

def get_user_by_username(db: Session, username: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = f"User with username {username} not found")
    return user