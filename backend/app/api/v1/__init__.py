from fastapi import APIRouter

from app.api.v1 import (
    auth,
    bestiary,
    consumables,
    crafting,
    hero,
    inventory,
    leaderboard,
    materials,
    runes,
    shop,
    users,
    veil,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(hero.router)
api_router.include_router(veil.router)
api_router.include_router(inventory.router)
api_router.include_router(materials.router)
api_router.include_router(runes.router)
api_router.include_router(crafting.router)
api_router.include_router(consumables.router)
api_router.include_router(bestiary.router)
api_router.include_router(leaderboard.router)
api_router.include_router(shop.router)
