import secrets
from datetime import datetime, timedelta


class AgentService:
    async def create_session(self, user_id: int):
        session_key = secrets.token_hex(32)

        return {
            "user_id": user_id,
            "session_key": session_key,
            "max_amount": 100,
            "expires_at": datetime.utcnow() + timedelta(hours=1),
        }