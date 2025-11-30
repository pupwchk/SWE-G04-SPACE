"""
Location API
GPS 위치 수신 및 Geofence 처리
"""
import os
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.services.geofence_service import geofence_service
from app.services.llm_service import llm_service, memory_service
from app.services.sendbird_client import SendbirdChatClient, SendbirdCallsClient
from app.config.sendbird import SendbirdConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/location", tags=["Location"])

# 클라이언트
chat_client = SendbirdChatClient()
calls_client = SendbirdCallsClient()


class LocationUpdate(BaseModel):
    """위치 업데이트 요청"""
    user_id: str = Field(..., description="사용자 ID")
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    accuracy: Optional[float] = Field(None, description="GPS 정확도 (미터)")
    timestamp: Optional[float] = Field(None, description="타임스탬프")


class GeofenceConfig(BaseModel):
    """Geofence 설정"""
    latitude: float = Field(..., description="집 위도")
    longitude: float = Field(..., description="집 경도")
    radius_meters: float = Field(100.0, description="반경 (미터)")


@router.post("/update")
async def update_location(
    location: LocationUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    위치 업데이트 수신 (10분 간격 추천)

    iOS 앱에서 주기적으로 호출
    - Geofence 진입/이탈 감지
    - Approaching 패턴 감지 (지속적으로 가까워지는 경우)
    """
    try:
        logger.info(f"📍 Location update from {location.user_id}: ({location.latitude}, {location.longitude})")

        # Geofence 확인 (DB에 기록됨)
        result = geofence_service.check_geofence_trigger(
            db=db,
            user_id=location.user_id,
            latitude=location.latitude,
            longitude=location.longitude,
            accuracy=location.accuracy
        )

        # APPROACHING_DETECTED 또는 ENTER 시 시나리오 1 트리거
        if result["triggered"] and result["event"] in ["APPROACHING_DETECTED", "ENTER"]:
            background_tasks.add_task(
                trigger_auto_call,
                location.user_id,
                result["distance"],
                result["event"]
            )

            return {
                "status": "ok",
                "action": "AUTO_CALL",
                "message": "집에 거의 도착하셨어요. 잠시 후 전화 드릴게요.",
                "geofence": result
            }

        return {
            "status": "ok",
            "action": "NONE",
            "geofence": result
        }

    except Exception as e:
        logger.error(f"❌ Location update error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def trigger_auto_call(user_id: str, distance: float, event_type: str):
    """
    자동 전화 트리거 (시나리오 1 - Proactive)

    흐름:
    1. HRV 피로도 조회
    2. 날씨 데이터 조회
    3. Rule Engine으로 가전 제어 결정
    4. 가전 제어 실행
    5. Sendbird 채팅 메시지
    6. Sendbird 음성 통화

    Args:
        user_id: 사용자 ID
        distance: 집까지 거리
        event_type: 이벤트 타입 (APPROACHING_DETECTED 또는 ENTER)
    """
    try:
        from app.config.db import SessionLocal
        from app.services.hrv_service import hrv_service
        from app.services.weather_service import weather_service
        from app.services.appliance_rule_engine import appliance_rule_engine
        from app.services.appliance_control_service import appliance_control_service
        from app.models.location import UserLocation

        logger.info(f"📞 [Scenario 1] Triggering for {user_id} (event: {event_type}, distance: {distance:.1f}m)")

        db = SessionLocal()

        try:
            # 1. HRV 피로도 조회
            fatigue_level = hrv_service.get_latest_fatigue_level(db, user_id)
            if fatigue_level is None:
                fatigue_level = 2  # 기본값
                logger.warning(f"⚠️ No HRV data for {user_id}, using default fatigue level 2")

            logger.info(f"💓 Fatigue level: {fatigue_level}")

            # 2. 사용자 집 위치 조회
            user_location = db.query(UserLocation)\
                .filter(UserLocation.user_id == user_id)\
                .first()

            if not user_location or not user_location.home_latitude:
                logger.error(f"❌ No home location for {user_id}")
                return

            # 3. 날씨 데이터 조회
            weather_data = await weather_service.get_combined_weather(
                db=db,
                latitude=user_location.home_latitude,
                longitude=user_location.home_longitude,
                sido_name=os.getenv("DEFAULT_SIDO_NAME", "서울")
            )

            logger.info(f"🌤️ Weather: {weather_data.get('temperature')}°C, {weather_data.get('humidity')}%")

            # 4. Rule Engine으로 가전 제어 결정
            appliances_to_control = appliance_rule_engine.get_appliances_to_control(
                db=db,
                user_id=user_id,
                weather_data=weather_data,
                fatigue_level=fatigue_level
            )

            logger.info(f"🎛️ Appliances to control: {len(appliances_to_control)}")

            # 5. 가전 제어 실행
            if appliances_to_control:
                control_results = appliance_control_service.execute_multiple_commands(
                    db=db,
                    user_id=user_id,
                    commands=appliances_to_control,
                    triggered_by="scenario1"
                )

                success_count = sum(1 for r in control_results if r.get("success"))
                logger.info(f"✅ Controlled {success_count}/{len(appliances_to_control)} appliances")

            # 6. Sendbird 채팅 메시지
            channel_url = SendbirdConfig.get_channel_url(user_id)

            # 메시지 생성
            appliance_names = [a["appliance_type"] for a in appliances_to_control]
            if appliances_to_control:
                message = f"집에 거의 도착하셨네요! 피로도를 고려해서 {', '.join(appliance_names)}을(를) 켜드렸어요. 잠시 후 전화로 자세히 안내해드릴게요."
            else:
                message = "집에 거의 도착하셨네요! 현재 날씨와 피로도 상태가 괜찮아서 따로 켤 가전은 없어요. 잠시 후 전화드릴게요."

            try:
                await chat_client.send_message(
                    channel_url=channel_url,
                    message=message
                )
                logger.info(f"💬 Chat message sent")
            except Exception as e:
                logger.warning(f"⚠️ Failed to send chat: {str(e)}")

            # 7. Sendbird 음성 통화
            try:
                await calls_client.make_call(
                    caller_id=SendbirdConfig.AI_USER_ID,
                    callee_id=user_id,
                    call_type="voice"
                )
                logger.info(f"📞 Call initiated")
            except Exception as e:
                logger.warning(f"⚠️ Failed to make call: {str(e)}")

            logger.info(f"✅ [Scenario 1] Completed for {user_id}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ [Scenario 1] Error: {str(e)}", exc_info=True)


@router.get("/status/{user_id}")
async def get_location_status(user_id: str, db: Session = Depends(get_db)):
    """
    사용자 위치 상태 조회

    최근 추적 기록과 이벤트 히스토리 반환
    """
    try:
        # 사용자 위치 설정
        location = geofence_service.get_user_location_settings(db, user_id)

        # 최근 추적 기록
        from app.models.location import GeofenceTracking
        from sqlalchemy import desc

        latest_tracking = db.query(GeofenceTracking)\
            .filter(GeofenceTracking.user_id == user_id)\
            .order_by(desc(GeofenceTracking.tracked_at))\
            .first()

        # 최근 이벤트
        recent_events = geofence_service.get_recent_events(db, user_id, hours=24)

        if not latest_tracking:
            raise HTTPException(status_code=404, detail="No location data found for this user")

        return {
            "user_id": user_id,
            "home_location": {
                "latitude": location.home_latitude,
                "longitude": location.home_longitude,
                "geofence_radius_meters": location.geofence_radius_meters
            },
            "latest_tracking": {
                "distance_from_home": latest_tracking.distance_from_home,
                "approaching": latest_tracking.approaching,
                "tracked_at": latest_tracking.tracked_at.isoformat(),
                "latitude": latest_tracking.latitude,
                "longitude": latest_tracking.longitude
            },
            "recent_events": [
                {
                    "event_type": event.event_type,
                    "distance_from_home": event.distance_from_home,
                    "created_at": event.created_at.isoformat()
                }
                for event in recent_events
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get location status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/geofence/config/{user_id}")
async def configure_geofence(
    user_id: str,
    config: GeofenceConfig,
    db: Session = Depends(get_db)
):
    """
    사용자별 Geofence 설정 (집 위치 및 반경)
    """
    try:
        location = geofence_service.update_home_location(
            db=db,
            user_id=user_id,
            latitude=config.latitude,
            longitude=config.longitude,
            radius_meters=config.radius_meters
        )

        return {
            "status": "ok",
            "message": "Geofence configured successfully",
            "config": {
                "user_id": user_id,
                "latitude": location.home_latitude,
                "longitude": location.home_longitude,
                "radius_meters": location.geofence_radius_meters
            }
        }

    except Exception as e:
        logger.error(f"❌ Configure geofence error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geofence/config/{user_id}")
async def get_geofence_config(user_id: str, db: Session = Depends(get_db)):
    """
    사용자 Geofence 설정 조회
    """
    try:
        location = geofence_service.get_user_location_settings(db, user_id)

        return {
            "user_id": user_id,
            "latitude": location.home_latitude,
            "longitude": location.home_longitude,
            "radius_meters": location.geofence_radius_meters
        }

    except Exception as e:
        logger.error(f"❌ Get geofence config error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
