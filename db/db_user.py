from routers.schemas import UserBase
from sqlalchemy.orm import Session
from db.models import User
from resources.logger import Logger
from datetime import datetime, timedelta, timezone

logger = Logger.get_instance()

def create_user(db: Session, request: UserBase, verification_code: str): 
    fake_hashed_password = request.password + "notreallyhashed"
    fake_hashed_code = verification_code + "notreallyhashed"
    expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    new_user = User(username=request.username, email=request.email, hashed_password=fake_hashed_password,
                    verification_code=fake_hashed_code, code_expiry=expiry, is_verified=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User created: {new_user.username} with email: {new_user.email}")
    return new_user