# app/schemas.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


# ---------- User ----------

class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    deleted_at: datetime | None = None

    class Config:
        orm_mode = True


# ---------- UserPhone ----------

class UserPhoneBase(BaseModel):
    e164_number: str
    country_code: str | None = None
    platform: str | None = None
    model_name: str | None = None
    display_name: str | None = None
    os_version: str | None = None
    device_id_hash: str | None = None
    push_token: str | None = None
    is_verified: bool | None = None


class UserPhoneCreate(UserPhoneBase):
    user_id: UUID


class UserPhoneRead(UserPhoneBase):
    id: UUID
    user_id: UUID
    registered_at: datetime
    last_seen_at: datetime | None = None

    class Config:
        orm_mode = True


# ---------- UserDevice ----------

class UserDeviceBase(BaseModel):
    kind: str
    platform: str | None = None
    model_name: str | None = None
    display_name: str | None = None
    os_version: str | None = None
    serial_hash: str | None = None


class UserDeviceCreate(UserDeviceBase):
    user_id: UUID


class UserDeviceRead(UserDeviceBase):
    id: UUID
    user_id: UUID
    registered_at: datetime
    last_seen_at: datetime | None = None

    class Config:
        orm_mode = True


# ---------- (선택) User + 연관정보 묶어서 응답하고 싶을 때 ----------

class UserWithRelations(UserRead):
    phone: UserPhoneRead | None = None
    device: UserDeviceRead | None = None
