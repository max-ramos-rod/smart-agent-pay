"""add jupiter swap fields

Revision ID: a8f3d2e91c05
Revises: 59122cf0c1c4
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a8f3d2e91c05'
down_revision: Union[str, Sequence[str], None] = '59122cf0c1c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('strategies', sa.Column('token_in', sa.String(length=10), nullable=True))
    op.add_column('strategies', sa.Column('token_out', sa.String(length=10), nullable=True))
    op.add_column('strategies', sa.Column('slippage_bps', sa.Integer(), nullable=True))
    op.add_column('executions', sa.Column('serialized_tx', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('executions', 'serialized_tx')
    op.drop_column('strategies', 'slippage_bps')
    op.drop_column('strategies', 'token_out')
    op.drop_column('strategies', 'token_in')
