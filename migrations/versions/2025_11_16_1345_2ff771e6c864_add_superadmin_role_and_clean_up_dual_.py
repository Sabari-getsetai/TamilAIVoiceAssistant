"""Add SUPERADMIN role and clean up dual dashboard role structure

Revision ID: 2ff771e6c864
Revises: 375b07257851
Create Date: 2025-11-16 13:45:23.860357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ff771e6c864'
down_revision: Union[str, None] = '375b07257851'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add SUPERADMIN to the UserRole enum
    # First, create the new enum with all values including SUPERADMIN
    op.execute("ALTER TYPE userrole ADD VALUE 'SUPERADMIN'")

    # Update any existing ORGANIZATION_ADMIN users to proper roles based on context
    # For now, just ensure the enum is properly updated

    # Add comment to track this change
    op.execute("COMMENT ON TYPE userrole IS 'Updated to include SUPERADMIN for dual dashboard architecture'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values, so we just add a warning
    # In practice, downgrading enum values is complex and should be handled carefully
    op.execute("COMMENT ON TYPE userrole IS 'Downgrade warning: SUPERADMIN values may exist in database'")