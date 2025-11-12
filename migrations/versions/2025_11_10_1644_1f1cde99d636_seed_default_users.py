"""seed_default_users

Revision ID: 1f1cde99d636
Revises: 0e6259807e88
Create Date: 2025-11-10 16:44:10.215021

"""
from typing import Sequence, Union
from datetime import datetime
import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, DateTime, Boolean
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision: str = '1f1cde99d636'
down_revision: Union[str, None] = '0e6259807e88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Get admin credentials from environment variables
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@localhost')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Truncate password to 72 bytes for bcrypt compatibility
    safe_admin_password = admin_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    
    # Hash the admin password
    admin_password_hash = pwd_context.hash(safe_admin_password)
    
    # Create users table reference for SQLAlchemy operations
    users_table = table('users',
        column('id', sa.UUID),
        column('email', String),
        column('username', String),
        column('password_hash', String),
        column('full_name', String),
        column('role', String),
        column('is_active', Boolean),
        column('is_verified', Boolean),
        column('created_at', DateTime),
        column('updated_at', DateTime)
    )
    
    # Insert admin user with environment-based credentials
    op.bulk_insert(users_table, [
        {
            'id': '00000000-0000-0000-0000-000000000001',
            'email': admin_email,
            'username': 'admin',
            'password_hash': admin_password_hash,
            'full_name': 'System Administrator',
            'role': 'ADMIN',
            'is_active': True,
            'is_verified': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': '00000000-0000-0000-0000-000000000002',
            'email': 'system@localhost',
            'username': 'system',
            'password_hash': pwd_context.hash('system_default_password'),
            'full_name': 'System User (Anonymous Sessions)',
            'role': 'USER',
            'is_active': True,
            'is_verified': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ])


def downgrade() -> None:
    # Remove default users
    op.execute("DELETE FROM users WHERE id IN ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002')")
