"""Add organization invitations table

Revision ID: 233578d2d0c4
Revises: 4a1345b9df0b
Create Date: 2025-11-12 20:19:06.163745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '233578d2d0c4'
down_revision: Union[str, None] = '4a1345b9df0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create organization_invitations table using raw SQL to avoid enum creation issue
    op.execute("""
        CREATE TABLE organization_invitations (
            id VARCHAR NOT NULL,
            organization_id VARCHAR NOT NULL,
            invited_email VARCHAR(255) NOT NULL,
            role organizationrole NOT NULL,
            invited_by VARCHAR NOT NULL,
            token VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            accepted_at TIMESTAMP WITH TIME ZONE,
            accepted_by VARCHAR,
            is_expired BOOLEAN NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(accepted_by) REFERENCES users (id),
            FOREIGN KEY(invited_by) REFERENCES users (id),
            FOREIGN KEY(organization_id) REFERENCES organizations (id),
            CONSTRAINT uq_organization_invitation_email UNIQUE (organization_id, invited_email),
            CONSTRAINT uq_invitation_token UNIQUE (token)
        )
    """)

    # Create indexes
    op.create_index('ix_invitations_email_token', 'organization_invitations', ['invited_email', 'token'])
    op.create_index('ix_invitations_org_expires', 'organization_invitations', ['organization_id', 'expires_at'])
    op.create_index(op.f('ix_organization_invitations_invited_email'), 'organization_invitations', ['invited_email'])
    op.create_index(op.f('ix_organization_invitations_is_expired'), 'organization_invitations', ['is_expired'])
    op.create_index(op.f('ix_organization_invitations_token'), 'organization_invitations', ['token'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_organization_invitations_token'), table_name='organization_invitations')
    op.drop_index(op.f('ix_organization_invitations_is_expired'), table_name='organization_invitations')
    op.drop_index(op.f('ix_organization_invitations_invited_email'), table_name='organization_invitations')
    op.drop_index('ix_invitations_org_expires', table_name='organization_invitations')
    op.drop_index('ix_invitations_email_token', table_name='organization_invitations')

    # Drop table using raw SQL
    op.execute("DROP TABLE IF EXISTS organization_invitations")