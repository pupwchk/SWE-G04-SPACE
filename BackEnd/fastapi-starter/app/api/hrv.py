"""
HRV API 엔드포인트
iOS에서 HealthKit HRV 데이터를 전송받음
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.services.hrv_service import hrv_service
from app.utils.user_utils import get_user_uuid_by_identifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


class HRVSyncRequest(BaseModel):
    """HRV 동기화 요청"""
    user_id: str = Field(..., description="사용자 ID (email 또는 UUID)")
    hrv_value: float = Field(..., description="HRV 값 (ms)", gt=0)
    measured_at: datetime = Field(..., description="측정 시각 (ISO 8601)")


class HRVSyncResponse(BaseModel):
    """HRV 동기화 응답"""
    success: bool
    hrv_value: float
    fatigue_level: int
    fatigue_label: str
    measured_at: datetime
    synced_at: datetime


class FatigueStatusResponse(BaseModel):
    """피로도 상태 응답"""
    user_id: str
    current_fatigue_level: int | None
    fatigue_label: str | None
    latest_hrv_value: float | None
    measured_at: datetime | None
    average_fatigue_7days: float | None


@router.post("/hrv", response_model=HRVSyncResponse)
async def sync_hrv(
    request: HRVSyncRequest,
    db: Session = Depends(get_db)
):
    """
    HealthKit에서 HRV 데이터 동기화
    request.user_id: 사용자 email 또는 UUID

    iOS 앱에서 주기적으로 호출:
    - 새 HRV 값이 생성되면 즉시 전송
    - 또는 30분마다 최신 값 조회 후 전송
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, request.user_id)

        hrv_log = hrv_service.sync_hrv_from_healthkit(
            db=db,
            user_id=user_uuid,
            hrv_value=request.hrv_value,
            measured_at=request.measured_at
        )

        fatigue_labels = {
            1: "좋음",
            2: "보통",
            3: "나쁨",
            4: "매우 나쁨"
        }

        return HRVSyncResponse(
            success=True,
            hrv_value=hrv_log.hrv_value,
            fatigue_level=hrv_log.fatigue_level,
            fatigue_label=fatigue_labels[hrv_log.fatigue_level],
            measured_at=hrv_log.measured_at,
            synced_at=hrv_log.synced_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ HRV sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"HRV 동기화 실패: {str(e)}")


@router.get("/fatigue/{user_identifier}", response_model=FatigueStatusResponse)
async def get_fatigue_status(
    user_identifier: str,
    db: Session = Depends(get_db)
):
    """
    사용자의 현재 피로도 상태 조회
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        # 최신 HRV 로그
        latest_log = hrv_service.get_latest_hrv_log(db, user_uuid)

        # 최근 7일 평균 피로도
        avg_fatigue = hrv_service.calculate_average_fatigue(db, user_uuid, days=7)

        fatigue_labels = {
            1: "좋음",
            2: "보통",
            3: "나쁨",
            4: "매우 나쁨"
        }

        if latest_log:
            return FatigueStatusResponse(
                user_id=user_identifier,
                current_fatigue_level=latest_log.fatigue_level,
                fatigue_label=fatigue_labels[latest_log.fatigue_level],
                latest_hrv_value=latest_log.hrv_value,
                measured_at=latest_log.measured_at,
                average_fatigue_7days=avg_fatigue
            )
        else:
            return FatigueStatusResponse(
                user_id=user_identifier,
                current_fatigue_level=None,
                fatigue_label=None,
                latest_hrv_value=None,
                measured_at=None,
                average_fatigue_7days=None
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fatigue status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"피로도 조회 실패: {str(e)}")
