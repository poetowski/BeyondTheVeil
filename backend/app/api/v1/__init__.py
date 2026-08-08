from fastapi import APIRouter

from app.api.v1 import auth, bestiary, inventory, materials, users, veil

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(veil.router)
api_router.include_router(inventory.router)
api_router.include_router(materials.router)
api_router.include_router(bestiary.router)
