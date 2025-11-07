# app/schemas/user.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# -----------------------------
# User
# -----------------------------
class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    """회원 가입 / 유저 생성용"""
    # 지금은 email만 받지만, 나중에 OAuth / 인증 붙일 때 확장 가능
    pass


class User(UserBase):
    """기본 유저 응답용"""
    id: UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------
# UserPhone
# -----------------------------
class UserPhoneBase(BaseModel):
    e164_number: str
    country_code: Optional[str] = None
    platform: Optional[str] = None
    model_name: Optional[str] = None
    display_name: Optional[str] = None
    os_version: Optional[str] = None
    device_id_hash: Optional[str] = None
    push_token: Optional[str] = None
    is_verified: Optional[bool] = None


class UserPhoneCreate(UserPhoneBase):
    user_id: UUID


class UserPhone(UserPhoneBase):
    id: UUID
    user_id: UUID
    registered_at: datetime
    last_seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------
# UserDevice
# -----------------------------
class UserDeviceBase(BaseModel):
    kind: str
    platform: Optional[str] = None
    model_name: Optional[str] = None
    display_name: Optional[str] = None
    os_version: Optional[str] = None
    serial_hash: Optional[str] = None


class UserDeviceCreate(UserDeviceBase):
    user_id: UUID


class UserDevice(UserDeviceBase):
    id: UUID
    user_id: UUID
    registered_at: datetime
    last_seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------
# User + Relations 묶은 응답 (원하면 사용)
# -----------------------------
class UserWithRelations(User):
    phone: Optional[UserPhone] = None
    device: Optional[UserDevice] = None
