"""
날씨 API 엔드포인트
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from app.config.db import get_db
from app.services.weather_service import weather_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/weather", tags=["Weather"])


class WeatherResponse(BaseModel):
    """날씨 정보 응답"""
    temperature: float | None = Field(None, description="기온 (°C)")
    humidity: float | None = Field(None, description="습도 (%)")
    precipitation: float | None = Field(None, description="1시간 강수량 (mm)")
    wind_speed: float | None = Field(None, description="풍속 (m/s)")
    pm10: float | None = Field(None, description="미세먼지 PM10 (㎍/㎥)")
    pm2_5: float | None = Field(None, description="초미세먼지 PM2.5 (㎍/㎥)")
    cached: bool = Field(..., description="캐시 사용 여부")
    fetched_at: datetime = Field(..., description="조회 시각")


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    latitude: float = Query(..., description="위도"),
    longitude: float = Query(..., description="경도"),
    sido: str = Query("서울", description="시도 이름 (미세먼지 조회용)"),
    db: Session = Depends(get_db)
):
    """
    현재 날씨 조회 (캐싱됨, 10분 유효)

    기상청 초단기실황 + 미세먼지 API 통합

    Example:
        GET /api/weather/current?latitude=37.5665&longitude=126.9780&sido=서울
    """
    try:
        weather_data = await weather_service.get_combined_weather(
            db=db,
            latitude=latitude,
            longitude=longitude,
            sido_name=sido
        )

        return WeatherResponse(**weather_data)

    except Exception as e:
        logger.error(f"❌ Weather fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"날씨 조회 실패: {str(e)}")


@router.get("/home/{user_identifier}", response_model=WeatherResponse)
async def get_home_weather(
    user_identifier: str,
    db: Session = Depends(get_db)
):
    """
    사용자의 집 위치 기반 날씨 조회
    user_identifier: 사용자 email 또는 서버 DB UUID

    UserLocation 테이블에서 집 좌표를 조회하여 날씨 정보 반환
    """
    try:
        from app.models.location import UserLocation
        from app.utils.user_utils import get_user_uuid_by_identifier

        # user_identifier(email 또는 UUID)를 서버 DB UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        # 사용자 집 위치 조회 (서버 DB UUID 사용)
        location = db.query(UserLocation)\
            .filter(UserLocation.user_id == user_uuid)\
            .first()

        if not location or not location.home_latitude or not location.home_longitude:
            raise HTTPException(
                status_code=404,
                detail="사용자의 집 위치가 설정되지 않았습니다"
            )

        weather_data = await weather_service.get_combined_weather(
            db=db,
            latitude=location.home_latitude,
            longitude=location.home_longitude,
            sido_name="서울"  # TODO: 위도경도로부터 시도 이름 추출
        )

        return WeatherResponse(**weather_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Home weather error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"집 날씨 조회 실패: {str(e)}")
