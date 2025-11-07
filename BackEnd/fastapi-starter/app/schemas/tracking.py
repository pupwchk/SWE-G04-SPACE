# app/schemas/tracking.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# ---------- Place ----------

class PlaceBase(BaseModel):
    label: str
    category: Optional[str] = None
    center_lat: float
    center_lon: float
    radius_m: float
    visits_count: Optional[int] = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class PlaceCreate(PlaceBase):
    user_id: UUID


class PlaceRead(PlaceBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True


# ---------- TimeSlot ----------

class TimeSlotBase(BaseModel):
    ts_hour: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    horizontal_accuracy: Optional[float] = None
    vertical_accuracy: Optional[float] = None
    place_id: Optional[UUID] = None
    grid_nx: Optional[int] = None
    grid_ny: Optional[int] = None
    weather_provider: Optional[str] = None
    status: Optional[str] = None


class TimeSlotCreate(TimeSlotBase):
    user_id: UUID


class TimeSlotRead(TimeSlotBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True


# ---------- WeatherObservation ----------

class WeatherObservationBase(BaseModel):
    nx: int
    ny: int
    as_of: datetime
    provider: str
    condition_code: Optional[str] = None
    precip_type: Optional[str] = None
    temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_mps: Optional[float] = None
    pm10: Optional[float] = None
    pm2_5: Optional[float] = None
    raw_json: Optional[dict] = None


class WeatherObservationCreate(WeatherObservationBase):
    pass


class WeatherObservationRead(WeatherObservationBase):
    class Config:
        from_attributes = True


# ---------- SleepSession ----------

class SleepSessionBase(BaseModel):
    start_at: datetime
    end_at: datetime
    in_bed_hr: Optional[float] = None
    asleep_hr: Optional[float] = None
    awake_hr: Optional[float] = None
    core_hr: Optional[float] = None
    deep_hr: Optional[float] = None
    rem_hr: Optional[float] = None
    respiratory_rate: Optional[float] = None
    heart_rate_avg: Optional[float] = None
    efficiency: Optional[float] = None
    source: Optional[str] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None


class SleepSessionCreate(SleepSessionBase):
    user_id: UUID


class SleepSessionRead(SleepSessionBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True


# ---------- WorkoutSession ----------

class WorkoutSessionBase(BaseModel):
    start_at: datetime
    end_at: datetime
    workout_type: str
    step_count: Optional[int] = None
    distance_km: Optional[float] = None
    flights_climbed: Optional[int] = None
    active_energy_kcal: Optional[float] = None
    basal_energy_kcal: Optional[float] = None
    exercise_min: Optional[float] = None
    stand_hr: Optional[float] = None
    stand_hours: Optional[int] = None
    walking_speed_kmh: Optional[float] = None
    step_length_cm: Optional[float] = None
    walking_asymmetry_pct: Optional[float] = None
    double_support_pct: Optional[float] = None
    stair_speed_up_dps: Optional[float] = None
    stair_speed_down_dps: Optional[float] = None
    avg_hr: Optional[float] = None
    source: Optional[str] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    meta: Optional[dict] = None


class WorkoutSessionCreate(WorkoutSessionBase):
    user_id: UUID


class WorkoutSessionRead(WorkoutSessionBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True


# ---------- HealthHourly ----------

class HealthHourlyBase(BaseModel):
    ts_hour: datetime
    heart_rate_bpm: Optional[float] = None
    resting_hr_bpm: Optional[float] = None
    walking_hr_avg_bpm: Optional[float] = None
    hrv_sdnn_ms: Optional[float] = None
    vo2_max: Optional[float] = None
    spo2_pct: Optional[float] = None
    ecg_index: Optional[float] = None
    irregular_rhythm: Optional[bool] = None
    respiratory_rate_cpm: Optional[float] = None
    oxygen_saturation_pct: Optional[float] = None
    env_audio_db: Optional[float] = None
    headphone_audio_db: Optional[float] = None
    env_sound_level_db: Optional[float] = None
    wrist_temp_c: Optional[float] = None
    mindful_min: Optional[float] = None
    daylight_min: Optional[float] = None
    source: Optional[str] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    synced_at: Optional[datetime] = None


class HealthHourlyCreate(HealthHourlyBase):
    user_id: UUID


class HealthHourlyRead(HealthHourlyBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True
