from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from sqlalchemy.orm.session import Session
from db.database import get_db
from dotenv import load_dotenv
from db import db_user
from db.models import User, RefreshTokens
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
        expire = datetime.now(tz = timezone.utc) + timedelta(minutes=3)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(db: Session, user_id: int):

    expire = datetime.now(tz=timezone.utc) + timedelta(days=7)
    to_encode = {"sub": str(user_id),"exp": expire,"type": "refresh"}
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    db_user.create_refresh_token_record(db=db, user_id=user_id, token=refresh_token, expires_at=expire)
    return refresh_token


def get_refresh_token_record(db: Session, token: str):
    return db_user.get_refresh_token_record(db, token)


def revoke_refresh_token_record(db: Session, token: str):
    return db_user.revoke_refresh_token_record(db, token)


def verify_refresh_token(db: Session, token: str):
    db_token = get_refresh_token_record(db, token)
    if not db_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if db_token.is_revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    expires_at = db_token.expires_at
    if expires_at is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    # Normalize naive and aware datetime for safe comparison
    if expires_at.tzinfo is None or expires_at.tzinfo.utcoffset(expires_at) is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    payload = get_token_payload(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    if int(payload.get("sub")) != db_token.user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token user mismatch")
    return db_token


def get_token_payload(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload

def get_current_user(token:str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail='Could not validate credentials',
                                         headers={"WWW-Authenticate":"Bearer"})
    try:
        print(f"Token received for authentication: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credential_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credential_exception
    except JWTError:
        raise credential_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credential_exception
    return user
