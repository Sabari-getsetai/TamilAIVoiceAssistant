"""add_organization_scoping_to_documents_and_sessions

Revision ID: 6b9f23fe27b2
Revises: c8d9e0f1a2b3
Create Date: 2025-11-11 14:16:49.788803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b9f23fe27b2'
down_revision: Union[str, None] = 'c8d9e0f1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add organization_id foreign key to documents table
    op.add_column('documents', sa.Column('organization_id', sa.UUID(as_uuid=False), nullable=True))
    op.create_foreign_key('fk_documents_organization_id', 'documents', 'organizations', ['organization_id'], ['id'])

    # Add organization_id foreign key to conversation_sessions table
    op.add_column('conversation_sessions', sa.Column('organization_id', sa.UUID(as_uuid=False), nullable=True))
    op.create_foreign_key('fk_conversation_sessions_organization_id', 'conversation_sessions', 'organizations', ['organization_id'], ['id'])

    # Add organization_id foreign key to audio_files table
    op.add_column('audio_files', sa.Column('organization_id', sa.UUID(as_uuid=False), nullable=True))
    op.create_foreign_key('fk_audio_files_organization_id', 'audio_files', 'organizations', ['organization_id'], ['id'])

    # Populate organization_id for existing records based on user's active organization
    # This is a data migration that should run after all schema changes
    conn = op.get_bind()

    # Update documents with organization_id from user's active organization
    conn.execute(sa.text("""
        UPDATE documents
        SET organization_id = users.active_organization_id
        FROM users
        WHERE documents.user_id = users.id
        AND users.active_organization_id IS NOT NULL
    """))

    # Update conversation_sessions with organization_id from user's active organization
    conn.execute(sa.text("""
        UPDATE conversation_sessions
        SET organization_id = users.active_organization_id
        FROM users
        WHERE conversation_sessions.user_id = users.id
        AND users.active_organization_id IS NOT NULL
    """))

    # Update audio_files with organization_id from user's active organization
    conn.execute(sa.text("""
        UPDATE audio_files
        SET organization_id = users.active_organization_id
        FROM users
        WHERE audio_files.user_id = users.id
        AND users.active_organization_id IS NOT NULL
    """))

    # Make organization_id NOT NULL after populating data
    # Note: This will fail if there are users without organizations - which is the intended behavior
    # to enforce the "NO APP ACCESS WITHOUT ORG MEMBERSHIP" rule
    op.alter_column('documents', 'organization_id', nullable=False)
    op.alter_column('conversation_sessions', 'organization_id', nullable=False)
    op.alter_column('audio_files', 'organization_id', nullable=False)


def downgrade() -> None:
    # Remove NOT NULL constraints first
    op.alter_column('documents', 'organization_id', nullable=True)
    op.alter_column('conversation_sessions', 'organization_id', nullable=True)
    op.alter_column('audio_files', 'organization_id', nullable=True)

    # Drop foreign key constraints
    op.drop_constraint('fk_documents_organization_id', 'documents', type_='foreignkey')
    op.drop_constraint('fk_conversation_sessions_organization_id', 'conversation_sessions', type_='foreignkey')
    op.drop_constraint('fk_audio_files_organization_id', 'audio_files', type_='foreignkey')

    # Drop columns
    op.drop_column('documents', 'organization_id')
    op.drop_column('conversation_sessions', 'organization_id')
    op.drop_column('audio_files', 'organization_id')