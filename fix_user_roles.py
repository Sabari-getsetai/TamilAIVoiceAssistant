#!/usr/bin/env python3
"""
Script to fix user roles from lowercase to uppercase values.
This bypasses the complex PostgreSQL enum migration issues.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from database.connection import engine
from database.models import User


async def fix_user_roles():
    """Fix user roles from lowercase to uppercase."""
    
    # Use existing async engine
    # engine is already created in database.connection
    
    try:
        async with engine.begin() as conn:
            # First, let's see what roles currently exist
            result = await conn.execute(text("SELECT DISTINCT role FROM users"))
            current_roles = [row[0] for row in result.fetchall()]
            print(f"Current roles in database: {current_roles}")
            
            # Check what enum values are available
            result = await conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = 'userrole'::regtype 
                ORDER BY enumlabel
            """))
            enum_values = [row[0] for row in result.fetchall()]
            print(f"Available enum values: {enum_values}")
            
            # Add uppercase enum values if they don't exist
            for new_value in ['USER', 'ADMIN', 'ORGANIZATION_ADMIN']:
                if new_value not in enum_values:
                    print(f"Adding enum value: {new_value}")
                    await conn.execute(text(f"ALTER TYPE userrole ADD VALUE '{new_value}'"))
            
            # Update user roles to uppercase
            updates = [
                ('user', 'USER'),
                ('admin', 'ADMIN'), 
                ('organization_admin', 'ORGANIZATION_ADMIN')
            ]
            
            for old_role, new_role in updates:
                if old_role in current_roles:
                    print(f"Updating {old_role} -> {new_role}")
                    result = await conn.execute(text(f"""
                        UPDATE users 
                        SET role = '{new_role}' 
                        WHERE role = '{old_role}'
                    """))
                    print(f"Updated {result.rowcount} users")
            
            # Verify the changes
            result = await conn.execute(text("SELECT DISTINCT role FROM users"))
            final_roles = [row[0] for row in result.fetchall()]
            print(f"Final roles in database: {final_roles}")
            
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Fixing user roles from lowercase to uppercase...")
    asyncio.run(fix_user_roles())
    print("Done!")
