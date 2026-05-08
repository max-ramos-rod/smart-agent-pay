"""fix timezone

Revision ID: a1eda53ee14a
Revises: ecb50c49b0bc
Create Date: 2026-05-03 17:04:37.064786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1eda53ee14a'
down_revision: Union[str, Sequence[str], None] = 'ecb50c49b0bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
