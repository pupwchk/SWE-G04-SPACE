# app/api/appliances.py
from uuid import UUID
from typing import Optional, Dict, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.config.db import get_db
import app.schemas.info as infoSchema
import app.cruds.info as infoCruds
from app.services.appliance_control_service import appliance_control_service
from app.services.appliance_rule_engine import appliance_rule_engine
from app.services.weather_service import weather_service
from app.models.appliance import ApplianceConditionRule
from app.utils.user_utils import get_user_uuid_by_identifier

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 새로운 제어 API 스키마 ==========
class ApplianceControlRequest(BaseModel):
    """가전 제어 요청"""
    appliance_type: str = Field(..., description="가전 종류")
    action: str = Field(..., description="on/off/set")
    settings: Optional[Dict[str, Any]] = Field(None, description="설정값")


class ApplianceRecommendRequest(BaseModel):
    """가전 추천 요청"""
    latitude: float
    longitude: float
    sido: str = "서울"


class RuleModifyRequest(BaseModel):
    """가전 규칙 수정 요청"""
    appliance_type: str = Field(..., description="가전 종류 (에어컨, 제습기 등)")
    fatigue_level: Optional[int] = Field(None, description="피로도 레벨 (1-4)")
    operation: str = Field(..., description="enable/disable/modify_threshold")
    new_threshold: Optional[Dict[str, Any]] = Field(None, description="새로운 임계값 (modify_threshold일 때 필수)")
    is_enabled: Optional[bool] = Field(None, description="활성화 여부 (enable/disable일 때 사용)")


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


# ========== 새로운 제어 API ==========

@router.post("/smart-control/{user_identifier}")
async def smart_control_appliances(
    user_identifier: str,
    request: ApplianceControlRequest,
    db: Session = Depends(get_db)
):
    """
    가전 스마트 제어 (Rule Engine 기반)
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        result = appliance_control_service.execute_command(
            db=db,
            user_id=str(user_uuid),
            appliance_type=request.appliance_type,
            action=request.action,
            settings=request.settings,
            triggered_by="manual"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Control error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend/{user_identifier}")
async def recommend_appliances(
    user_identifier: str,
    request: ApplianceRecommendRequest,
    db: Session = Depends(get_db)
):
    """
    현재 상황 기반 가전 제어 추천 (피로도 + 날씨 분석)
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        weather_data = await weather_service.get_combined_weather(
            db=db,
            latitude=request.latitude,
            longitude=request.longitude,
            sido_name=request.sido
        )

        recommendations = appliance_rule_engine.get_appliances_to_control(
            db=db,
            user_id=str(user_uuid),
            weather_data=weather_data
        )

        return {
            "user_id": user_identifier,
            "weather": {
                "temperature": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity"),
                "pm10": weather_data.get("pm10"),
                "pm2_5": weather_data.get("pm2_5")
            },
            "recommendations": recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Recommend error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-status/{user_identifier}")
async def get_smart_status(
    user_identifier: str,
    appliance_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    가전 스마트 상태 조회
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        statuses = appliance_control_service.get_appliance_status(
            db=db,
            user_id=str(user_uuid),
            appliance_type=appliance_type
        )
        return {"user_id": user_identifier, "appliances": statuses}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-history/{user_identifier}")
async def get_smart_history(
    user_identifier: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    가전 제어 히스토리
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        history = appliance_control_service.get_command_history(
            db=db,
            user_id=str(user_uuid),
            limit=limit
        )
        return {"user_id": user_identifier, "history": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ History error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-rules/{user_identifier}")
async def setup_default_rules(
    user_identifier: str,
    db: Session = Depends(get_db)
):
    """
    사용자를 위한 기본 가전 규칙 생성
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        appliance_rule_engine.create_default_rules(db, str(user_uuid))
        return {
            "status": "ok",
            "message": "Default rules created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Setup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/rules/{user_identifier}")
async def modify_appliance_rule(
    user_identifier: str,
    request: RuleModifyRequest,
    db: Session = Depends(get_db)
):
    """
    가전 자동 작동 조건 수정 API
    user_identifier: 사용자 email 또는 UUID

    사용 예시:
    1. 제습기 자동 작동 끄기: operation="disable", appliance_type="제습기"
    2. 에어컨 임계값 수정: operation="modify_threshold", appliance_type="에어컨", new_threshold={"temp_threshold": 26}
    3. 제습기 다시 켜기: operation="enable", appliance_type="제습기"
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        # fatigue_level이 없으면 모든 레벨에 적용
        if request.fatigue_level:
            rules = db.query(ApplianceConditionRule).filter(
                ApplianceConditionRule.user_id == user_uuid,
                ApplianceConditionRule.appliance_type == request.appliance_type,
                ApplianceConditionRule.fatigue_level == request.fatigue_level
            ).all()
        else:
            rules = db.query(ApplianceConditionRule).filter(
                ApplianceConditionRule.user_id == user_uuid,
                ApplianceConditionRule.appliance_type == request.appliance_type
            ).all()

        if not rules:
            raise HTTPException(
                status_code=404,
                detail=f"No rules found for {request.appliance_type}"
            )

        # Operation에 따라 처리
        if request.operation == "enable":
            for rule in rules:
                rule.is_enabled = True
            db.commit()
            logger.info(f"✅ Enabled {len(rules)} rules for {request.appliance_type}")
            return {
                "status": "ok",
                "message": f"{request.appliance_type} 자동 작동이 활성화되었습니다",
                "updated_count": len(rules)
            }

        elif request.operation == "disable":
            for rule in rules:
                rule.is_enabled = False
            db.commit()
            logger.info(f"✅ Disabled {len(rules)} rules for {request.appliance_type}")
            return {
                "status": "ok",
                "message": f"{request.appliance_type} 자동 작동이 비활성화되었습니다",
                "updated_count": len(rules)
            }

        elif request.operation == "modify_threshold":
            if not request.new_threshold:
                raise HTTPException(
                    status_code=400,
                    detail="new_threshold is required for modify_threshold operation"
                )

            for rule in rules:
                # 기존 condition_json에 새로운 임계값 병합
                updated_condition = {**rule.condition_json, **request.new_threshold}
                rule.condition_json = updated_condition

            db.commit()
            logger.info(f"✅ Modified threshold for {len(rules)} rules: {request.new_threshold}")
            return {
                "status": "ok",
                "message": f"{request.appliance_type} 작동 조건이 수정되었습니다",
                "updated_count": len(rules),
                "new_threshold": request.new_threshold
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown operation: {request.operation}. Use enable/disable/modify_threshold"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Rule modification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{user_identifier}")
async def get_appliance_rules(
    user_identifier: str,
    appliance_type: Optional[str] = None,
    fatigue_level: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    사용자의 가전 규칙 조회
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        query = db.query(ApplianceConditionRule).filter(
            ApplianceConditionRule.user_id == user_uuid
        )

        if appliance_type:
            query = query.filter(ApplianceConditionRule.appliance_type == appliance_type)

        if fatigue_level:
            query = query.filter(ApplianceConditionRule.fatigue_level == fatigue_level)

        rules = query.all()

        return {
            "user_id": user_identifier,
            "rules": [
                {
                    "id": str(rule.id),
                    "appliance_type": rule.appliance_type,
                    "fatigue_level": rule.fatigue_level,
                    "condition": rule.condition_json,
                    "action": rule.action,
                    "settings": rule.settings_json,
                    "is_enabled": rule.is_enabled,
                    "priority": rule.priority
                }
                for rule in rules
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get rules error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
