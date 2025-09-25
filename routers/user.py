from fastapi import APIRouter, Depends, HTTPException, status
from routers.schemas import UserDisplay, UserBase
from sqlalchemy.orm.session import Session
from db.database import get_db
from db import db_user
from datetime import datetime, timedelta, timezone
from resources.logger import Logger
import random
from resources.email_client import EmailClient, get_email_client, get_fake_email_client

router = APIRouter(prefix="/users", tags=["users"])
logger = Logger()

@router.post('/register', response_model=UserDisplay, summary="Create a new user", 
             description="This endpoint allows the creation of a new user. It checks if a user with the same username or email already exists before creating a new user.",
             response_description="The created user data.")
def create_user(request: UserBase, db: Session = Depends(get_db),email_client: EmailClient = Depends(get_fake_email_client)):
    """
    Creates a new user in the database and sends a verification code to the user's email.
    Args:
        request (UserBase): The user data containing username and email.
        db (Session): The database session dependency.
    Returns:
        UserDisplay: The created user data.
    Raises:
        HTTPException: If a user with the same username or email already exists.
    """
    existing_user = db.query(db_user.User).filter(
        (db_user.User.username == request.username) | (db_user.User.email == request.email)).first()
    if existing_user:
        logger.error(f"Attempt to create a user that already exists: {request.username} or {request.email}")
        raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="User already exists")
    
    # Generate a random 6-digit verification code
    verification_code = f"{random.randint(100000, 999999)}"
    
    # Send the verification code to the user's email
    email_subject = "Your Verification Code"
    email_body = f"Hello {request.username},\n\nYour verification code is: {verification_code}"
    try:
        email_client.send_email(email_subject, request.email, email_body)
    except Exception as e:
        logger.error(f"Failed to send verification email to {request.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email")
    
    # Create the user in the database
    user = db_user.create_user(db, request, verification_code)

    return UserDisplay.model_validate(user)

@router.post('/resend-verification', 
             summary="Resend verification code", 
             description="This endpoint allows resending a new verification code to the user's email if the user is not already verified.",
             response_description="A message indicating that the verification code has been resent.")
def resend_verification(email: str, db: Session = Depends(get_db), email_client: EmailClient = Depends(get_fake_email_client)):
    """
    Resends a new verification code to the user's email if the user is not already verified.
    Args:
        request (ResendVerificationRequest): The user data containing email.
        db (Session): The database session dependency.
        Returns:
        dict: A message indicating that the verification code has been resent.
    Raises:
        HTTPException: If the user is not found or already verified.
    """
    user = db.query(db_user.User).filter(db_user.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")

    # Generate new code and expiry
    verification_code = f"{random.randint(100000, 999999)}"
    user.verification_code = verification_code
    user.code_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    # Send email
    email_subject = "Your New Verification Code"
    email_body = f"Hello {user.username},\n\nYour new verification code is: {verification_code}"
    email_client.send_email(email_subject, user.email, email_body)
    return {"message": "Verification code resent"}

@router.post('/verify', summary="Verify user",description="Verify a user using the verification code sent to their email.",
             response_description="A message indicating that the user has been verified successfully.")
def verify_user(email: str, code: str, db: Session = Depends(get_db)):
    """Verifies a user using the verification code sent to their email.
    Args:
        email (str): The user's email address.
        code (str): The verification code sent to the user's email.
        db (Session): The database session dependency.
    Returns:
        dict: A message indicating that the user has been verified successfully.
    Raises:
        HTTPException: If the user is not found, the code is invalid, or the code has expired."""
    user = db.query(db_user.User).filter(db_user.User.email == email).first()
    if not user or user.verification_code != code or user.code_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    user.is_verified = True
    user.verification_code = None
    user.code_expiry = None
    db.commit()
    return {"message": "User verified successfully"}