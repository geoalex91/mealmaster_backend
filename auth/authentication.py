from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from db.database import get_db
from db.models import User
from db.hashing import Hash
from auth.auth2 import create_access_token
from resources.logger import Logger
from auth.auth2 import get_current_user
from db.database import SessionLocal
from datetime import datetime, timedelta, timezone
from resources.background_task_queue import BackgroundTaskQueue
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
# --- Start of Changes ---

# Configuration for the unverified user cleanup task
UNVERIFIED_CLEAN_INTERVAL_HOURS = 5 * 3600

# --- End of Changes ---

router = APIRouter(tags=["authentication"])
logger = Logger()

@router.post('/token', description = "This endpoint generates an access token for a user based on their username and password.")
def get_token(request: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
    """
    Authenticates a user and generates an access token.
    This function verifies the user's credentials (username or email and password),
    checks if the user is verified, and returns an access token along with user details.
    Args:
        request (OAuth2PasswordRequestForm): The OAuth2 request form containing username and password.
        db (Session): The database session dependency.
    Returns:
        dict: A dictionary containing the access token, token type, user ID, and username.
    Raises:
        HTTPException: If credentials are invalid, password is incorrect, or user is not verified.
    """
    
    user = db.query(User).filter(User.username == request.username).first()
    email = db.query(User).filter(User.email == request.username.lower()).first()
    if not user and not email:
        logger.error(f"Invalid Credentials: {request.username}")
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail = "Invalid Credentials")
    if email:
        user = email
    if not Hash.verify(request.password,user.hashed_password):
            logger.error(f"Incorrect password for user: {request.username}")
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail = "Incorrect password")
    if not user.is_verified:
        logger.error(f"User not verified: {request.username}")
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "User not verified. Please verify your email before logging in.")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,}

@router.post('/change-password',description="This endpoint allows a user to change their password by providing their old and new passwords.")
def change_password(old_pasword: str, new_password: str, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not Hash.verify(old_pasword, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
    user.hashed_password = Hash.bcrypt(new_password)
    db.commit()
    logger.info(f"Password changed successfully for user: {user.username}")
    return {"message": "Password changed successfully"}

@router.delete('/delete-account',description="This endpoint allows a user to delete their account by providing their password for verification.")
def delete_account(password:str, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not Hash.verify(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is incorrect")
    db.delete(user)
    db.commit()
    logger.info(f"{user.username} Account deleted successfully for user: {user.username}")
    return {"message": "Account deleted successfully"}

def delete_unverified_users():
    """
    Deletes unverified users from the database whose verification code has expired.
    This function queries the database for users who have not been verified and whose
    verification code expiry time is older than 10 minutes from the current UTC time.
    It deletes each matching user and commits the changes to the database.
    Logging:
        Logs the email of each deleted user.
    Raises:
        Any exceptions raised by the database session or commit will propagate.
    Note:
        The database session is closed after the operation.
    """
    db: Session = SessionLocal()
    expiry_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    users = db.query(User).filter(User.is_verified == False,User.code_expiry < expiry_time).all()
    if not users:
        logger.info("No unverified users to delete.")
        db.close()
        return
    for user in users:
        logger.info(f"Deleting unverified user: {user.email}")
        db.delete(user)
    db.commit()
    db.close()
