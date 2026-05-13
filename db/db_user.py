from routers.schemas import UserBase, UserMeasurementsBase, UserStatsBase
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from db.models import User, UserStats, RefreshTokens, UserMeasurementsEntry
from resources.logger import Logger
from datetime import datetime, timedelta, timezone
from db.hashing import Hash

logger = Logger()

def create_user(db: Session, request: UserBase, verification_code: str): 
    password = Hash.bcrypt(request.password)
    hashed_code = Hash.bcrypt(verification_code)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=1)
    new_user = User(username=request.username, email=request.email.lower(), hashed_password=password,
                    verification_code=hashed_code, code_expiry=expiry, is_verified=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User created: {new_user.username}")
    return new_user

# Refresh token helpers

def create_refresh_token_record(db: Session, user_id: int, token: str, expires_at):
    db_token = RefreshTokens(user_id=user_id, token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_refresh_token_record(db: Session, token: str):
    return db.query(RefreshTokens).filter(RefreshTokens.token == token).first()


def revoke_refresh_token_record(db: Session, token: str):
    db_token = get_refresh_token_record(db, token)
    if not db_token:
        return None
    db_token.is_revoked = True
    db.commit()
    db.refresh(db_token)
    return db_token


def revoke_all_refresh_tokens_for_user(db: Session, user_id: int):
    tokens = db.query(RefreshTokens).filter(RefreshTokens.user_id == user_id, RefreshTokens.is_revoked == False).all()
    for t in tokens:
        t.is_revoked = True
    db.commit()
    return tokens


def get_active_refresh_tokens_for_user(db: Session, user_id: int):
    now = datetime.now(timezone.utc)
    return db.query(RefreshTokens).filter(
        RefreshTokens.user_id == user_id,
        RefreshTokens.is_revoked == False,
        RefreshTokens.expires_at > now
    ).all()


def get_user_by_username(db: Session, username: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = f"User with username {username} not found")
    return user

def get_user_stats_by_username(db: Session, user: User):
    return user.user_stats

def create_user_stats(db: Session, user: User, stats: UserStatsBase):
    user_stats = UserStats(
        user_id=user.id,
        name=stats.name or user.username,
        height=stats.height or 0,
        birthdate=datetime.strptime(stats.birthdate, "%d/%m/%Y") if stats.birthdate else None,
        gender=stats.gender,
        activity_level=stats.activity_level,
    )
    db.add(user_stats)
    db.commit()
    db.refresh(user_stats)
    return user_stats


def update_user_stats(db: Session, user: User, stats: UserStatsBase):
    user_stats = user.user_stats
    print(f"Current stats for user {user.username}: {user_stats}")
    if not user_stats:
        return create_user_stats(db, user, stats)

    if stats.name is not None:
        user_stats.name = stats.name
    if stats.height is not None:
        user_stats.height = stats.height
    if stats.birthdate is not None:
        user_stats.birthdate = datetime.strptime(stats.birthdate, "%d/%m/%Y")
    if stats.gender is not None:
        user_stats.gender = stats.gender
    if stats.activity_level is not None:
        user_stats.activity_level = stats.activity_level
    if stats.profile_photo_url is not None:
        user_stats.profile_photo_url = stats.profile_photo_url
    db.commit()
    db.refresh(user_stats)
    return user_stats

def add_new_measurement_entry(db: Session, user: User, schema: UserMeasurementsBase):
    measurement_entry = UserMeasurementsEntry(
        user_id=user.id,
        weight=schema.weight,
        timestamp = datetime.strptime(schema.timestamp, "%d/%m/%Y") if schema.timestamp else datetime.now(timezone.utc),
        arm_circumference_r=schema.arm_circumference_r,
        arm_circumference_l=schema.arm_circumference_l,
        waist_circumference=schema.waist_circumference,
        hip_circumference=schema.hip_circumference,
        chest_circumference=schema.chest_circumference,
        quad_circumference_r=schema.quad_circumference_r,
        quad_circumference_l=schema.quad_circumference_l,
        shoulder_circumference=schema.shoulder_circumference,
        fat_percentage=schema.fat_percentage
    )
    db.add(measurement_entry)
    db.commit()
    db.refresh(measurement_entry)
    return measurement_entry

def modify_measurement_entry(db: Session, entry_id: int, schema: UserMeasurementsBase):
    entry = db.query(UserMeasurementsEntry).filter(UserMeasurementsEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Measurement entry with id {entry_id} not found")
    if schema.weight is not None:
        entry.weight = schema.weight
    if schema.timestamp is not None:
        entry.timestamp = datetime.strptime(schema.timestamp, "%d/%m/%Y")
    if schema.arm_circumference_r is not None:
        entry.arm_circumference_r = schema.arm_circumference_r
    if schema.arm_circumference_l is not None:
        entry.arm_circumference_l = schema.arm_circumference_l
    if schema.waist_circumference is not None:
        entry.waist_circumference = schema.waist_circumference
    if schema.hip_circumference is not None:
        entry.hip_circumference = schema.hip_circumference
    if schema.chest_circumference is not None:
        entry.chest_circumference = schema.chest_circumference
    if schema.quad_circumference_r is not None:
        entry.quad_circumference_r = schema.quad_circumference_r
    if schema.quad_circumference_l is not None:
        entry.quad_circumference_l = schema.quad_circumference_l
    if schema.shoulder_circumference is not None:
        entry.shoulder_circumference = schema.shoulder_circumference
    if schema.fat_percentage is not None:
        entry.fat_percentage = schema.fat_percentage
    db.commit()
    db.refresh(entry)
    return entry

def delete_measurement_entry(db: Session, entry_id: int):
    entry = db.query(UserMeasurementsEntry).filter(UserMeasurementsEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Measurement entry with id {entry_id} not found")
    db.delete(entry)
    db.commit()
    return entry

def get_user_measurement_entries(db: Session, user: User):
    entries = db.query(UserMeasurementsEntry).filter(UserMeasurementsEntry.user_id == user.id).order_by(UserMeasurementsEntry.timestamp.desc()).all()
    for entry in entries:
        if entry.timestamp:
            entry.timestamp = entry.timestamp.strftime("%d/%m/%Y")
    return entries