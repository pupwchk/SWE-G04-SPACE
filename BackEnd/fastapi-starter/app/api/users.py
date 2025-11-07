# app/api/users.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.db import get_db
import app.schemas.user as userSchema
import app.cruds.user as userCruds

router = APIRouter()


# -----------------------------
# Users
# -----------------------------

@router.get("/", response_model=list[userSchema.User])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """전체 유저 리스트 조회"""
    users = userCruds.get_users(db, skip=skip, limit=limit)
    return users


@router.post(
    "/",
    response_model=userSchema.User,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: userSchema.UserCreate,
    db: Session = Depends(get_db),
):
    """유저 생성 (현재는 email만 사용)"""
    db_user = userCruds.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return userCruds.create_user(db=db, user=user)


@router.get("/{user_id}", response_model=userSchema.User)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """단일 유저 조회"""
    user = userCruds.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/{user_id}/profile", response_model=userSchema.UserWithRelations)
def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    User + UserPhone + UserDevice 를 한 번에 반환하는 프로필 조회
    """
    user = userCruds.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # SQLAlchemy relationship (phone, device)가 같이 직렬화됨
    return user


# -----------------------------
# UserPhone
# -----------------------------

@router.get(
    "/{user_id}/phone",
    response_model=userSchema.UserPhone,
)
def get_user_phone(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """유저의 휴대폰 정보 조회"""
    phone = userCruds.get_user_phone(db, user_id=user_id)
    if not phone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone not found")
    return phone


@router.put(
    "/{user_id}/phone",
    response_model=userSchema.UserPhone,
)
def upsert_user_phone(
    user_id: UUID,
    body: userSchema.UserPhoneBase,
    db: Session = Depends(get_db),
):
    """
    유저의 휴대폰 정보 생성/업데이트 (upsert)
    - body에는 user_id 없이 휴대폰 정보만 보냄
    """
    data = userSchema.UserPhoneCreate(
        user_id=user_id,
        **body.model_dump(exclude_unset=True),
    )
    phone = userCruds.create_or_update_user_phone(db, data=data)
    return phone


# -----------------------------
# UserDevice
# -----------------------------

@router.get(
    "/{user_id}/device",
    response_model=userSchema.UserDevice,
)
def get_user_device(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """유저의 웨어러블(디바이스) 정보 조회"""
    device = userCruds.get_user_device(db, user_id=user_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.put(
    "/{user_id}/device",
    response_model=userSchema.UserDevice,
)
def upsert_user_device(
    user_id: UUID,
    body: userSchema.UserDeviceBase,
    db: Session = Depends(get_db),
):
    """
    유저의 웨어러블 정보 생성/업데이트 (upsert)
    - body에는 user_id 없이 디바이스 정보만 보냄
    """
    data = userSchema.UserDeviceCreate(
        user_id=user_id,
        **body.model_dump(exclude_unset=True),
    )
    device = userCruds.create_or_update_user_device(db, data=data)
    return device
