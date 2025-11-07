from fastapi import APIRouter

router = APIRouter(prefix="/api")

# Import your API routes here
from . import users, tracking

router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(tracking.router, prefix="/api")