from routers.schemas import UserBase, UserStatsBase
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from db.models import User
from resources.logger import Logger
from datetime import datetime, timedelta, timezone
from db.hashing import Hash

logger = Logger()

def create_user(db: Session, request: UserBase, verification_code: str): 
    password = Hash.bcrypt(request.password)
    hashed_code = Hash.bcrypt(verification_code)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=1)
    new_user = User(username=request.username, email=request.email.lower(), hashed_password=password,
                    verification_code=hashed_code, code_expiry=expiry, is_verified=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User created: {new_user.username}")
    return new_user

def get_user_by_username(db: Session, username: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = f"User with username {username} not found")
    return user

def get_user_stats_by_username(db: Session, username: str):
    user = get_user_by_username(db, username)
    if not user.user_stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = f"Stats for user {username} not found")
    return user.user_stats

def update_user_stats(db: Session, user: User, stats: UserStatsBase):
    user_stats = get_user_stats_by_username(db, user.username)
    if stats.name is not None:
        user_stats.name = stats.name
    if stats.height is not None:
        user_stats.height = stats.height
    if stats.weight is not None:
        user_stats.weight = stats.weight
    if stats.birthdate is not None:
        user_stats.birthdate = datetime.strptime(stats.birthdate, "%Y-%m-%d")
    if stats.gender is not None:
        user_stats.gender = stats.gender
    if stats.activity_level is not None:
        user_stats.activity_level = stats.activity_level
    db.commit()
    db.refresh(user_stats)
    return user_stats

