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

router = APIRouter(tags=["authentication"])
logger = Logger()

@router.post('/token', description = "This endpoint generates an access token for a user based on their username and password.")
def get_token(request: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
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