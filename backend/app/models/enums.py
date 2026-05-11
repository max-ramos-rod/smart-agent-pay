from enum import Enum

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    AWAITING_SIGNATURE = "awaiting_signature"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"