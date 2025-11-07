# app/api/tracking.py
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.schemas.tracking import (
    PlaceBase,
    PlaceCreate,
    PlaceRead,
    TimeSlotBase,
    TimeSlotCreate,
    TimeSlotRead,
    WeatherObservationCreate,
    WeatherObservationRead,
    SleepSessionBase,
    SleepSessionCreate,
    SleepSessionRead,
    WorkoutSessionBase,
    WorkoutSessionCreate,
    WorkoutSessionRead,
    HealthHourlyBase,
    HealthHourlyCreate,
    HealthHourlyRead,
)
from app.cruds.tracking import (
    create_place,
    get_places_by_user,
    create_time_slot,
    get_time_slots_for_user_range,
    upsert_weather_observation,
    create_sleep_session,
    get_sleep_sessions_for_user_range,
    create_workout_session,
    get_workout_sessions_for_user_range,
    upsert_health_hourly,
    get_health_hourly_range,
)

router = APIRouter(tags=["tracking"])
# app/api/__init__.py 에서:
# router.include_router(tracking.router, prefix="/api")
# 이렇게 include 된다고 가정 (/api + 아래 path들)


# ---------------------------------------------------------------------------
# Places
# ---------------------------------------------------------------------------

@router.post(
    "/users/{user_id}/places",
    response_model=PlaceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_place_for_user(
    user_id: UUID,
    body: PlaceBase,
    db: Session = Depends(get_db),
):
    """
    유저의 Place 생성
    - body에는 user_id 없이 label / category / center_lat 등만 보냄
    """
    data = PlaceCreate(
        user_id=user_id,
        **body.model_dump(exclude_unset=True),
    )
    place = create_place(db, data)
    return place


@router.get(
    "/users/{user_id}/places",
    response_model=List[PlaceRead],
)
def list_places_for_user(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """유저의 Place 목록 조회"""
    places = get_places_by_user(db, user_id=user_id)
    return places


# ---------------------------------------------------------------------------
# TimeSlots
# ---------------------------------------------------------------------------

@router.post(
    "/users/{user_id}/time-slots",
    response_model=TimeSlotRead,
    status_code=status.HTTP_201_CREATED,
)
def create_time_slot_for_user(
    user_id: UUID,
    body: TimeSlotBase,
    db: Session = Depends(get_db),
):
    """
    유저의 1시간 단위 TimeSlot 생성
    - body.ts_hour 는 필수
    """
    data = TimeSlotCreate(
        user_id=user_id,
        **body.model_dump(exclude_unset=True),
    )
    slot = create_time_slot(db, data)
    return slot


@router.get(
    "/users/{user_id}/time-slots",
    response_model=List[TimeSlotRead],
)
def list_time_slots_for_user(
    user_id: UUID,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    """
    유저의 TimeSlot 범위 조회
    - query: ?start=2025-01-01T00:00:00Z&end=2025-01-02T00:00:00Z
    """
    slots = get_time_slots_for_user_range(db, user_id=user_id, start=start, end=end)
    return slots


# ---------------------------------------------------------------------------
# WeatherObservation (유저와 직접 연결 X)
# ---------------------------------------------------------------------------

@router.put(
    "/weather/observation",
    response_model=WeatherObservationRead,
)
def upsert_weather(
    body: WeatherObservationCreate,
    db: Session = Depends(get_db),
):
    """
    날씨 관측값 upsert
    - (nx, ny, as_of, provider) 기준으로 존재하면 업데이트, 없으면 생성
    """
    obs = upsert_weather_observation(db, body)
    return obs


# ---------------------------------------------------------------------------
# SleepSession
# ---------------------------------------------------------------------------

@router.post(
    "/users/{user_id}/sleep-sessions",
    response_model=SleepSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sleep_session_for_user(
    user_id: UUID,
    body: SleepSessionBase,
    db: Session = Depends(get_db),
):
    """
    수면 세션 생성
    """
    data = SleepSessionCreate(
        user_id=user_id,
        **body.model_dump(exclude_unset=True),
    )
    session = create_sleep_session(db, data)
    return session


@router.get(
    "/users/{user_id}/sleep-sessions",
    response_model=List[SleepSessionRead],
)
def list_sleep_sessions_for_user(
    user_id: UUID,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    """
    특정 기간의 수면 세션 조회
    """
    sessions = get_sleep_sessions_for_user_range(
        db,
        user_id=user_id,
        start=start,
        end=end,
    )
    return sessions


# ---------------------------------------------------------------------------
# WorkoutSession
# ---------------------------------------------------------------------------

@router.post(
    "/users/{user_id}/workout-sessions",
    response_model=WorkoutSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workout_session_for_user(
    user_id: UUID,
    body: WorkoutSessionBase,
    db: Session = Depends(get_db),
):
    """
    운동 세션 생성
    """
    data = WorkoutSessionCreate(
        user_id=user_id,
        **body.model_dump(exclude_unset=True),
    )
    session = create_workout_session(db, data)
    return session


@router.get(
    "/users/{user_id}/workout-sessions",
    response_model=List[WorkoutSessionRead],
)
def list_workout_sessions_for_user(
    user_id: UUID,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    """
    특정 기간의 운동 세션 조회
    """
    sessions = get_workout_sessions_for_user_range(
        db,
        user_id=user_id,
        start=start,
        end=end,
    )
    return sessions


# ---------------------------------------------------------------------------
# HealthHourly
# ---------------------------------------------------------------------------

@router.put(
    "/users/{user_id}/health-hourly",
    response_model=HealthHourlyRead,
)
def upsert_health_hourly_for_user(
    user_id: UUID,
    body: HealthHourlyBase,
    db: Session = Depends(get_db),
):
    """
    1시간 단위 헬스 데이터 upsert
    - ts_hour 가 동일한 레코드가 있으면 업데이트, 없으면 생성
    """
    data = HealthHourlyCreate(
        user_id=user_id,
        **body.model_dump(exclude_unset=True),
    )
    row = upsert_health_hourly(db, data)
    return row


@router.get(
    "/users/{user_id}/health-hourly",
    response_model=List[HealthHourlyRead],
)
def list_health_hourly_for_user(
    user_id: UUID,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    """
    특정 기간의 1시간 단위 헬스 데이터 조회
    """
    rows = get_health_hourly_range(
        db,
        user_id=user_id,
        start=start,
        end=end,
    )
    return rows
