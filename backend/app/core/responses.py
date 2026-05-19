from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field
from app.core.pagination import PageMeta

T = TypeVar("T")

class ResponseEnvelope(BaseModel, Generic[T]):
    data: T
    meta: dict[str, Any] = Field(default_factory=dict)

class PaginatedResponseEnvelope(ResponseEnvelope[T], Generic[T]):
    meta: PageMeta

def success_response(data: T, meta: dict[str, Any] | None = None) -> ResponseEnvelope[T]:
    return ResponseEnvelope[T](data=data, meta=meta or {})

def paginated_response(data: Any, meta: PageMeta) -> dict[str, Any]:
    return PaginatedResponseEnvelope[Any](data=data, meta=meta).model_dump(mode="json")
