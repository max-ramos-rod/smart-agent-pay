from __future__ import annotations

from abc import ABC
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select

from app.core.pagination import PaginationParams
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
EntityT = TypeVar("EntityT")


class SQLAlchemyRepository(Generic[ModelT], ABC):
    model: type[ModelT]

    async def list(self, db: AsyncSession, *, order_by: Any | None = None,) -> list[ModelT]:
        statement = select(self.model)

        if order_by is not None:
            statement = statement.order_by(order_by)

        return await self._list_from_stmt(db, statement)

    async def list_paginated(
        self,
        db: AsyncSession,
        params: PaginationParams,
        *,
        order_by: Any | None = None,
    ) -> tuple[list[ModelT], int]:
        statement = select(self.model)

        if order_by is not None:
            statement = statement.order_by(order_by)

        return await self._paginate_select(db, statement, params)

    async def get(self, db: AsyncSession, entity_id: Any) -> ModelT | None:
        return await db.get(self.model, entity_id)

    async def create(self, db: AsyncSession, entity: ModelT) -> ModelT:
        return await self._save(db, entity)

    async def update_fields(self, db: AsyncSession, entity: ModelT, data: dict[str, Any]) -> ModelT:
        for key, value in data.items():
            setattr(entity, key, value)
        db.add(entity)
        await db.flush()
        return entity

    async def delete(self, db: AsyncSession, entity: ModelT) -> None:
        await db.delete(entity)
        await db.flush()

    async def _save(self, db: AsyncSession, entity: EntityT) -> EntityT:
        db.add(entity)
        await db.flush()
        return entity
    
    def _save_many(self, db: AsyncSession, entities: list[EntityT]) -> list[EntityT]:
        db.add_all(entities)
        db.flush()
        return entities

    async def _get_one(self, db: AsyncSession, statement: Select[Any]) -> Any:
        return await db.scalar(statement)

    async def _list_from_stmt(self, db: AsyncSession, statement: Select[Any], *, unique: bool = False):
        result = await db.scalars(statement)
        if unique:
            result = result.unique()
        return list(result.all())

    async def _paginate_select(
        self,
        db: AsyncSession,
        statement: Select[Any],
        params: PaginationParams,
        *,
        unique: bool = False,
    ):
        total = int(
            await db.scalar(
                select(func.count()).select_from(statement.order_by(None).subquery())
            ) or 0
        )

        paginated_statement = statement.offset(
            (params.page - 1) * params.page_size
        ).limit(params.page_size)

        items = await self._list_from_stmt(db, paginated_statement, unique=unique)

        return items, total