"""Add ORG_ADMIN role and tier-based organization limits

Revision ID: 4a1345b9df0b
Revises: 6b9f23fe27b2
Create Date: 2025-11-12 10:26:16.605300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a1345b9df0b'
down_revision: Union[str, None] = '6b9f23fe27b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ORG_ADMIN role to OrganizationRole enum
    op.execute("ALTER TYPE organizationrole ADD VALUE 'ORG_ADMIN'")

    # Add tier-based organization limits to Organization table
    op.add_column('organizations', sa.Column('max_organizations_per_user', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('organizations', sa.Column('tier_type', sa.String(50), nullable=False, server_default='free'))

    # Add organization ownership limits to User table
    op.add_column('users', sa.Column('max_organizations_allowed', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('subscription_tier', sa.String(50), nullable=False, server_default='free'))

    # Create index for faster tier-based queries
    op.create_index('ix_users_subscription_tier', 'users', ['subscription_tier'])
    op.create_index('ix_organizations_tier_type', 'organizations', ['tier_type'])

    # Update existing free tier users with proper limits
    op.execute("UPDATE users SET max_organizations_allowed = 1, subscription_tier = 'free' WHERE subscription_tier = 'free'")
    op.execute("UPDATE organizations SET tier_type = 'free', max_organizations_per_user = 1 WHERE subscription_plan = 'free'")


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_users_subscription_tier')
    op.drop_index('ix_organizations_tier_type')

    # Remove tier-based columns from User table
    op.drop_column('users', 'max_organizations_allowed')
    op.drop_column('users', 'subscription_tier')

    # Remove tier-based columns from Organization table
    op.drop_column('organizations', 'max_organizations_per_user')
    op.drop_column('organizations', 'tier_type')

    # Note: Cannot remove enum value in PostgreSQL without recreating the type
    # The ORG_ADMIN role will remain in the enum but won't be used