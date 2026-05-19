import secrets
from fastapi import APIRouter

from app.services.agent.service import AgentService

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("")
async def create_session():
    service = AgentService()
    return await service.create_session(user_id=1)