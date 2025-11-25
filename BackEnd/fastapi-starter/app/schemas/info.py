from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# -----------------------------
# Appliance
# -----------------------------
class ApplianceBase(BaseModel):
    appliance_code: str
    display_name: str
    place_id: Optional[UUID] = None
    vendor: Optional[str] = None
    model_name: Optional[str] = None
    external_device_id: Optional[str] = None
    connection_type: Optional[str] = None  # wifi | zigbee | ir | bluetooth ...
    status: Optional[str] = None           # ONLINE | OFFLINE | ERROR | UNKNOWN


class ApplianceCreate(ApplianceBase):
    user_id: UUID


class Appliance(ApplianceBase):
    id: UUID
    user_id: UUID
    registered_at: datetime
    last_seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------
# AirConditionerConfig
# -----------------------------
class AirConditionerConfigBase(BaseModel):
    power_state: str                      # ON | OFF
    mode: Optional[str] = None           # cool | heat | dry | fan | auto ...
    target_temp_c: Optional[float] = None
    fan_speed: Optional[str] = None      # low | mid | high | auto ...
    swing_mode: Optional[str] = None     # none | vertical | horizontal | both
    target_humidity_pct: Optional[float] = None


class AirConditionerConfigCreate(AirConditionerConfigBase):
    appliance_id: UUID


class AirConditionerConfig(AirConditionerConfigBase):
    id: UUID
    appliance_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------
# TvConfig
# -----------------------------
class TvConfigBase(BaseModel):
    power_state: str
    volume: Optional[int] = None
    channel: Optional[int] = None
    input_source: Optional[str] = None   # HDMI1 / HDMI2 / TV / APP_NETFLIX ...
    brightness: Optional[int] = None
    contrast: Optional[int] = None
    color: Optional[int] = None


class TvConfigCreate(TvConfigBase):
    appliance_id: UUID


class TvConfig(TvConfigBase):
    id: UUID
    appliance_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------
# AirPurifierConfig
# -----------------------------
class AirPurifierConfigBase(BaseModel):
    power_state: str
    mode: Optional[str] = None           # auto | sleep | turbo ...
    fan_speed: Optional[str] = None      # low | mid | high | auto
    ionizer_on: Optional[bool] = None
    target_pm10: Optional[int] = None
    target_pm2_5: Optional[int] = None


class AirPurifierConfigCreate(AirPurifierConfigBase):
    appliance_id: UUID


class AirPurifierConfig(AirPurifierConfigBase):
    id: UUID
    appliance_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------
# LightConfig
# -----------------------------
class LightConfigBase(BaseModel):
    power_state: str
    brightness_pct: Optional[int] = None       # 0~100 (%)
    color_temperature_k: Optional[int] = None  # 2700K ~ 6500K
    color_hex: Optional[str] = None            # #RRGGBB
    scene: Optional[str] = None                # reading / relax / movie ...


class LightConfigCreate(LightConfigBase):
    appliance_id: UUID


class LightConfig(LightConfigBase):
    id: UUID
    appliance_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------
# HumidifierConfig
# -----------------------------
class HumidifierConfigBase(BaseModel):
    power_state: str
    mode: Optional[str] = None          # auto | sleep | turbo ...
    mist_level: Optional[int] = None
    target_humidity_pct: Optional[int] = None
    warm_mist: Optional[bool] = None


class HumidifierConfigCreate(HumidifierConfigBase):
    appliance_id: UUID


class HumidifierConfig(HumidifierConfigBase):
    id: UUID
    appliance_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------
# Character
# -----------------------------
class CharacterBase(BaseModel):
    nickname: str
    persona: str  # 캐릭터 페르소나 텍스트


class CharacterCreate(CharacterBase):
    user_id: UUID
    # 만약 클라이언트가 uuid를 생성해서 보내고 싶으면:
    # id: UUID 추가하면 됨.

class CharacterUpdate(BaseModel):
    nickname: Optional[str] = None
    persona: Optional[str] = None

class Character(CharacterBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True
