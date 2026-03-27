from random import random

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from db.database import get_db
from db.models import User, RefreshTokens
from db.hashing import Hash
from auth.auth2 import create_access_token, create_refresh_token, get_token_payload
from resources.logger import Logger
from auth.auth2 import get_current_user
from db.database import SessionLocal
from datetime import datetime, timedelta, timezone
from jose import JWTError
from resources.email_client import EmailClient, get_fake_email_client
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
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail = "Invalid Credentials")
    if not user.is_verified:
        logger.error(f"User not verified: {request.username}")
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail = "User not verified. Please verify your email before logging in.")
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(db=db, user_id=user.id)
    return {"access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user.id}

@router.post('/refresh')
def refresh_token(request: dict,db: Session = Depends(get_db)):
    token = request.get("refresh_token")
    try:
        db_token = db.query(RefreshTokens).filter(RefreshTokens.token == token).first()
        if not db_token:
            raise HTTPException(status_code=401, detail="Invalid token")

        if db_token.is_revoked:
            raise HTTPException(status_code=401, detail="Token revoked")

        if db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token expired")
        payload = get_token_payload(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = int(payload.get("sub"))
        db_token.is_revoked = True
        db.commit()
        new_refresh_token = create_refresh_token(user_id, db)
        new_access_token = create_access_token(str(user_id))
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

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

@router.post('/generate-secret-code', description="This endpoint generates a secret code and sends it to the user's email for password reset or email change verification.")
def generate_secret_code(email: str, db: Session = Depends(get_db), email_client: EmailClient = Depends(get_fake_email_client)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    secret_code = f"{random.randint(100000, 999999)}"
    user.verification_code = Hash.bcrypt(secret_code)
    db.commit()
    email_subject = "Your Secret Code"
    email_body = f"Hello {user.username},\n\nYour secret code is: {secret_code}"
    status = email_client.send_email(email_subject, user.email, email_body)
    if status["status"] != "fake-sent":
        logger.error(f"Failed to send secret code email to {email} Reason: {status['reason']}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to send secret code email. {status['reason']}")
    else:
        logger.info(f"Secret code sent to {email}")
        return {"message": "Secret code sent"}

@router.post('/change-email',description="This endpoint allows a user to change their email by providing their password and new email address.")
def change_email(password: str, new_email: str,secret_code: str,db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not Hash.verify(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password")
    if not new_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email is required")
    if secret_code != user.verification_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid secret code")
    user.email = new_email
    db.commit()
    logger.info(f"Email changed successfully for user: {user.username}")
    return {"message": "Email changed successfully"}

@router.post('/change-username',description="This endpoint allows a user to change their username by providing their password and new username.")
def change_username(password: str, new_username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not Hash.verify(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password")
    if not new_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New username is required")
    user.username = new_username
    db.commit()
    logger.info(f"Username changed successfully for user: {user.username}")
    return {"message": "Username changed successfully"}

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
