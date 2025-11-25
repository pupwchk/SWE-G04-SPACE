# app/models/info.py
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Float,
    Integer,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.db import Base


# --------------------------------
# Appliance
# --------------------------------
class Appliance(Base):
    """
    ERD: Appliance
      - id: uuid PK
      - user_id: uuid FK → users.id
      - appliance_code: text
      - display_name: text
      - place_id: uuid FK → places.id (nullable)
      - vendor: text (nullable)
      - model_name: text (nullable)
      - external_device_id: text (nullable)
      - connection_type: text (nullable)
      - status: text (nullable)
      - registered_at: timestamptz
      - last_seen_at: timestamptz (nullable)
      - INDEX(user_id, appliance_code)
      - INDEX(user_id, place_id)
    """
    __tablename__ = "appliances"
    __table_args__ = (
        Index("ix_appliances_user_id_appliance_code", "user_id", "appliance_code"),
        Index("ix_appliances_user_id_place_id", "user_id", "place_id"),
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
    )

    place_id = Column(
        UUID(as_uuid=True),
        ForeignKey("places.id", ondelete="SET NULL"),
        nullable=True,
    )

    appliance_code = Column(String, nullable=False)  # AC / TV / AIR_PURIFIER / ...
    display_name = Column(String, nullable=False)

    vendor = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    external_device_id = Column(String, nullable=True)
    connection_type = Column(String, nullable=True)  # wifi | zigbee | ir | bluetooth ...
    status = Column(String, nullable=True)          # ONLINE | OFFLINE | ERROR | UNKNOWN

    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # 관계 설정 (1:N or 1:1)
    user = relationship("User", backref="appliances")
    place = relationship("Place", backref="appliances")

    air_conditioner_config = relationship(
        "AirConditionerConfig",
        back_populates="appliance",
        uselist=False,
        cascade="all, delete-orphan",
    )
    tv_config = relationship(
        "TvConfig",
        back_populates="appliance",
        uselist=False,
        cascade="all, delete-orphan",
    )
    air_purifier_config = relationship(
        "AirPurifierConfig",
        back_populates="appliance",
        uselist=False,
        cascade="all, delete-orphan",
    )
    light_config = relationship(
        "LightConfig",
        back_populates="appliance",
        uselist=False,
        cascade="all, delete-orphan",
    )
    humidifier_config = relationship(
        "HumidifierConfig",
        back_populates="appliance",
        uselist=False,
        cascade="all, delete-orphan",
    )


# --------------------------------
# AirConditionerConfig
# --------------------------------
class AirConditionerConfig(Base):
    """
    ERD: AirConditionerConfig
      - id: uuid PK
      - appliance_id: uuid FK → appliances.id
      - power_state: text (ON | OFF)
      - mode: text (nullable)
      - target_temp_c: double (nullable)
      - fan_speed: text (nullable)
      - swing_mode: text (nullable)
      - target_humidity_pct: double (nullable)
      - updated_at: timestamptz
      - UNIQUE(appliance_id)
    """
    __tablename__ = "air_conditioner_configs"
    __table_args__ = (
        UniqueConstraint("appliance_id", name="uq_air_conditioner_configs_appliance_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    appliance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appliances.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    power_state = Column(String, nullable=False)        # ON | OFF
    mode = Column(String, nullable=True)                # cool | heat | dry | fan | auto ...
    target_temp_c = Column(Float, nullable=True)
    fan_speed = Column(String, nullable=True)           # low | mid | high | auto ...
    swing_mode = Column(String, nullable=True)          # none | vertical | horizontal | both
    target_humidity_pct = Column(Float, nullable=True)  # (%)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    appliance = relationship("Appliance", back_populates="air_conditioner_config")


# --------------------------------
# TvConfig
# --------------------------------
class TvConfig(Base):
    """
    ERD: TvConfig
      - id: uuid PK
      - appliance_id: uuid FK → appliances.id
      - power_state: text
      - volume: int (nullable)
      - channel: int (nullable)
      - input_source: text (nullable)
      - brightness, contrast, color: int (nullable)
      - updated_at: timestamptz
      - UNIQUE(appliance_id)
    """
    __tablename__ = "tv_configs"
    __table_args__ = (
        UniqueConstraint("appliance_id", name="uq_tv_configs_appliance_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    appliance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appliances.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    power_state = Column(String, nullable=False)
    volume = Column(Integer, nullable=True)
    channel = Column(Integer, nullable=True)
    input_source = Column(String, nullable=True)  # HDMI1 / HDMI2 / TV / APP_NETFLIX ...
    brightness = Column(Integer, nullable=True)
    contrast = Column(Integer, nullable=True)
    color = Column(Integer, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    appliance = relationship("Appliance", back_populates="tv_config")


# --------------------------------
# AirPurifierConfig
# --------------------------------
class AirPurifierConfig(Base):
    """
    ERD: AirPurifierConfig
      - id: uuid PK
      - appliance_id: uuid FK → appliances.id
      - power_state: text
      - mode: text (nullable)
      - fan_speed: text (nullable)
      - ionizer_on: boolean (nullable)
      - target_pm10: int (nullable)
      - target_pm2_5: int (nullable)
      - updated_at: timestamptz
      - UNIQUE(appliance_id)
    """
    __tablename__ = "air_purifier_configs"
    __table_args__ = (
        UniqueConstraint("appliance_id", name="uq_air_purifier_configs_appliance_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    appliance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appliances.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    power_state = Column(String, nullable=False)
    mode = Column(String, nullable=True)           # auto | sleep | turbo ...
    fan_speed = Column(String, nullable=True)      # low | mid | high | auto
    ionizer_on = Column(Boolean, nullable=True)
    target_pm10 = Column(Integer, nullable=True)
    target_pm2_5 = Column(Integer, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    appliance = relationship("Appliance", back_populates="air_purifier_config")


# --------------------------------
# LightConfig
# --------------------------------
class LightConfig(Base):
    """
    ERD: LightConfig
      - id: uuid PK
      - appliance_id: uuid FK → appliances.id
      - power_state: text
      - brightness_pct: int (nullable)
      - color_temperature_k: int (nullable)
      - color_hex: text (nullable)
      - scene: text (nullable)
      - updated_at: timestamptz
      - UNIQUE(appliance_id)
    """
    __tablename__ = "light_configs"
    __table_args__ = (
        UniqueConstraint("appliance_id", name="uq_light_configs_appliance_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    appliance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appliances.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    power_state = Column(String, nullable=False)
    brightness_pct = Column(Integer, nullable=True)       # 0~100
    color_temperature_k = Column(Integer, nullable=True)  # 2700~6500
    color_hex = Column(String, nullable=True)             # #RRGGBB
    scene = Column(String, nullable=True)                 # reading / relax / movie ...

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    appliance = relationship("Appliance", back_populates="light_config")


# --------------------------------
# HumidifierConfig
# --------------------------------
class HumidifierConfig(Base):
    """
    ERD: HumidifierConfig
      - id: uuid PK
      - appliance_id: uuid FK → appliances.id
      - power_state: text
      - mode: text (nullable)
      - mist_level: int (nullable)
      - target_humidity_pct: int (nullable)
      - warm_mist: boolean (nullable)
      - updated_at: timestamptz
      - UNIQUE(appliance_id)
    """
    __tablename__ = "humidifier_configs"
    __table_args__ = (
        UniqueConstraint("appliance_id", name="uq_humidifier_configs_appliance_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    appliance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appliances.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    power_state = Column(String, nullable=False)
    mode = Column(String, nullable=True)           # auto | sleep | turbo ...
    mist_level = Column(Integer, nullable=True)
    target_humidity_pct = Column(Integer, nullable=True)
    warm_mist = Column(Boolean, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    appliance = relationship("Appliance", back_populates="humidifier_config")


# --------------------------------
# Character
# --------------------------------
class Character(Base):
    """
    ERD: Character
      - id: uuid PK
      - user_id: uuid FK → users.id
      - nickname: text
      - persona: text
      - (1:N) User → Character
    """
    __tablename__ = "characters"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    nickname = Column(String, nullable=False)
    persona = Column(String, nullable=False)

    user = relationship("User", backref="characters")
