# app/cruds/tracking.py
from datetime import datetime
from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.tracking import (
    Place,
    TimeSlot,
    WeatherObservation,
    SleepSession,
    WorkoutSession,
    HealthHourly,
)
from app.schemas.tracking import (
    PlaceCreate,
    TimeSlotCreate,
    WeatherObservationCreate,
    SleepSessionCreate,
    WorkoutSessionCreate,
    HealthHourlyCreate,
)


# ---------- Place ----------

def create_place(db: Session, data: PlaceCreate) -> Place:
    db_place = Place(**data.model_dump())
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place


def get_places_by_user(db: Session, user_id: UUID) -> List[Place]:
    return (
        db.query(Place)
        .filter(Place.user_id == user_id)
        .order_by(Place.first_seen.asc().nullsfirst())
        .all()
    )


# ---------- TimeSlot ----------

def create_time_slot(db: Session, data: TimeSlotCreate) -> TimeSlot:
    db_slot = TimeSlot(**data.model_dump())
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot


def get_time_slots_for_user_range(
    db: Session,
    user_id: UUID,
    start: datetime,
    end: datetime,
) -> List[TimeSlot]:
    return (
        db.query(TimeSlot)
        .filter(
            TimeSlot.user_id == user_id,
            TimeSlot.ts_hour >= start,
            TimeSlot.ts_hour < end,
        )
        .order_by(TimeSlot.ts_hour.asc())
        .all()
    )


# ---------- WeatherObservation ----------

def upsert_weather_observation(
    db: Session,
    data: WeatherObservationCreate,
) -> WeatherObservation:
    key = {
        "nx": data.nx,
        "ny": data.ny,
        "as_of": data.as_of,
        "provider": data.provider,
    }
    existing = db.query(WeatherObservation).get(
        (data.nx, data.ny, data.as_of, data.provider)
    )
    if existing:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    db_obs = WeatherObservation(**data.model_dump())
    db.add(db_obs)
    db.commit()
    db.refresh(db_obs)
    return db_obs


# ---------- SleepSession ----------

def create_sleep_session(
    db: Session,
    data: SleepSessionCreate,
) -> SleepSession:
    db_session = SleepSession(**data.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_sleep_sessions_for_user_range(
    db: Session,
    user_id: UUID,
    start: datetime,
    end: datetime,
) -> List[SleepSession]:
    return (
        db.query(SleepSession)
        .filter(
            SleepSession.user_id == user_id,
            SleepSession.start_at >= start,
            SleepSession.end_at <= end,
        )
        .order_by(SleepSession.start_at.asc())
        .all()
    )


# ---------- WorkoutSession ----------

def create_workout_session(
    db: Session,
    data: WorkoutSessionCreate,
) -> WorkoutSession:
    db_session = WorkoutSession(**data.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_workout_sessions_for_user_range(
    db: Session,
    user_id: UUID,
    start: datetime,
    end: datetime,
) -> List[WorkoutSession]:
    return (
        db.query(WorkoutSession)
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.start_at >= start,
            WorkoutSession.end_at <= end,
        )
        .order_by(WorkoutSession.start_at.asc())
        .all()
    )


# ---------- HealthHourly ----------

def upsert_health_hourly(
    db: Session,
    data: HealthHourlyCreate,
) -> HealthHourly:
    existing: Optional[HealthHourly] = (
        db.query(HealthHourly)
        .filter(
            HealthHourly.user_id == data.user_id,
            HealthHourly.ts_hour == data.ts_hour,
        )
        .first()
    )
    if existing:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    db_row = HealthHourly(**data.model_dump())
    db.add(db_row)
    db.commit()
    db.refresh(db_row)
    return db_row


def get_health_hourly_range(
    db: Session,
    user_id: UUID,
    start: datetime,
    end: datetime,
) -> List[HealthHourly]:
    return (
        db.query(HealthHourly)
        .filter(
            HealthHourly.user_id == user_id,
            HealthHourly.ts_hour >= start,
            HealthHourly.ts_hour < end,
        )
        .order_by(HealthHourly.ts_hour.asc())
        .all()
    )
