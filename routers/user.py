from fastapi import APIRouter, Depends
from routers.schemas import UserDisplay, UserBase
from sqlalchemy.orm.session import Session
from db.database import get_db
from db import db_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post('', response_model=UserDisplay)
def create_user(request: UserBase, db: Session = Depends(get_db)):
    user = db_user.create_user(db, request)
    return UserDisplay.model_validate(user)