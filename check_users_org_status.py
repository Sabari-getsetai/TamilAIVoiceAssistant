#!/usr/bin/env python3
"""
Check current users and their organization status before migration.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database.connection import async_session_factory
from backend.database.models import User, Organization, OrganizationMember, Document, ConversationSession, AudioFile
from sqlalchemy import text


async def check_users_and_data():
    """Check current users and their organization status."""
    async with async_session_factory() as session:
        try:
            # Check users
            users = await session.execute(text("SELECT id, email, active_organization_id FROM users"))
            users_data = users.fetchall()
            
            print(f"=== USERS STATUS ===")
            print(f"Total users: {len(users_data)}")
            
            users_without_org = []
            for user in users_data:
                user_id, email, active_org_id = user
                print(f"User: {email} (ID: {user_id}), active_organization_id: {active_org_id}")
                if active_org_id is None:
                    users_without_org.append((user_id, email))
            
            print(f"\nUsers without active organization: {len(users_without_org)}")
            for user_id, email in users_without_org:
                print(f"  - {email} (ID: {user_id})")
            
            # Check existing organizations
            orgs = await session.execute(text("SELECT id, name, created_at FROM organizations"))
            orgs_data = orgs.fetchall()
            
            print(f"\n=== ORGANIZATIONS STATUS ===")
            print(f"Total organizations: {len(orgs_data)}")
            for org in orgs_data:
                org_id, name, created_by = org
                print(f"Organization: {name} (ID: {org_id}), created_by: {created_by}")
            
            # Check organization members
            members = await session.execute(text("SELECT organization_id, user_id, role FROM organization_members"))
            members_data = members.fetchall()
            
            print(f"\n=== ORGANIZATION MEMBERS ===")
            print(f"Total memberships: {len(members_data)}")
            for member in members_data:
                org_id, user_id, role = member
                print(f"User {user_id} -> Organization {org_id} (Role: {role})")
            
            # Check existing content that needs organization_id
            documents = await session.execute(text("SELECT COUNT(*) FROM documents"))
            doc_count = documents.scalar()
            
            sessions = await session.execute(text("SELECT COUNT(*) FROM conversation_sessions"))
            session_count = sessions.scalar()
            
            audio_files = await session.execute(text("SELECT COUNT(*) FROM audio_files"))
            audio_count = audio_files.scalar()
            
            print(f"\n=== CONTENT TO MIGRATE ===")
            print(f"Documents: {doc_count}")
            print(f"Conversation Sessions: {session_count}")
            print(f"Audio Files: {audio_count}")
            
            # Check if any content exists without user_id (would be problematic)
            docs_without_user = await session.execute(text("SELECT COUNT(*) FROM documents WHERE user_id IS NULL"))
            docs_without_user_count = docs_without_user.scalar()
            
            sessions_without_user = await session.execute(text("SELECT COUNT(*) FROM conversation_sessions WHERE user_id IS NULL"))
            sessions_without_user_count = sessions_without_user.scalar()
            
            if docs_without_user_count > 0 or sessions_without_user_count > 0:
                print(f"\n⚠️  WARNING: Found content without user_id:")
                print(f"  - Documents without user_id: {docs_without_user_count}")
                print(f"  - Sessions without user_id: {sessions_without_user_count}")
            
            return {
                'users_without_org': users_without_org,
                'total_users': len(users_data),
                'total_orgs': len(orgs_data),
                'content_counts': {
                    'documents': doc_count,
                    'sessions': session_count,
                    'audio_files': audio_count
                }
            }
            
        except Exception as e:
            print(f"Error checking database: {e}")
            return None


if __name__ == "__main__":
    result = asyncio.run(check_users_and_data())
    
    if result and result['users_without_org']:
        print(f"\n🚨 CRITICAL: {len(result['users_without_org'])} users need default organizations created!")
        print("This must be done before running the organization scoping migration.")
    elif result:
        print(f"\n✅ All {result['total_users']} users have active organizations.")
        print("Safe to proceed with organization scoping migration.")
