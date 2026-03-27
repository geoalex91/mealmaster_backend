from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from sqlalchemy.orm.session import Session
from db.database import get_db
from dotenv import load_dotenv
from db import db_user
from db.models import RefreshTokens
import os

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY","no key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.now(tz = timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz = timezone.utc) + timedelta(minutes=15)
    to_encode = {"user_id": str(user_id), "exp": expire,"type": "access"}
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(db: Session, user_id: int):

    expire = datetime.now(tz=timezone.utc) + timedelta(days=7)
    to_encode = {"sub": str(user_id),"exp": expire,"type": "refresh"}
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    db_token = RefreshTokens(
        user_id=user_id,
        token=refresh_token,
        expires_at=expire
    )
    db.add(db_token)
    db.commit()
    return refresh_token

def get_token_payload(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload

def get_current_user(token:str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail = 'Could not validate creentials',
                                         headers = {"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str = payload.get("sub")
        if username is None:
            raise credential_exception
    except JWTError:
        raise credential_exception
    user = db_user.get_user_by_username(db,username)
    if user is None:
        raise credential_exception
    return user
