from fastapi import APIRouter

router = APIRouter(prefix="/api")

# Import your API routes here
from . import users, tracking, stress, fatigue

router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(tracking.router, prefix="/api")
router.include_router(stress.router)
router.include_router(fatigue.router)