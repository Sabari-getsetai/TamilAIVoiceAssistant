#!/usr/bin/env python3
"""
Script to check current user roles in the database.
This helps diagnose permission issues.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database.connection import async_session_factory
from sqlalchemy import text


async def check_user_roles():
    """Check current user roles in the database."""
    
    try:
        async with async_session_factory() as session:
            # Get all users with their roles
            result = await session.execute(text("""
                SELECT id, email, role, created_at 
                FROM users 
                ORDER BY created_at
            """))
            users = result.fetchall()
            
            print("Current users in database:")
            print("-" * 80)
            for user in users:
                print(f"  ID: {user[0]}")
                print(f"  Email: {user[1]}")
                print(f"  Role: {user[2]}")
                print(f"  Created: {user[3]}")
                print("-" * 40)
            
            # Check enum values
            result = await session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = 'userrole'::regtype 
                ORDER BY enumlabel
            """))
            enum_values = [row[0] for row in result.fetchall()]
            print(f"\nAvailable UserRole enum values: {enum_values}")
            
            # Check distinct roles in use
            result = await session.execute(text("SELECT DISTINCT role FROM users"))
            current_roles = [row[0] for row in result.fetchall()]
            print(f"Roles currently in use: {current_roles}")
            
    except Exception as e:
        print(f"Error checking user roles: {e}")
        raise


if __name__ == "__main__":
    print("Checking user roles in database...")
    asyncio.run(check_user_roles())
    print("Done!")
