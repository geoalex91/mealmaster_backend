from routers.schemas import UserBase
from sqlalchemy.orm import Session
from db.models import User

def create_user(db: Session, request: UserBase): 
    fake_hashed_password = request.password + "notreallyhashed"
    new_user = User(username=request.username, email=request.email, hashed_password=fake_hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user