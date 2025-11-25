# app/api/appliances.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.db import get_db
import app.schemas.info as infoSchema
import app.cruds.info as infoCruds

router = APIRouter()


# -----------------------------
# Appliances
# -----------------------------

@router.get("/user/{user_id}", response_model=list[infoSchema.Appliance])
def get_appliances_by_user(
    user_id: UUID,
    appliance_code: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    특정 유저의 가전(Appliance) 리스트 조회
    - appliance_code 로 필터링 가능 (예: "AC", "TV", "AIR_PURIFIER", ...)
    """
    appliances = infoCruds.get_appliances_by_user(
        db,
        user_id=user_id,
        appliance_code=appliance_code,
        skip=skip,
        limit=limit,
    )
    return appliances


@router.post(
    "/",
    response_model=infoSchema.Appliance,
    status_code=status.HTTP_201_CREATED,
)
def create_appliance(
    appliance: infoSchema.ApplianceCreate,
    db: Session = Depends(get_db),
):
    """
    가전(Appliance) 생성
    - body 에 user_id, appliance_code, display_name 등 포함
    """
    return infoCruds.create_appliance(db, appliance)


@router.get("/{appliance_id}", response_model=infoSchema.Appliance)
def get_appliance(
    appliance_id: UUID,
    db: Session = Depends(get_db),
):
    """
    단일 가전 조회
    """
    db_appliance = infoCruds.get_appliance(db, appliance_id=appliance_id)
    if not db_appliance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appliance not found",
        )
    return db_appliance


@router.delete("/{appliance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appliance(
    appliance_id: UUID,
    db: Session = Depends(get_db),
):
    """
    가전 삭제
    """
    ok = infoCruds.delete_appliance(db, appliance_id=appliance_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appliance not found",
        )
    return None


# -----------------------------
# AirConditioner Config
# -----------------------------

@router.post(
    "/config/ac",
    response_model=infoSchema.AirConditionerConfig,
    status_code=status.HTTP_201_CREATED,
)
def upsert_air_conditioner_config(
    payload: infoSchema.AirConditionerConfigCreate,
    db: Session = Depends(get_db),
):
    """
    에어컨 설정 업서트
    - appliance_id 기준 1:1
    - 이미 있으면 UPDATE, 없으면 CREATE
    """
    return infoCruds.upsert_air_conditioner_config(db, payload)


@router.get(
    "/config/ac/{appliance_id}",
    response_model=infoSchema.AirConditionerConfig,
)
def get_air_conditioner_config(
    appliance_id: UUID,
    db: Session = Depends(get_db),
):
    """
    에어컨 설정 조회 (appliance_id 기준)
    """
    cfg = infoCruds.get_air_conditioner_config_by_appliance(db, appliance_id)
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AirConditionerConfig not found",
        )
    return cfg


# -----------------------------
# TV Config
# -----------------------------

@router.post(
    "/config/tv",
    response_model=infoSchema.TvConfig,
    status_code=status.HTTP_201_CREATED,
)
def upsert_tv_config(
    payload: infoSchema.TvConfigCreate,
    db: Session = Depends(get_db),
):
    """
    TV 설정 업서트
    """
    return infoCruds.upsert_tv_config(db, payload)


@router.get(
    "/config/tv/{appliance_id}",
    response_model=infoSchema.TvConfig,
)
def get_tv_config(
    appliance_id: UUID,
    db: Session = Depends(get_db),
):
    """
    TV 설정 조회
    """
    cfg = infoCruds.get_tv_config_by_appliance(db, appliance_id)
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TvConfig not found",
        )
    return cfg


# -----------------------------
# AirPurifier Config
# -----------------------------

@router.post(
    "/config/air_purifier",
    response_model=infoSchema.AirPurifierConfig,
    status_code=status.HTTP_201_CREATED,
)
def upsert_air_purifier_config(
    payload: infoSchema.AirPurifierConfigCreate,
    db: Session = Depends(get_db),
):
    """
    공기청정기 설정 업서트
    """
    return infoCruds.upsert_air_purifier_config(db, payload)


@router.get(
    "/config/air_purifier/{appliance_id}",
    response_model=infoSchema.AirPurifierConfig,
)
def get_air_purifier_config(
    appliance_id: UUID,
    db: Session = Depends(get_db),
):
    """
    공기청정기 설정 조회
    """
    cfg = infoCruds.get_air_purifier_config_by_appliance(db, appliance_id)
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AirPurifierConfig not found",
        )
    return cfg


# -----------------------------
# Light Config
# -----------------------------

@router.post(
    "/config/light",
    response_model=infoSchema.LightConfig,
    status_code=status.HTTP_201_CREATED,
)
def upsert_light_config(
    payload: infoSchema.LightConfigCreate,
    db: Session = Depends(get_db),
):
    """
    조명 설정 업서트
    """
    return infoCruds.upsert_light_config(db, payload)


@router.get(
    "/config/light/{appliance_id}",
    response_model=infoSchema.LightConfig,
)
def get_light_config(
    appliance_id: UUID,
    db: Session = Depends(get_db),
):
    """
    조명 설정 조회
    """
    cfg = infoCruds.get_light_config_by_appliance(db, appliance_id)
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LightConfig not found",
        )
    return cfg


# -----------------------------
# Humidifier Config
# -----------------------------

@router.post(
    "/config/humidifier",
    response_model=infoSchema.HumidifierConfig,
    status_code=status.HTTP_201_CREATED,
)
def upsert_humidifier_config(
    payload: infoSchema.HumidifierConfigCreate,
    db: Session = Depends(get_db),
):
    """
    가습기 설정 업서트
    """
    return infoCruds.upsert_humidifier_config(db, payload)


@router.get(
    "/config/humidifier/{appliance_id}",
    response_model=infoSchema.HumidifierConfig,
)
def get_humidifier_config(
    appliance_id: UUID,
    db: Session = Depends(get_db),
):
    """
    가습기 설정 조회
    """
    cfg = infoCruds.get_humidifier_config_by_appliance(db, appliance_id)
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HumidifierConfig not found",
        )
    return cfg
