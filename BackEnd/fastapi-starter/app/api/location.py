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
from app.utils.user_utils import get_user_uuid_by_identifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/location", tags=["Location"])

# 클라이언트
chat_client = SendbirdChatClient()
calls_client = SendbirdCallsClient()


class LocationUpdate(BaseModel):
    """위치 업데이트 요청"""
    user_id: str = Field(..., description="사용자 ID (email 또는 UUID)")
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
    location.user_id: 사용자 email 또는 UUID

    iOS 앱에서 주기적으로 호출
    - Geofence 진입/이탈 감지
    - Approaching 패턴 감지 (지속적으로 가까워지는 경우)
    """
    try:
        logger.info(f"📍 Location update from {location.user_id}: ({location.latitude}, {location.longitude})")

        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, location.user_id)

        # Geofence 확인 (DB에 기록됨)
        result = geofence_service.check_geofence_trigger(
            db=db,
            user_id=str(user_uuid),
            latitude=location.latitude,
            longitude=location.longitude,
            accuracy=location.accuracy
        )

        # APPROACHING_DETECTED 또는 ENTER 시 시나리오 1 트리거
        if result["triggered"] and result["event"] in ["APPROACHING_DETECTED", "ENTER"]:
            background_tasks.add_task(
                trigger_auto_notification,
                str(user_uuid),
                result["distance"],
                result["event"]
            )

            return {
                "status": "ok",
                "action": "AUTO_NOTIFICATION",
                "message": "집에 거의 도착하셨어요. 잠시 후 메시지를 보내드릴게요.",
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


async def trigger_auto_notification(user_id: str, distance: float, event_type: str):
    """
    자동 알림 트리거 (시나리오 1 - Proactive)

    흐름:
    1. HRV 피로도 조회
    2. 날씨 데이터 조회 (서울 기본값)
    3. Rule Engine으로 가전 제어 결정
    4. 가장 최근 대화한 페르소나 조회
    5. Sendbird 채팅으로 승인 요청 메시지 전송

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

        logger.info(f"📞 [Scenario 1] Triggering for {user_id} (event: {event_type}, distance: {distance:.1f}m)")

        db = SessionLocal()

        try:
            # 1. HRV 피로도 조회
            fatigue_level = hrv_service.get_latest_fatigue_level(db, user_id)
            if fatigue_level is None:
                fatigue_level = 2  # 기본값
                logger.warning(f"⚠️ No HRV data for {user_id}, using default fatigue level 2")

            logger.info(f"💓 Fatigue level: {fatigue_level}")

            # 2. 날씨 데이터 조회 (서울 기본값 사용)
            weather_data = await weather_service.get_combined_weather(
                db=db,
                latitude=37.5665,  # 서울 시청 좌표
                longitude=126.9780,
                sido_name=os.getenv("DEFAULT_SIDO_NAME", "서울")
            )

            logger.info(f"🌤️ Weather: {weather_data.get('temperature')}°C, {weather_data.get('humidity')}%")

            # 3. Rule Engine으로 가전 제어 결정
            appliances_to_control = appliance_rule_engine.get_appliances_to_control(
                db=db,
                user_id=user_id,
                weather_data=weather_data,
                fatigue_level=fatigue_level
            )

            logger.info(f"🎛️ Appliances to control: {len(appliances_to_control)}")

            # 4. 가장 최근 대화한 페르소나 조회
            from app.models.chat import ChatSession
            from sqlalchemy import desc

            recent_session = db.query(ChatSession)\
                .filter(
                    ChatSession.user_id == user_id,
                    ChatSession.persona_id.isnot(None)
                )\
                .order_by(desc(ChatSession.last_message_at))\
                .first()

            if recent_session and recent_session.persona_nickname:
                persona_name = recent_session.persona_nickname
                logger.info(f"👤 Using recent persona: {persona_name}")
            else:
                persona_name = "AI 어시스턴트"
                logger.info(f"👤 No recent persona, using default: {persona_name}")

            # 5. Sendbird 채팅으로 승인 요청 메시지 전송
            try:
                channel_data = await chat_client.create_channel(
                    channel_url=None,  # 자동 생성
                    user_ids=[user_id, SendbirdConfig.AI_USER_ID]
                )
                channel_url = channel_data.get("channel_url")

                # 승인 요청 메시지 생성
                if appliances_to_control:
                    # 가전 목록과 설정값을 상세히 설명
                    appliance_details = []
                    for cmd in appliances_to_control:
                        detail = f"- {cmd['appliance_type']}"
                        if cmd.get('settings'):
                            # 주요 설정값만 표시
                            settings_str = ", ".join([f"{k}: {v}" for k, v in list(cmd['settings'].items())[:3]])
                            detail += f" ({settings_str})"
                        appliance_details.append(detail)

                    appliance_list = "\n".join(appliance_details)

                    message = f"""[{persona_name}]

집에 거의 도착하셨네요!

현재 상황:
- 피로도 레벨: {fatigue_level}
- 온도: {weather_data.get('temperature', 'N/A')}°C
- 습도: {weather_data.get('humidity', 'N/A')}%

추천 가전:
{appliance_list}

위 가전을 작동시킬까요?"""
                else:
                    message = f"""[{persona_name}]

집에 거의 도착하셨네요!

현재 상황:
- 피로도 레벨: {fatigue_level}
- 온도: {weather_data.get('temperature', 'N/A')}°C
- 습도: {weather_data.get('humidity', 'N/A')}%

현재 날씨와 피로도 상태가 괜찮아서 따로 켤 가전은 없어요."""

                await chat_client.send_message(
                    channel_url=channel_url,
                    message=message,
                    user_id=SendbirdConfig.AI_USER_ID
                )
                logger.info(f"💬 Approval request sent to {channel_url}")

                # TODO: 사용자 응답 대기 및 승인 시 가전 실행
                # 추후 callback endpoint 구현 필요

            except Exception as e:
                logger.warning(f"⚠️ Failed to send approval request: {str(e)}")

            logger.info(f"✅ [Scenario 1] Completed for {user_id}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ [Scenario 1] Error: {str(e)}", exc_info=True)


@router.get("/status/{user_identifier}")
async def get_location_status(user_identifier: str, db: Session = Depends(get_db)):
    """
    사용자 위치 상태 조회
    user_identifier: 사용자 email 또는 UUID

    최근 추적 기록과 이벤트 히스토리 반환
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        # 사용자 위치 설정
        location = geofence_service.get_user_location_settings(db, str(user_uuid))

        # 최근 추적 기록
        from app.models.location import GeofenceTracking
        from sqlalchemy import desc

        latest_tracking = db.query(GeofenceTracking)\
            .filter(GeofenceTracking.user_id == user_uuid)\
            .order_by(desc(GeofenceTracking.tracked_at))\
            .first()

        # 최근 이벤트
        recent_events = geofence_service.get_recent_events(db, str(user_uuid), hours=24)

        if not latest_tracking:
            raise HTTPException(status_code=404, detail="No location data found for this user")

        return {
            "user_id": user_identifier,
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


@router.post("/geofence/config/{user_identifier}")
async def configure_geofence(
    user_identifier: str,
    config: GeofenceConfig,
    db: Session = Depends(get_db)
):
    """
    사용자별 Geofence 설정 (집 위치 및 반경)
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        location = geofence_service.update_home_location(
            db=db,
            user_id=str(user_uuid),
            latitude=config.latitude,
            longitude=config.longitude,
            radius_meters=config.radius_meters
        )

        return {
            "status": "ok",
            "message": "Geofence configured successfully",
            "config": {
                "user_id": user_identifier,
                "latitude": location.home_latitude,
                "longitude": location.home_longitude,
                "radius_meters": location.geofence_radius_meters
            }
        }

    except Exception as e:
        logger.error(f"❌ Configure geofence error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geofence/config/{user_identifier}")
async def get_geofence_config(user_identifier: str, db: Session = Depends(get_db)):
    """
    사용자 Geofence 설정 조회
    user_identifier: 사용자 email 또는 UUID
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        location = geofence_service.get_user_location_settings(db, str(user_uuid))

        return {
            "user_id": user_identifier,
            "latitude": location.home_latitude,
            "longitude": location.home_longitude,
            "radius_meters": location.geofence_radius_meters
        }

    except Exception as e:
        logger.error(f"❌ Get geofence config error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/demo/{user_identifier}")
async def trigger_demo_notification(
    user_identifier: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    시연용 API - 수동으로 Geofence 이벤트 트리거

    user_identifier: 사용자 email 또는 UUID

    실제 위치 이동 없이 AI 자동 알림을 테스트할 수 있습니다.
    """
    try:
        logger.info(f"🎬 [DEMO] Manual trigger for {user_identifier}")

        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        # 백그라운드에서 자동 알림 트리거 (거리 50m, ENTER 이벤트로 시뮬레이션)
        background_tasks.add_task(
            trigger_auto_notification,
            str(user_uuid),
            50.0,  # 집에서 50m 거리로 가정
            "ENTER"
        )

        return {
            "status": "ok",
            "message": "시연용 자동 알림이 트리거되었습니다. 잠시 후 메시지가 전송됩니다.",
            "user_id": user_identifier
        }

    except Exception as e:
        logger.error(f"❌ Demo trigger error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
