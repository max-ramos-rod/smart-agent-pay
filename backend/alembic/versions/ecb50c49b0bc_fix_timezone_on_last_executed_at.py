"""fix timezone on last_executed_at

Revision ID: ecb50c49b0bc
Revises: 5e99293e3f4d
Create Date: 2026-05-03 16:58:49.449060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ecb50c49b0bc'
down_revision: Union[str, Sequence[str], None] = '5e99293e3f4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
