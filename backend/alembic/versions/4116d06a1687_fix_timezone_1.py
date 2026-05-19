"""fix timezone 1

Revision ID: 4116d06a1687
Revises: a1eda53ee14a
Create Date: 2026-05-03 17:12:05.535810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4116d06a1687'
down_revision: Union[str, Sequence[str], None] = 'a1eda53ee14a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "strategies",
        "last_executed_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "strategies",
        "last_executed_at",
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )