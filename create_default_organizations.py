#!/usr/bin/env python3
"""
Create default organizations for users who don't have active_organization_id set.
This MUST be run before the organization scoping migration.
"""

import asyncio
import sys
import os
from datetime import datetime
import uuid

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database.connection import async_session_factory
from backend.database.models import User, Organization, OrganizationMember, OrganizationRole
from sqlalchemy import text


async def create_default_organizations():
    """Create default organizations for users without active_organization_id."""
    async with async_session_factory() as session:
        try:
            # Find users without active organizations
            users_result = await session.execute(
                text("SELECT id, email FROM users WHERE active_organization_id IS NULL")
            )
            users_without_org = users_result.fetchall()
            
            if not users_without_org:
                print("✅ All users already have active organizations.")
                return True
            
            print(f"Found {len(users_without_org)} users without active organizations:")
            for user_id, email in users_without_org:
                print(f"  - {email} (ID: {user_id})")
            
            print("\n🔧 Creating default organizations...")
            
            created_count = 0
            for user_id, email in users_without_org:
                try:
                    # Create organization
                    org_id = str(uuid.uuid4())
                    org_name = f"{email.split('@')[0]}'s Personal Workspace"
                    
                    await session.execute(
                        text("""
                            INSERT INTO organizations (id, name, description, creator_id, size, timezone, is_active, subscription_plan, subscription_status, created_at, updated_at)
                            VALUES (:org_id, :name, :description, :creator_id, :size, :timezone, :is_active, :subscription_plan, :subscription_status, :created_at, :updated_at)
                        """),
                        {
                            'org_id': org_id,
                            'name': org_name,
                            'description': f"Personal workspace for {email}",
                            'creator_id': user_id,
                            'size': 'startup',
                            'timezone': 'UTC',
                            'is_active': True,
                            'subscription_plan': 'free',
                            'subscription_status': 'active',
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        }
                    )
                    
                    # Add user as OWNER of the organization
                    await session.execute(
                        text("""
                            INSERT INTO organization_members (organization_id, user_id, role, joined_at)
                            VALUES (:org_id, :user_id, :role, :joined_at)
                        """),
                        {
                            'org_id': org_id,
                            'user_id': user_id,
                            'role': OrganizationRole.OWNER.value,
                            'joined_at': datetime.utcnow()
                        }
                    )
                    
                    # Set as user's active organization
                    await session.execute(
                        text("""
                            UPDATE users 
                            SET active_organization_id = :org_id, updated_at = :updated_at
                            WHERE id = :user_id
                        """),
                        {
                            'org_id': org_id,
                            'user_id': user_id,
                            'updated_at': datetime.utcnow()
                        }
                    )
                    
                    print(f"  ✅ Created organization '{org_name}' for {email}")
                    created_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Failed to create organization for {email}: {e}")
                    await session.rollback()
                    return False
            
            # Commit all changes
            await session.commit()
            
            print(f"\n🎉 Successfully created {created_count} default organizations!")
            
            # Verify all users now have active organizations
            verification_result = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE active_organization_id IS NULL")
            )
            remaining_users = verification_result.scalar()
            
            if remaining_users == 0:
                print("✅ Verification: All users now have active organizations.")
                return True
            else:
                print(f"⚠️  Warning: {remaining_users} users still without active organizations.")
                return False
                
        except Exception as e:
            print(f"❌ Error creating default organizations: {e}")
            await session.rollback()
            return False


async def verify_migration_readiness():
    """Verify that the database is ready for organization scoping migration."""
    async with async_session_factory() as session:
        try:
            # Check users without organizations
            users_result = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE active_organization_id IS NULL")
            )
            users_without_org = users_result.scalar()
            
            # Check content counts
            docs_result = await session.execute(text("SELECT COUNT(*) FROM documents"))
            docs_count = docs_result.scalar()
            
            sessions_result = await session.execute(text("SELECT COUNT(*) FROM conversation_sessions"))
            sessions_count = sessions_result.scalar()
            
            audio_result = await session.execute(text("SELECT COUNT(*) FROM audio_files"))
            audio_count = audio_result.scalar()
            
            print(f"\n=== MIGRATION READINESS CHECK ===")
            print(f"Users without active organization: {users_without_org}")
            print(f"Documents to migrate: {docs_count}")
            print(f"Sessions to migrate: {sessions_count}")
            print(f"Audio files to migrate: {audio_count}")
            
            if users_without_org == 0:
                print("✅ READY: All users have active organizations.")
                print("✅ Safe to run organization scoping migration.")
                return True
            else:
                print("❌ NOT READY: Some users still lack active organizations.")
                return False
                
        except Exception as e:
            print(f"❌ Error checking migration readiness: {e}")
            return False


if __name__ == "__main__":
    print("🚀 Creating default organizations for users...")
    
    # Create default organizations
    success = asyncio.run(create_default_organizations())
    
    if success:
        # Verify readiness
        ready = asyncio.run(verify_migration_readiness())
        
        if ready:
            print("\n🎯 NEXT STEP: Run the organization scoping migration:")
            print("   alembic upgrade head")
        else:
            print("\n⚠️  Please resolve issues before running migration.")
    else:
        print("\n❌ Failed to create default organizations. Please check errors above.")
