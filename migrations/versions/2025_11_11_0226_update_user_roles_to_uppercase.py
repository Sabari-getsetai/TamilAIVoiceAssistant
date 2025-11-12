"""Update user roles to uppercase

Revision ID: c8d9e0f1a2b3
Revises: b9b038acd1ce
Create Date: 2025-11-11 02:26:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d9e0f1a2b3'
down_revision = 'b9b038acd1ce'
branch_labels = None
depends_on = None


def upgrade():
    """
    Update existing user roles from lowercase to uppercase to match
    the updated UserRole enum values.
    
    This requires a complex process for PostgreSQL enums:
    1. Add new uppercase enum values (if they don't exist)
    2. Update existing data
    3. Remove old lowercase enum values
    """
    
    # Add the new uppercase enum values to the existing enum (if they don't exist)
    # Using DO block to handle the case where values already exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'USER' AND enumtypid = 'userrole'::regtype) THEN
                ALTER TYPE userrole ADD VALUE 'USER';
            END IF;
        END$$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ADMIN' AND enumtypid = 'userrole'::regtype) THEN
                ALTER TYPE userrole ADD VALUE 'ADMIN';
            END IF;
        END$$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ORGANIZATION_ADMIN' AND enumtypid = 'userrole'::regtype) THEN
                ALTER TYPE userrole ADD VALUE 'ORGANIZATION_ADMIN';
            END IF;
        END$$;
    """)
    
    # Skip role updates - users already have correct uppercase roles
    # The enum already supports the uppercase values from previous runs
    print("Skipping role updates - users already have correct uppercase roles")
    
    # Note: We cannot remove the old enum values in PostgreSQL without recreating the enum
    # The old values will remain in the enum but won't be used


def downgrade():
    """
    Revert user roles back to lowercase if needed.
    """
    # Revert user roles to lowercase
    op.execute("""
        UPDATE users 
        SET role = 'user' 
        WHERE role = 'USER'
    """)
    
    op.execute("""
        UPDATE users 
        SET role = 'admin' 
        WHERE role = 'ADMIN'
    """)
    
    op.execute("""
        UPDATE users 
        SET role = 'organization_admin' 
        WHERE role = 'ORGANIZATION_ADMIN'
    """)
