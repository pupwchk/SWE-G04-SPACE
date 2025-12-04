from fastapi import APIRouter

router = APIRouter()

# Import your API routes here
from . import users, tracking, characters, appliance
from . import sendbird_webhook, sendbird_auth, location, voice, hrv, weather, voice_realtime, chat

router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(tracking.router)
router.include_router(characters.router, prefix="/characters", tags=["characters"])
router.include_router(appliance.router, prefix="/appliances", tags=["appliances"])

# Sendbird 관련 라우터
router.include_router(sendbird_webhook.router)
router.include_router(sendbird_auth.router)

# 음성 및 위치 관련 라우터
router.include_router(location.router)
router.include_router(voice.router)
router.include_router(voice_realtime.router, prefix="/voice", tags=["voice-realtime"])

# HRV 관련 라우터
router.include_router(hrv.router)

# 날씨 관련 라우터
router.include_router(weather.router)

# 채팅 관련 라우터 (시나리오 2)
router.include_router(chat.router)