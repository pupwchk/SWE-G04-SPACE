# app/cruds/user.py
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User, UserPhone, UserDevice
from app.schemas.user import UserCreate, UserPhoneCreate, UserDeviceCreate


# -----------------------------
# User
# -----------------------------
def get_user(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        email=user.email,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# -----------------------------
# UserPhone
# -----------------------------
def get_user_phone(db: Session, user_id: UUID) -> UserPhone | None:
    return db.query(UserPhone).filter(UserPhone.user_id == user_id).first()


def create_or_update_user_phone(db: Session, data: UserPhoneCreate) -> UserPhone:
    existing = get_user_phone(db, data.user_id)
    if existing:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    db_phone = UserPhone(**data.model_dump())
    db.add(db_phone)
    db.commit()
    db.refresh(db_phone)
    return db_phone


# -----------------------------
# UserDevice
# -----------------------------
def get_user_device(db: Session, user_id: UUID) -> UserDevice | None:
    return db.query(UserDevice).filter(UserDevice.user_id == user_id).first()


def create_or_update_user_device(db: Session, data: UserDeviceCreate) -> UserDevice:
    existing = get_user_device(db, data.user_id)
    if existing:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    db_device = UserDevice(**data.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device
