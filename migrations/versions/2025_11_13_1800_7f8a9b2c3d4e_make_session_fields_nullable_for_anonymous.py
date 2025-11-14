"""Make user_id and organization_id nullable in conversation_sessions for anonymous sessions

Revision ID: 7f8a9b2c3d4e
Revises: 233578d2d0c4
Create Date: 2025-11-13 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f8a9b2c3d4e'
down_revision: Union[str, None] = '233578d2d0c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make user_id and organization_id nullable to support anonymous sessions."""
    # Make user_id nullable in conversation_sessions table
    op.alter_column(
        'conversation_sessions',
        'user_id',
        existing_type=sa.UUID(),
        nullable=True,
        existing_nullable=False
    )

    # Make organization_id nullable in conversation_sessions table
    op.alter_column(
        'conversation_sessions',
        'organization_id',
        existing_type=sa.UUID(),
        nullable=True,
        existing_nullable=False
    )


def downgrade() -> None:
    """Revert user_id and organization_id back to non-nullable."""
    # Note: This downgrade will fail if there are anonymous sessions in the database
    # You should clean up anonymous sessions before running this downgrade

    # Make organization_id non-nullable again
    op.alter_column(
        'conversation_sessions',
        'organization_id',
        existing_type=sa.UUID(),
        nullable=False,
        existing_nullable=True
    )

    # Make user_id non-nullable again
    op.alter_column(
        'conversation_sessions',
        'user_id',
        existing_type=sa.UUID(),
        nullable=False,
        existing_nullable=True
    )