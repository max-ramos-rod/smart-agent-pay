import logging

logger = logging.getLogger("agent")

def log_agent_execution(
    user_id: int,
    status: str,
    metadata: dict | None = None,  # 🔥 adicionar
):
    log = {
        "user_id": user_id,
        "status": status,
        "metadata": metadata or {},
    }

    print(f"📜 LOG: {log}")