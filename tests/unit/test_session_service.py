#!/usr/bin/env python3
"""
Unit tests for the new DatabaseSessionManager service.

Tests all CRUD operations, Redis caching integration, and edge cases
for the session management system.
"""

import asyncio
import sys
import pytest
import pytest_asyncio
import logging
import uuid
import bcrypt
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Configure logging for testing
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test fixtures and utilities
@pytest_asyncio.fixture
async def session_manager():
    """Create a fresh session manager for each test."""
    try:
        from services.session_service import DatabaseSessionManager
        from database.connection import get_db, init_db

        # Ensure database is initialized
        await init_db()

        # Create session manager
        manager = DatabaseSessionManager()

        yield manager

        # Cleanup: This would be done in a real test with proper teardown
        # For now, we'll leave the test sessions in the database

    except Exception as e:
        logger.error(f"Failed to create session manager fixture: {e}")
        raise

@pytest_asyncio.fixture
async def test_user():
    """Create a test user for session tests."""
    from database.connection import get_db
    from database.models import User, UserRole, generate_uuid, utc_now
    
    db = await anext(get_db())
    try:
        # Create test user with unique username/email to avoid conflicts
        user_id = generate_uuid()
        unique_suffix = user_id[:8]  # Use first 8 chars of UUID for uniqueness
        password_hash = bcrypt.hashpw("testpass123".encode(), bcrypt.gensalt()).decode()
        
        user = User(
            id=user_id,
            email=f"test_{unique_suffix}@example.com",
            username=f"testuser_{unique_suffix}",
            password_hash=password_hash,
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            created_at=utc_now()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Created test user: {user_id}")
        yield user_id
        
        # Cleanup - delete test user and all related data
        # The cascade delete should handle sessions and other related data
        await db.delete(user)
        await db.commit()
        logger.info(f"Cleaned up test user: {user_id}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create test user: {e}")
        raise
    finally:
        await db.close()

@pytest.fixture
def sample_session_data(test_user):
    """Sample session data for testing."""
    return {
        "user_id": test_user,  # Use actual test user
        "language": "ta",
        "rag_enabled": True,
        "session_metadata": {
            "test": "unit_test",
            "created_by": "pytest",
            "environment": "test"
        }
    }

@pytest.fixture
def sample_conversation_turn():
    """Sample conversation turn data for testing."""
    return {
        "user_text": "வணக்கம்! செயற்கை நுண்ணறிவு பற்றி எனக்கு தெரிந்துகொள்ள வேண்டும்.",
        "assistant_text": "வணக்கம்! செயற்கை நுண்ணறிவு (AI) என்பது கணினிகளுக்கு மனித போன்ற சிந்தனை திறன் அளிக்கும் தொழில்நுட்பம் ஆகும்.",
        "retrieved_chunks": ["chunk_ai_basics", "chunk_tamil_ai"],
        "processing_time": {
            "stt": 0.45,
            "rag": 0.32,
            "llm": 1.15,
            "tts": 0.68
        },
        "turn_metadata": {
            "model_used": "test_model",
            "confidence": 0.95,
            "language_detected": "ta"
        }
    }

class TestDatabaseSessionManager:
    """Test class for DatabaseSessionManager functionality."""

    @pytest.mark.asyncio
    async def test_session_creation(self, session_manager, sample_session_data):
        """Test creating a new session."""
        session_id = await session_manager.create_session(**sample_session_data)

        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        logger.info(f"Created session: {session_id}")

    @pytest.mark.asyncio
    async def test_session_retrieval(self, session_manager, sample_session_data):
        """Test retrieving an existing session."""
        # Create session
        session_id = await session_manager.create_session(**sample_session_data)

        # Retrieve session (disable cache to get fresh data from DB)
        session_data = await session_manager.get_session(session_id, use_cache=False)

        assert session_data is not None
        assert session_data["session_id"] == session_id
        assert session_data["language"] == sample_session_data["language"]
        assert session_data["rag_enabled"] == sample_session_data["rag_enabled"]
        assert session_data["user_id"] == sample_session_data["user_id"]

    @pytest.mark.asyncio
    async def test_session_retrieval_nonexistent(self, session_manager):
        """Test retrieving a non-existent session."""
        session_data = await session_manager.get_session("nonexistent_session_id")

        assert session_data is None

    @pytest.mark.asyncio
    async def test_conversation_turn_creation(self, session_manager, sample_session_data, sample_conversation_turn):
        """Test adding a conversation turn to a session."""
        # Create session
        session_id = await session_manager.create_session(**sample_session_data)

        # Add conversation turn
        turn_id = await session_manager.add_conversation_turn(
            session_id=session_id,
            **sample_conversation_turn
        )

        assert turn_id is not None
        assert isinstance(turn_id, str)
        logger.info(f"Created turn: {turn_id}")

    @pytest.mark.asyncio
    async def test_conversation_history(self, session_manager, sample_session_data, sample_conversation_turn):
        """Test retrieving conversation history."""
        # Create session
        session_id = await session_manager.create_session(**sample_session_data)

        # Add multiple conversation turns
        turn_ids = []
        for i in range(3):
            turn_data = sample_conversation_turn.copy()
            turn_data["user_text"] += f" (Turn {i+1})"
            turn_data["assistant_text"] += f" இது {i+1} வது பதில்."

            turn_id = await session_manager.add_conversation_turn(
                session_id=session_id,
                **turn_data
            )
            turn_ids.append(turn_id)

        # Retrieve history
        history = await session_manager.get_conversation_history(session_id, limit=10)

        assert history is not None
        assert len(history) == 3
        assert history[0]["turn_number"] == 1  # First turn should be first
        assert history[2]["turn_number"] == 3  # Third turn should be last

    @pytest.mark.asyncio
    async def test_session_metadata_update(self, session_manager, sample_session_data):
        """Test updating session metadata."""
        # Create session
        session_id = await session_manager.create_session(**sample_session_data)

        # Get initial session (disable cache)
        initial_session = await session_manager.get_session(session_id, use_cache=False)
        initial_metadata = initial_session["session_metadata"]

        # Update metadata
        new_metadata = {"updated": True, "test_value": 42}
        updated = await session_manager.update_session_metadata(session_id, new_metadata)

        assert updated is True

        # Verify metadata was updated (disable cache to get fresh data)
        updated_session = await session_manager.get_session(session_id, use_cache=False)
        final_metadata = updated_session["session_metadata"]

        # Should contain both original and new metadata
        assert "test" in final_metadata  # Original
        assert "updated" in final_metadata  # New
        assert final_metadata["updated"] is True
        assert final_metadata["test_value"] == 42

    @pytest.mark.asyncio
    async def test_session_deletion(self, session_manager, sample_session_data, test_user):
        """Test deleting a session."""
        # Create session
        session_id = await session_manager.create_session(**sample_session_data)

        # Delete session with user_id for authorization
        deleted = await session_manager.delete_session(session_id, user_id=test_user)

        assert deleted is True

        # Verify session is marked as ended (soft delete)
        session_data = await session_manager.get_session(session_id)
        # Session should be None since it's expired/ended
        assert session_data is None

    @pytest.mark.asyncio
    async def test_active_sessions_listing(self, session_manager, sample_session_data, test_user):
        """Test listing active sessions for a user."""
        # Create multiple sessions for the test user
        session_ids = []
        for i in range(3):
            session_id = await session_manager.create_session(
                user_id=test_user,
                language=sample_session_data["language"],
                session_metadata={"session_number": i}
            )
            session_ids.append(session_id)

        # Delete one session
        await session_manager.delete_session(session_ids[1], user_id=test_user)

        # List active sessions for the user
        active_sessions = await session_manager.list_user_sessions(test_user)
        
        # Should have 2 active sessions (created 3, deleted 1)
        assert len(active_sessions) == 2
        assert all(s["status"] == "active" for s in active_sessions)
        
        # Verify the deleted session is not in the list
        active_session_ids = [s["session_id"] for s in active_sessions]
        assert session_ids[1] not in active_session_ids
        assert session_ids[0] in active_session_ids
        assert session_ids[2] in active_session_ids

    @pytest.mark.asyncio
    async def test_session_expiration(self, session_manager, sample_session_data):
        """Test session expiration functionality."""
        # Create session
        session_id = await session_manager.create_session(**sample_session_data)

        # Test expiration check (should not be expired)
        # cleanup_expired_sessions returns count, not list of sessions
        expired_count = await session_manager.cleanup_expired_sessions(batch_size=100)

        # Should be 0 or very low since we just created the session
        assert expired_count >= 0

        # Verify session is still active (disable cache)
        session_data = await session_manager.get_session(session_id, use_cache=False)
        assert session_data["status"] == "active"

    @pytest.mark.asyncio
    async def test_invalid_operations(self, session_manager):
        """Test handling of invalid operations."""
        # Test adding turn to non-existent session
        turn_id = await session_manager.add_conversation_turn(
            session_id="nonexistent",
            user_text="Test",
            assistant_text="Test response"
        )
        assert turn_id is None

        # Test updating metadata for non-existent session
        updated = await session_manager.update_session_metadata("nonexistent", {"test": True})
        assert updated is False

        # Test deleting non-existent session
        deleted = await session_manager.delete_session("nonexistent")
        assert deleted is False

        # Test invalid UUID format
        with pytest.raises(ValueError, match="Invalid UUID format"):
            await session_manager.create_session(user_id="invalid_uuid")
        
        # Test deleting with invalid user_id UUID
        with pytest.raises(ValueError, match="Invalid UUID format"):
            await session_manager.delete_session("some_session_id", user_id="invalid_uuid")
        
        # Test listing sessions with invalid user_id UUID
        with pytest.raises(ValueError, match="Invalid UUID format"):
            await session_manager.list_user_sessions("invalid_uuid")

    @pytest.mark.asyncio
    async def test_session_statistics(self, session_manager, sample_session_data, sample_conversation_turn):
        """Test session statistics calculation."""
        # Create session
        session_id = await session_manager.create_session(**sample_session_data)

        # Add conversation turns
        for i in range(5):
            await session_manager.add_conversation_turn(
                session_id=session_id,
                user_text=f"Test message {i+1}",
                assistant_text=f"Test response {i+1}"
            )

        # Get session with updated statistics (disable cache to get fresh data)
        session_data = await session_manager.get_session(session_id, use_cache=False)

        assert session_data["total_turns"] == 5

    @pytest.mark.asyncio
    async def test_redis_caching_integration(self, session_manager, sample_session_data):
        """Test Redis caching functionality if available."""
        # Create session
        session_id = await session_manager.create_session(**sample_session_data)

        # First retrieval (should cache in Redis)
        session_data_1 = await session_manager.get_session(session_id)

        # Second retrieval (should come from Redis cache)
        session_data_2 = await session_manager.get_session(session_id)

        # Core data should be identical (ignoring timestamps that may differ slightly)
        assert session_data_1["session_id"] == session_data_2["session_id"]
        assert session_data_1["user_id"] == session_data_2["user_id"]
        assert session_data_1["language"] == session_data_2["language"]
        assert session_data_1["status"] == session_data_2["status"]
        
        # Verify caching worked (this test assumes Redis is available)
        # In a real test environment, we'd mock Redis or use a test Redis instance


# Standalone test runner for manual execution
async def run_manual_tests():
    """Run tests manually without pytest."""
    print("🧪 Running DatabaseSessionManager Unit Tests (Manual Mode)")
    print("=" * 60)

    try:
        from services.session_service import DatabaseSessionManager
        from database.connection import init_db, get_db
        from database.models import User, UserRole, generate_uuid, utc_now

        # Initialize database
        await init_db()

        # Create test user
        db = await anext(get_db())
        user_id = generate_uuid()
        password_hash = bcrypt.hashpw("testpass123".encode(), bcrypt.gensalt()).decode()
        
        user = User(
            id=user_id,
            email="manual_test@example.com",
            username="manual_testuser",
            password_hash=password_hash,
            full_name="Manual Test User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            created_at=utc_now()
        )
        
        db.add(user)
        await db.commit()
        print(f"✓ Created test user: {user_id}")

        # Create session manager
        session_manager = DatabaseSessionManager()

        # Sample data
        sample_data = {
            "user_id": user_id,  # Use actual test user
            "language": "ta",
            "rag_enabled": True,
            "session_metadata": {"test": "manual_run"}
        }

        # Test 1: Session creation
        print("\n🔍 Test 1: Session Creation")
        session_id = await session_manager.create_session(**sample_data)
        print(f"✓ Created session: {session_id}")

        # Test 2: Session retrieval
        print("\n🔍 Test 2: Session Retrieval")
        session_data = await session_manager.get_session(session_id)
        print(f"✓ Retrieved session: {session_data['session_id']}")
        print(f"  Language: {session_data['language']}")
        print(f"  Status: {session_data['status']}")

        # Test 3: Conversation turn
        print("\n🔍 Test 3: Conversation Turn")
        turn_id = await session_manager.add_conversation_turn(
            session_id=session_id,
            user_text="வணக்கம்! இது ஒரு சோதனை.",
            assistant_text="வணக்கம்! நான் உங்களுக்கு உதவ தயாராக இருக்கிறேன்."
        )
        print(f"✓ Created conversation turn: {turn_id}")

        # Test 4: Conversation history
        print("\n🔍 Test 4: Conversation History")
        history = await session_manager.get_conversation_history(session_id)
        print(f"✓ Retrieved {len(history)} conversation turns")
        if history:
            print(f"  First turn: {history[0]['user_text'][:50]}...")

        # Test 5: Session cleanup
        print("\n🔍 Test 5: Session Cleanup")
        deleted = await session_manager.delete_session(session_id, user_id=user_id)
        print(f"✓ Session cleanup: {'SUCCESS' if deleted else 'FAILED'}")

        # Cleanup test user
        await db.delete(user)
        await db.commit()
        await db.close()

        print("\n🎉 All manual tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Manual test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run manual tests if executed directly
    asyncio.run(run_manual_tests())
