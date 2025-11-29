# 이전 버전
# app/models.py
import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# from .database import Base 


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
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
    __tablename__ = "user_phones"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1인 1폰
    )

    e164_number = Column(String, nullable=False)          # +821012345678
    country_code = Column(String(2), nullable=True)       # KR, JP, US ...
    platform = Column(String, nullable=True)              # ios | android
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
    __tablename__ = "user_devices"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1인 1워치
    )

    kind = Column(String, nullable=False)                 # apple_watch, fitbit ...
    platform = Column(String, nullable=True)              # watchOS, wearOS ...
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
