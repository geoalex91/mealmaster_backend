from fastapi import APIRouter, Depends, HTTPException, status
from routers.schemas import UserDisplay, UserBase
from sqlalchemy.orm.session import Session
from db.database import get_db
from db import db_user
from resources.logger import Logger

router = APIRouter(prefix="/users", tags=["users"])
logger = Logger.get_instance()

@router.post('/create_user', response_model=UserDisplay, summary="Create a new user", 
             description="This endpoint allows the creation of a new user. It checks if a user with the same username or email already exists before creating a new user.",
             response_description="The created user data.")
def create_user(request: UserBase, db: Session = Depends(get_db)):
    """
    Creates a new user in the database.
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
    user = db_user.create_user(db, request)

    return UserDisplay.model_validate(user)