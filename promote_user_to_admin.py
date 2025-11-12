#!/usr/bin/env python3
"""
Script to promote a user to admin role.
This allows access to admin features.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database.connection import async_session_factory
from sqlalchemy import text


async def promote_user_to_admin():
    """Promote a user to admin role."""
    
    try:
        async with async_session_factory() as session:
            # Get all users
            result = await session.execute(text("""
                SELECT id, email, role 
                FROM users 
                ORDER BY created_at
            """))
            users = result.fetchall()
            
            print("Current users:")
            for i, user in enumerate(users, 1):
                print(f"  {i}. {user[1]} (Role: {user[2]})")
            
            if not users:
                print("No users found in database!")
                return
            
            # Promote the first user (sabari@test.com) to ADMIN
            first_user = users[0]
            user_id = first_user[0]
            user_email = first_user[1]
            
            print(f"\nPromoting {user_email} to ADMIN role...")
            
            await session.execute(text("""
                UPDATE users 
                SET role = 'ADMIN' 
                WHERE id = :user_id
            """), {"user_id": user_id})
            
            await session.commit()
            
            print(f"✅ Successfully promoted {user_email} to ADMIN role!")
            
            # Verify the change
            result = await session.execute(text("""
                SELECT email, role 
                FROM users 
                WHERE id = :user_id
            """), {"user_id": user_id})
            
            updated_user = result.fetchone()
            print(f"Verification: {updated_user[0]} now has role: {updated_user[1]}")
            
    except Exception as e:
        print(f"Error promoting user to admin: {e}")
        raise


if __name__ == "__main__":
    print("Promoting user to admin role...")
    asyncio.run(promote_user_to_admin())
    print("Done!")
