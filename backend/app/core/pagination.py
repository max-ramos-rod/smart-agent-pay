from math import ceil

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    has_next: bool
    total_pages: int


class PaginationMetaBuilder:
    @staticmethod
    def build(total: int, params: PaginationParams) -> PageMeta:
        total_pages = ceil(total / params.page_size) if total else 0
        has_next = params.page * params.page_size < total
        return PageMeta(
            total=total,
            page=params.page,
            page_size=params.page_size,
            has_next=has_next,
            total_pages=total_pages,
        )
