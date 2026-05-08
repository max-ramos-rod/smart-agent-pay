from fastapi import APIRouter

from app.api.v1.routers.agents import router as agent_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.sessions import router as session_router
from app.api.v1.routers.strategies import router as strategy_router
from app.api.v1.routers.wallets import router as wallet_router
from app.api.v1.routers.users import router as users_router
from app.api.v1.routers.executions import router as executions_router
from app.api.v1.routers.demo import router as demo_router
from app.api.v1.routers.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(agent_router)
api_router.include_router(auth_router)
api_router.include_router(session_router)
api_router.include_router(strategy_router)
api_router.include_router(wallet_router)
api_router.include_router(users_router)
api_router.include_router(executions_router)
api_router.include_router(demo_router)