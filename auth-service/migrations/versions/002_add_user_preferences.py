"""Add user preferences column

Revision ID: 002_add_user_preferences
Revises: 001_create_users_and_invites
Create Date: 2024-12-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_user_preferences'
down_revision: Union[str, None] = '001_create_users_and_invites'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add preferences column as JSON (nullable, stores user preferences like dark_mode)
    op.add_column(
        'users',
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'preferences')

