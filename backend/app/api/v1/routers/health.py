from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def healthcheck() -> dict[str, dict[str, str]]:
    return {
        "data": {
            "status": "ok",
            "service": "smart-agent-pay",
        },
        "meta": {},
    }
