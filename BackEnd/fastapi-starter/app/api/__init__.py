from fastapi import APIRouter

router = APIRouter(prefix="/api")

# Import your API routes here
from . import users, tracking, characters, appliance

router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(tracking.router, prefix="/api")
router.include_router(characters.router, prefix="/characters", tags=["characters"])
router.include_router(appliance.router, prefix="/appliances", tags=["appliances"])