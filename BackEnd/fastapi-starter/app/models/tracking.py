# app/models/tracking.py
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.db import Base


class StressAssessment(Base):
    """스트레스 평가 결과 (1분 간격)"""
    __tablename__ = "stress_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stress_level = Column(String, nullable=False)  # VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH
    stress_score = Column(Float, nullable=False)  # 0-100
    confidence = Column(Float, nullable=False)
    hrv_metrics = Column(JSONB, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Place(Base):
    """
    ERD: Place
    - User 1 : N Place
    """
    __tablename__ = "places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    label = Column(String, nullable=False)
    category = Column(String, nullable=True)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    radius_m = Column(Float, nullable=False)
    visits_count = Column(Integer, nullable=False, server_default="0")
    first_seen = Column(DateTime(timezone=True), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="places")
    timeslots = relationship("TimeSlot", back_populates="place")


class TimeSlot(Base):
    """
    ERD: TimeSlot
    - 1시간 단위 시간 블록
    """
    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint("user_id", "ts_hour", name="uq_time_slots_user_hour"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ts_hour = Column(DateTime(timezone=True), nullable=False, index=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    horizontal_accuracy = Column(Float, nullable=True)
    vertical_accuracy = Column(Float, nullable=True)

    place_id = Column(
        UUID(as_uuid=True),
        ForeignKey("places.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    grid_nx = Column(Integer, nullable=True)
    grid_ny = Column(Integer, nullable=True)
    weather_provider = Column(String, nullable=True)
    status = Column(String, nullable=True)  # MISSING | PARTIAL | COMPLETE

    user = relationship("User", backref="time_slots")
    place = relationship("Place", back_populates="timeslots")


class WeatherObservation(Base):
    """
    ERD: WeatherObservation
    - (nx, ny, as_of, provider) 복합키
    """
    __tablename__ = "weather_observations"

    nx = Column(Integer, primary_key=True)
    ny = Column(Integer, primary_key=True)
    as_of = Column(DateTime(timezone=True), primary_key=True)
    provider = Column(String, primary_key=True)

    condition_code = Column(String, nullable=True)
    precip_type = Column(String, nullable=True)  # none | rain | snow | sleet
    temp_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    wind_speed_mps = Column(Float, nullable=True)
    pm10 = Column(Float, nullable=True)
    pm2_5 = Column(Float, nullable=True)

    raw_json = Column(JSONB, nullable=True)


class SleepSession(Base):
    """
    ERD: SleepSession
    """
    __tablename__ = "sleep_sessions"
    __table_args__ = (
        # 자주 조회할 패턴: user_id + 기간
        UniqueConstraint("user_id", "start_at", "end_at", name="uq_sleep_user_period"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=False, index=True)

    in_bed_hr = Column(Float, nullable=True)
    asleep_hr = Column(Float, nullable=True)
    awake_hr = Column(Float, nullable=True)
    core_hr = Column(Float, nullable=True)
    deep_hr = Column(Float, nullable=True)
    rem_hr = Column(Float, nullable=True)
    respiratory_rate = Column(Float, nullable=True)
    heart_rate_avg = Column(Float, nullable=True)
    efficiency = Column(Float, nullable=True)

    source = Column(String, nullable=True)
    device_model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)

    user = relationship("User", backref="sleep_sessions")


class WorkoutSession(Base):
    """
    ERD: WorkoutSession
    """
    __tablename__ = "workout_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=False, index=True)

    workout_type = Column(String, nullable=False)  # running / cycling / ...
    step_count = Column(Integer, nullable=True)
    distance_km = Column(Float, nullable=True)
    flights_climbed = Column(Integer, nullable=True)
    active_energy_kcal = Column(Float, nullable=True)
    basal_energy_kcal = Column(Float, nullable=True)
    exercise_min = Column(Float, nullable=True)
    stand_hr = Column(Float, nullable=True)
    stand_hours = Column(Integer, nullable=True)
    walking_speed_kmh = Column(Float, nullable=True)
    step_length_cm = Column(Float, nullable=True)
    walking_asymmetry_pct = Column(Float, nullable=True)
    double_support_pct = Column(Float, nullable=True)
    stair_speed_up_dps = Column(Float, nullable=True)
    stair_speed_down_dps = Column(Float, nullable=True)
    avg_hr = Column(Float, nullable=True)
    source = Column(String, nullable=True)
    device_model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    meta = Column(JSONB, nullable=True)

    user = relationship("User", backref="workout_sessions")


class HealthHourly(Base):
    """
    ERD: HealthHourly
    """
    __tablename__ = "health_hourly"
    __table_args__ = (
        UniqueConstraint("user_id", "ts_hour", name="uq_health_user_hour"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ts_hour = Column(DateTime(timezone=True), nullable=False, index=True)

    heart_rate_bpm = Column(Float, nullable=True)
    resting_hr_bpm = Column(Float, nullable=True)
    walking_hr_avg_bpm = Column(Float, nullable=True)
    hrv_sdnn_ms = Column(Float, nullable=True)
    vo2_max = Column(Float, nullable=True)
    spo2_pct = Column(Float, nullable=True)
    ecg_index = Column(Float, nullable=True)
    irregular_rhythm = Column(Boolean, nullable=True)
    respiratory_rate_cpm = Column(Float, nullable=True)
    oxygen_saturation_pct = Column(Float, nullable=True)
    env_audio_db = Column(Float, nullable=True)
    headphone_audio_db = Column(Float, nullable=True)
    env_sound_level_db = Column(Float, nullable=True)
    wrist_temp_c = Column(Float, nullable=True)
    mindful_min = Column(Float, nullable=True)
    daylight_min = Column(Float, nullable=True)

    source = Column(String, nullable=True)
    device_model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    synced_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user = relationship("User", backref="health_hourly")
