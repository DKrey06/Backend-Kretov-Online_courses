"""add index on title

Revision ID: 8e6795b51d02
Revises: 
Create Date: 2026-11-06 17:57:44.219934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e6795b51d02'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_courses_title', 'courses', ['title'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_courses_title', table_name='courses')
