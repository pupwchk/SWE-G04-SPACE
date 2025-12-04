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

            # 4. 가장 최근 생성된 페르소나 조회 (Supabase)
            persona_name = "AI 어시스턴트"  # 기본값
            persona_id = None  # Supabase 페르소나 ID
            sendbird_user_id = None  # Sendbird에서 사용할 user_id (Supabase UUID)

            try:
                from app.models.user import User
                from app.services.supabase_service import supabase_persona_service

                # 4-1. 서버 DB에서 user_id로 email 조회
                user = db.query(User).filter(User.id == user_id).first()

                if not user or not user.email:
                    logger.warning(f"⚠️ User {user_id} not found or has no email")
                    raise Exception("User email not found")

                user_email = user.email
                logger.info(f"📧 User email: {user_email}")

                # 4-2. email로 Supabase UUID 조회 (Sendbird user_id로 사용)
                sendbird_user_id = supabase_persona_service.get_supabase_user_id_by_email(user_email)
                if sendbird_user_id:
                    logger.info(f"✅ Sendbird user_id (Supabase UUID): {sendbird_user_id}")
                else:
                    logger.warning(f"⚠️ Failed to get Supabase UUID for {user_email}, using DB UUID as fallback")
                    sendbird_user_id = user_id  # Fallback to DB UUID

                # 4-3. Supabase에서 email로 가장 최근 페르소나 조회
                latest_persona = supabase_persona_service.get_latest_persona_by_email(user_email)

                if latest_persona:
                    persona_id = latest_persona.get("id")
                    persona_name = latest_persona.get("nickname", "AI 어시스턴트")
                    logger.info(f"👤 Latest persona from Supabase: {persona_name} (id: {persona_id})")
                else:
                    logger.info(f"ℹ️ No personas found in Supabase for {user_email}, using default")

            except Exception as e:
                # Supabase 조회 실패 시 기본값 사용
                logger.warning(f"⚠️ Failed to get latest persona from Supabase: {str(e)}, using default: {persona_name}")
                # sendbird_user_id가 없으면 DB UUID 사용
                if not sendbird_user_id:
                    sendbird_user_id = user_id

            # 5. Sendbird 채팅으로 승인 요청 메시지 전송
            try:
                # 5-1. Supabase persona_channels에서 기존 채널 URL 조회
                channel_url = None
                if persona_id and user_email:
                    channel_url = supabase_persona_service.get_channel_url_by_email_and_persona(
                        email=user_email,
                        persona_id=persona_id
                    )

                # 5-2. 채널 URL이 없으면 새로 생성 (fallback)
                if not channel_url:
                    logger.warning(f"⚠️ No existing channel found, creating new one")
                    channel_data = await chat_client.create_channel(
                        channel_url=None,  # 자동 생성
                        user_ids=[sendbird_user_id, SendbirdConfig.AI_USER_ID],  # Sendbird는 Supabase UUID 사용
                        name=f"Chat with {persona_name}"
                    )
                    channel_url = channel_data.get("channel_url")

                logger.info(f"📱 Using channel: {channel_url} (persona: {persona_name})")

                # ChatSession에 기록 저장 (선택적, 추후 분석용)
                if persona_id:
                    try:
                        from app.models.chat import ChatSession
                        from datetime import datetime, timezone

                        # 기존 세션이 있으면 업데이트, 없으면 생성
                        existing_session = db.query(ChatSession)\
                            .filter(
                                ChatSession.user_id == user_id,
                                ChatSession.persona_id == persona_id
                            )\
                            .first()

                        if existing_session:
                            # 기존 세션 업데이트
                            existing_session.sendbird_channel_url = channel_url
                            existing_session.persona_nickname = persona_name
                            existing_session.last_message_at = datetime.now(timezone.utc)
                            logger.info(f"💾 Updated ChatSession")
                        else:
                            # 새 세션 생성
                            new_session = ChatSession(
                                user_id=user_id,
                                persona_id=persona_id,
                                persona_nickname=persona_name,
                                sendbird_channel_url=channel_url,
                                is_active=True
                            )
                            db.add(new_session)
                            logger.info(f"💾 Created new ChatSession")

                        db.commit()
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to save ChatSession: {str(e)}")
                        db.rollback()

                # 승인 요청 메시지 생성 (LLM으로 자연스럽게)
                if appliances_to_control:
                    # LLM으로 자연스러운 메시지 생성
                    try:
                        # 페르소나 정보 준비
                        persona_info = None
                        if persona_name != "AI 어시스턴트":
                            persona_info = {"nickname": persona_name}

                        # LLM 서비스로 자연스러운 메시지 생성
                        message = await llm_service.generate_proactive_appliance_message(
                            appliances=appliances_to_control,
                            weather=weather_data,
                            fatigue_level=fatigue_level,
                            persona=persona_info
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to generate LLM message, using fallback: {str(e)}")
                        # Fallback: 간단한 형식
                        appliance_names = [a["appliance_type"] for a in appliances_to_control]
                        message = f"집에 거의 도착하셨네요! 현재 날씨와 피로도를 고려해서 {', '.join(appliance_names)}을(를) 켜드릴까요?"
                else:
                    # 가전이 없을 때도 LLM으로 자연스러운 메시지 생성
                    try:
                        persona_info = None
                        if persona_name != "AI 어시스턴트":
                            persona_info = {"nickname": persona_name}

                        message = await llm_service.generate_proactive_no_appliance_message(
                            weather=weather_data,
                            fatigue_level=fatigue_level,
                            persona=persona_info
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to generate LLM message, using fallback: {str(e)}")
                        message = "집에 거의 도착하셨네요! 현재 날씨와 피로도 상태가 괜찮아 보여요."

                await chat_client.send_message(
                    channel_url=channel_url,
                    message=message,
                    user_id=SendbirdConfig.AI_USER_ID
                )
                logger.info(f"💬 Approval request sent to {channel_url}")

                # AI 메시지를 메모리에 저장 (대화 컨텍스트 유지)
                # 메모리 키는 Sendbird user_id (Supabase UUID) 사용
                memory_service.add_message(sendbird_user_id, "assistant", message)
                logger.info(f"💾 AI message saved to memory for Sendbird user {sendbird_user_id}")

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
