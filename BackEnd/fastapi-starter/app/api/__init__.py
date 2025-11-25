from fastapi import APIRouter

router = APIRouter()

# Import your API routes here
from . import users, tracking, characters, appliance
from . import sendbird_webhook, location, voice

router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(tracking.router)
router.include_router(characters.router, prefix="/characters", tags=["characters"])
router.include_router(appliance.router, prefix="/appliances", tags=["appliances"])

# Sendbird 및 음성 관련 라우터
router.include_router(sendbird_webhook.router)
router.include_router(location.router)
router.include_router(voice.router)