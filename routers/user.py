from fastapi import APIRouter, Depends, HTTPException, status
from auth.auth2 import get_current_user
from routers.schemas import User, UserDisplay, UserBase, UserStatsDisplay, UserStatsBase
from sqlalchemy.orm.session import Session
from db.database import get_db
from db import db_user
from db.hashing import Hash
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
    if "@" not in request.email:
        logger.error(f"Invalid email address: {request.email}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid email address")
    existing_user = db.query(db_user.User).filter(
        (db_user.User.username == request.username) | (db_user.User.email == request.email.lower())).first()
    if existing_user:
        logger.error(f"Attempt to create a user that already exists: {request.username} or {request.email}")
        raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="User already exists")
    
    # Generate a random 6-digit verification code
    verification_code = f"{random.randint(100000, 999999)}"
    logger.info(f"Generated verification code for {request.email}: {verification_code}")
    # Send the verification code to the user's email
    email_subject = "Your Verification Code"
    email_body = f"Hello {request.username},\n\nYour verification code is: {verification_code}"
    mail_sent = email_client.send_email(email_subject, request.email.lower(), email_body)
    if mail_sent["status"] != "fake-sent":
        logger.error(f"Failed to send verification email to {request.email} Reaseon {mail_sent['reason']}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to send verification email. {mail_sent['reason']}")
    else:
        user = db_user.create_user(db, request, verification_code)
        return UserDisplay.model_validate(user)
    # # Create the user in the database
    # user = db_user.create_user(db, request, verification_code)

    # return UserDisplay.model_validate(user)
    

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
    if "@" not in email:
        logger.error(f"Invalid email address: {email}")
        raise HTTPException(status_code=422, detail="Invalid email address")
    user = db.query(db_user.User).filter(db_user.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=422, detail="User already verified")

    # Generate new code and expiry
    verification_code = f"{random.randint(100000, 999999)}"
    user.verification_code = Hash.bcrypt(verification_code)
    user.code_expiry = datetime.now(timezone.utc) + timedelta(minutes=1)
    db.commit()
    logger.info(f"Generated new verification code for {email}: {verification_code}")
    # Send email
    email_subject = "Your New Verification Code"
    email_body = f"Hello {user.username},\n\nYour new verification code is: {verification_code}"
    status = email_client.send_email(email_subject, user.email, email_body)
    if status["status"] != "fake-sent":
        logger.error(f"Failed to resend verification email to {email} Reaseon {status['reason']}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to resend verification email. {status['reason']}")
    else:
        logger.info(f"Verification code resent to {email}")
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
    if not user:
        # Create a dummy hash to run the verification against.
        # The hash is for an empty string, which will never match a real code.
        dummy_hash = Hash.bcrypt("")
        Hash.verify(code, dummy_hash) # This call is for timing consistency.
        raise HTTPException(status_code=422, detail="Invalid or expired 1-time code")

    # Check if the code is valid and not expired
    is_code_valid = Hash.verify(code, user.verification_code)
    is_code_expired = user.code_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)

    if not is_code_valid or is_code_expired:
        raise HTTPException(status_code=422, detail="Invalid or expired code")

    user.is_verified = True
    user.verification_code = None
    user.code_expiry = None
    initial_stats = db_user.UserStatsBase(name=user.username,
                                            height=0,
                                            weight=0.0,
                                            birthdate="2001-01-01",
                                            gender="unknown",
                                            activity_level="sedentary")
    db.commit()
    db_user.update_user_stats(db, user, initial_stats)
    logger.info(f"User {user.username} verified successfully")
    return {"message": "User verified successfully"}

@router.post('/check-user', summary="scheck user",description="Verify a user exists and sends a email with a secret code to reset password",
             response_description="A message indicating that email was send successfully.")
def forgot_password_email(email: str, db: Session = Depends(get_db),email_client: EmailClient = Depends(get_fake_email_client)):
    """Checks if a user exists by email and sends a password reset verification code.
    Args:
        email (str): The user's email address.
        db (Session): The database session dependency.
        email_client (EmailClient): The email client dependency.
    Returns:
        dict: A message indicating that the secret code was sent.
    Raises:
        HTTPException: If the email format is invalid or email sending fails."""

    if "@" not in email:
        logger.error(f"Invalid email address: {email}")
        raise HTTPException(status_code=422, detail="Invalid email address")
    user = db.query(db_user.User).filter(db_user.User.email == email).first()
    if not user:
        return {"message": "A secret code was sent to your email"}

    # Generate new code and expiry
    verification_code = f"{random.randint(100000, 999999)}"
    user.verification_code = Hash.bcrypt(verification_code)
    user.code_expiry = datetime.now(timezone.utc) + timedelta(minutes=1)
    db.commit()
    logger.info(f"Generated new verification code for {email}: {verification_code}")
    # Send email
    email_subject = "Your New Verification Code"
    email_body = f"Hello {user.username},\n\nYour new verification code is: {verification_code}"
    status = email_client.send_email(email_subject, user.email, email_body)
    if status["status"] != "fake-sent":
        logger.error(f"Failed to resend verification email to {email} Reaseon {status['reason']}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to send the secret code email. {status['reason']}")
    else:
        logger.info(f"Verification code resent to {email}")
        return {"message": "A secret code was sent to your email"}
    
@router.post('/reset_password', summary="Reset Password",description="Reset a user's password using the verification code sent to their email.",
             response_description="A message indicating that the password was reset successfully.")
def reset_password(email: str, code: str, password: str, db: Session = Depends(get_db)):
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
    if not user:
        # Create a dummy hash to run the verification against.
        # The hash is for an empty string, which will never match a real code.
        dummy_hash = Hash.bcrypt("")
        Hash.verify(code, dummy_hash) # This call is for timing consistency.
        raise HTTPException(status_code=422, detail="Invalid or expired 1-time code")

    # Check if the code is valid and not expired
    is_code_valid = Hash.verify(code, user.verification_code)
    is_code_expired = user.code_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)

    if not is_code_valid or is_code_expired:
        raise HTTPException(status_code=422, detail="Invalid or expired code")

    user.hashed_password = Hash.bcrypt(password)
    user.verification_code = None
    user.code_expiry = None
    db.commit()
    return {"message": "password reset successfully"}

@router.get('/stats/', response_model=UserStatsDisplay, summary="Get user stats",
             description="This endpoint retrieves the stats of a user by their username.",
             response_description="The stats of the user.")
def get_user_stats(db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    user_stats = db_user.get_user_stats_by_username(db, current_user.username)
    return UserStatsDisplay.model_validate(user_stats)

@router.put('/stats/', response_model=UserStatsDisplay, summary="Update user stats",
             description="This endpoint updates the stats of a user by their username.",
             response_description="The updated stats of the user.")
def update_user_stats(stats: UserStatsBase, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    user_stats = db_user.update_user_stats(db, current_user, stats)
    return UserStatsDisplay.model_validate(user_stats)