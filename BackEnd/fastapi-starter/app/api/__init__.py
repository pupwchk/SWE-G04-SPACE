<<<<<<< HEAD
from fastapi import APIRouter

router = APIRouter(prefix="/api")

# Import your API routes here
from . import users

router.include_router(users.router, prefix="/users", tags=["users"])
=======
from fastapi import APIRouter

router = APIRouter(prefix="/api")

# Import your API routes here
from . import users

router.include_router(users.router, prefix="/users", tags=["users"])
>>>>>>> bcd457ea32467cf8181e23873afa32c1735331de
