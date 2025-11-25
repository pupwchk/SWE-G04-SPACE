"""
Location API
GPS 위치 수신 및 Geofence 처리
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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
    background_tasks: BackgroundTasks
):
    """
    위치 업데이트 수신
    
    iOS 앱에서 주기적으로 호출
    """
    try:
        logger.info(f"📍 Location update from {location.user_id}: ({location.latitude}, {location.longitude})")
        
        # Geofence 확인
        result = geofence_service.check_geofence_trigger(
            user_id=location.user_id,
            latitude=location.latitude,
            longitude=location.longitude,
            accuracy=location.accuracy
        )
        
        # Geofence 진입 시 자동 전화 트리거
        if result["triggered"] and result["event"] == "ENTER":
            background_tasks.add_task(
                trigger_auto_call,
                location.user_id,
                result["distance"]
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


async def trigger_auto_call(user_id: str, distance: float):
    """자동 전화 트리거"""
    try:
        logger.info(f"📞 Triggering auto-call for {user_id} (distance: {distance:.1f}m)")
        
        # 채널 URL 생성
        channel_url = SendbirdConfig.get_channel_url(user_id)
        
        # LLM으로 Geofence 메시지 생성
        long_term = memory_service.get_long_term_memory(user_id)
        
        response = await llm_service.generate_geofence_trigger(
            user_id=user_id,
            distance=distance,
            context={
                "time": datetime.now().strftime("%H:%M"),
                "user_preferences": long_term
            }
        )
        
        message_to_user = response.get("message_to_user", "집에 거의 도착하셨어요. 잠시 후 전화 드릴게요.")
        
        # 채팅 메시지 먼저 전송
        try:
            await chat_client.send_message(
                channel_url=channel_url,
                message=message_to_user
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send chat message: {str(e)}")
        
        # 전화 발신
        await calls_client.make_call(
            caller_id=SendbirdConfig.AI_USER_ID,
            callee_id=user_id,
            call_type="voice"
        )
        
        logger.info(f"✅ Auto-call triggered successfully for {user_id}")
    
    except Exception as e:
        logger.error(f"❌ Auto-call trigger error: {str(e)}")


@router.get("/status/{user_id}")
async def get_location_status(user_id: str):
    """사용자 위치 상태 조회"""
    try:
        state = geofence_service.get_user_state(user_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="User location not found")
        
        return {
            "user_id": user_id,
            "state": state
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get location status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/geofence/config")
async def configure_geofence(config: GeofenceConfig):
    """Geofence 설정"""
    try:
        geofence_service.set_home_location(
            latitude=config.latitude,
            longitude=config.longitude
        )
        
        geofence_service.set_geofence_radius(config.radius_meters)
        
        return {
            "status": "ok",
            "message": "Geofence configured successfully",
            "config": {
                "latitude": config.latitude,
                "longitude": config.longitude,
                "radius_meters": config.radius_meters
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Configure geofence error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geofence/config")
async def get_geofence_config():
    """현재 Geofence 설정 조회"""
    return {
        "latitude": geofence_service.home_lat,
        "longitude": geofence_service.home_lng,
        "radius_meters": geofence_service.radius
    }
