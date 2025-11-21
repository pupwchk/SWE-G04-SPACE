# app/models/user.py
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.db import Base


class User(Base):
    """
    ERD: User
      - id: uuid PK
      - email: text
      - created_at: timestamptz
      - deleted_at: timestamptz (nullable)
    """
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email = Column(String, unique=True, nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # 1:1 관계
    phone = relationship(
        "UserPhone",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    device = relationship(
        "UserDevice",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserPhone(Base):
    """
    ERD: UserPhone
      - id: uuid PK
      - user_id: uuid FK → User.id
      - e164_number, country_code, platform, model_name, display_name, ...
      - is_verified: boolean
      - registered_at, last_seen_at: timestamptz
      - UNIQUE(user_id)  -- 1인 1폰
    """
    __tablename__ = "user_phones"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_phones_user_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 한 유저당 한 개의 UserPhone
    )

    e164_number = Column(String, nullable=False)       # +821012345678
    country_code = Column(String(2), nullable=True)    # KR, JP, US 등
    platform = Column(String, nullable=True)           # ios | android
    model_name = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    device_id_hash = Column(String, nullable=True)
    push_token = Column(String, nullable=True)
    is_verified = Column(Boolean, nullable=False, server_default="false")

    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="phone")


class UserDevice(Base):
    """
    ERD: UserDevice
      - id: uuid PK
      - user_id: uuid FK → User.id
      - kind, platform, model_name, display_name, ...
      - registered_at, last_seen_at: timestamptz
      - UNIQUE(user_id)  -- 1인 1워치
    """
    __tablename__ = "user_devices"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_devices_user_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    kind = Column(String, nullable=False)              # apple_watch, fitbit 등
    platform = Column(String, nullable=True)           # watchOS, wearOS
    model_name = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    serial_hash = Column(String, nullable=True)

    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="device")
