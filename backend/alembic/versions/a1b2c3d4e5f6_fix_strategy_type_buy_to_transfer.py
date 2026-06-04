"""fix strategy type buy to transfer

Revision ID: a1b2c3d4e5f6
Revises: 6e84c397014c
Create Date: 2026-06-04

"""
from alembic import op

revision = 'a1b2c3d4e5f6'
down_revision = '6e84c397014c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE strategies SET type = 'transfer' WHERE type = 'buy'")


def downgrade() -> None:
    op.execute("UPDATE strategies SET type = 'buy' WHERE type = 'transfer'")
