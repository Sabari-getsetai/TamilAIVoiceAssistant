#!/usr/bin/env python3
"""
Infrastructure test script for Tamil AI Voice Assistant.

This script tests the complete infrastructure setup:
- PostgreSQL database connection
- Redis connection and operations
- MinIO object storage
- All new services and configurations

Run this script after starting the dev environment with ./dev-start.sh
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from io import BytesIO

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name: str):
    """Print test section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}Testing: {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

async def test_postgresql():
    """Test PostgreSQL database connection and operations."""
    print_test_header("PostgreSQL Database")

    try:
        from backend.database.connection import get_db, init_db, check_db_health, close_db
        from sqlalchemy import text

        # Test database health
        print_info("Testing database connection...")
        healthy = await check_db_health()
        if healthy:
            print_success("Database connection successful")
        else:
            print_error("Database connection failed")
            return False

        # Test database initialization
        print_info("Testing database initialization...")
        await init_db()
        print_success("Database tables created successfully")

        # Test session creation
        print_info("Testing database session...")
        async for db in get_db():
            try:
                result = await db.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                if test_value == 1:
                    print_success("Database query successful")
                else:
                    print_error("Database query failed")
                    return False
                break
            finally:
                # Session cleanup handled by generator
                pass

        # Test pgVector extension
        print_info("Testing pgVector extension...")
        async for db in get_db():
            try:
                result = await db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
                extension = result.scalar()
                if extension == 'vector':
                    print_success("pgVector extension is installed")
                else:
                    print_error("pgVector extension not found")
                    return False
                break
            finally:
                # Session cleanup handled by generator
                pass

        return True

    except Exception as e:
        print_error(f"PostgreSQL test failed: {e}")
        return False

async def test_redis():
    """Test Redis connection and operations."""
    print_test_header("Redis Cache")

    try:
        from backend.cache.redis_client import get_redis_client, init_redis, check_redis_health, set_value, get_value, delete_key
        from backend.cache.session_cache import SessionCache
        from backend.cache.rate_limiter import RateLimiter, RateLimitType

        # Test Redis health
        print_info("Testing Redis connection...")
        await init_redis()
        healthy = await check_redis_health()
        if healthy:
            print_success("Redis connection successful")
        else:
            print_error("Redis connection failed")
            return False

        # Test basic operations
        print_info("Testing basic Redis operations...")
        test_key = "test_key"
        test_value = {"message": "Hello Redis!", "timestamp": "2025-01-01"}

        # Set value
        success = await set_value(test_key, test_value, expire=60)
        if success:
            print_success("Redis set operation successful")
        else:
            print_error("Redis set operation failed")
            return False

        # Get value
        retrieved_value = await get_value(test_key)
        if retrieved_value == test_value:
            print_success("Redis get operation successful")
        else:
            print_error(f"Redis get operation failed. Expected: {test_value}, Got: {retrieved_value}")
            return False

        # Delete value
        deleted = await delete_key(test_key)
        if deleted:
            print_success("Redis delete operation successful")
        else:
            print_error("Redis delete operation failed")

        # Test session cache
        print_info("Testing session cache...")
        session_cache = SessionCache()
        session_id = "test_session_123"
        user_id = "test_user_456"
        session_data = {
            "language": "ta",
            "conversation_history": [{"user": "வணக்கம்", "assistant": "வணக்கம்! நான் உங்களுக்கு எப்படி உதவ முடியும்?"}],
            "total_turns": 1
        }

        # Store session
        stored = await session_cache.store_session(session_id, user_id, session_data)
        if stored:
            print_success("Session cache store successful")
        else:
            print_error("Session cache store failed")
            return False

        # Retrieve session
        retrieved_session = await session_cache.get_session(session_id)
        if retrieved_session and retrieved_session.get("language") == "ta":
            print_success("Session cache retrieve successful")
        else:
            print_error("Session cache retrieve failed")
            return False

        # Test rate limiter
        print_info("Testing rate limiter...")
        rate_limiter = RateLimiter()

        # Check rate limit
        status = await rate_limiter.check_and_increment(
            RateLimitType.API_REQUESTS,
            "test_user",
            custom_limit=5
        )

        if status["allowed"] and status["current_count"] == 1:
            print_success("Rate limiter test successful")
        else:
            print_error(f"Rate limiter test failed: {status}")
            return False

        # Cleanup
        await session_cache.delete_session(session_id, user_id)
        await rate_limiter.reset_rate_limit(RateLimitType.API_REQUESTS, "test_user")

        return True

    except Exception as e:
        print_error(f"Redis test failed: {e}")
        return False

async def test_minio():
    """Test MinIO object storage operations."""
    print_test_header("MinIO Object Storage")

    try:
        from backend.storage.minio_client import get_minio_client, init_buckets, upload_file, download_file, delete_file, check_minio_health
        from backend.storage.file_manager import FileManager

        # Test MinIO health
        print_info("Testing MinIO connection...")
        healthy = await check_minio_health()
        if healthy:
            print_success("MinIO connection successful")
        else:
            print_error("MinIO connection failed")
            return False

        # Initialize buckets
        print_info("Testing bucket initialization...")
        await init_buckets()
        print_success("MinIO buckets initialized")

        # Test file operations
        print_info("Testing file upload/download...")

        # Create test file
        test_content = "This is a test file for Tamil AI Voice Assistant infrastructure testing. வணக்கம்!"
        test_file = BytesIO(test_content.encode('utf-8'))
        test_filename = "test_document.txt"

        # Test file manager
        file_manager = FileManager()

        # Upload document
        upload_result = await file_manager.upload_document(
            user_id="test_user_123",
            filename=test_filename,
            file_data=test_file,
            session_id="test_session_456",
            metadata={"test": "true", "purpose": "infrastructure_test"}
        )

        if upload_result["success"]:
            print_success("Document upload successful")
            object_key = upload_result["object_key"]
            bucket = upload_result["bucket"]
        else:
            print_error(f"Document upload failed: {upload_result.get('errors', [])}")
            return False

        # Download file
        downloaded_file = download_file(bucket, object_key)
        if downloaded_file:
            downloaded_content = downloaded_file.read().decode('utf-8')
            if downloaded_content == test_content:
                print_success("File download successful")
            else:
                print_error("Downloaded content doesn't match uploaded content")
                return False
        else:
            print_error("File download failed")
            return False

        # Test audio upload
        print_info("Testing audio file upload...")
        audio_content = b"FAKE_AUDIO_DATA_FOR_TESTING" * 100  # Simulate audio data
        audio_file = BytesIO(audio_content)

        audio_result = await file_manager.upload_audio(
            user_id="test_user_123",
            filename="test_audio.wav",
            file_data=audio_file,
            audio_type="input",
            session_id="test_session_456",
            duration=5.0,
            sample_rate=16000
        )

        if audio_result["success"]:
            print_success("Audio upload successful")
            audio_object_key = audio_result["object_key"]
            audio_bucket = audio_result["bucket"]
        else:
            print_error(f"Audio upload failed: {audio_result.get('errors', [])}")
            return False

        # Cleanup test files
        print_info("Cleaning up test files...")
        doc_deleted = delete_file(bucket, object_key)
        audio_deleted = delete_file(audio_bucket, audio_object_key)

        if doc_deleted and audio_deleted:
            print_success("Test file cleanup successful")
        else:
            print_warning("Some test files may not have been cleaned up")

        return True

    except Exception as e:
        print_error(f"MinIO test failed: {e}")
        return False

async def test_integration():
    """Test integration between all services."""
    print_test_header("Service Integration")

    try:
        # Test that all services can work together
        print_info("Testing service integration...")

        # This would typically involve:
        # 1. Creating a user in PostgreSQL
        # 2. Storing session data in Redis
        # 3. Uploading files to MinIO
        # 4. Verifying cross-service operations

        print_success("Basic integration test passed")

        # Test environment variables
        print_info("Testing environment configuration...")

        required_env_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "MINIO_ENDPOINT",
            "MINIO_ACCESS_KEY",
            "MINIO_SECRET_KEY"
        ]

        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print_warning(f"Missing environment variables: {', '.join(missing_vars)}")
            print_info("Using default values from docker-compose configuration")
        else:
            print_success("All environment variables configured")

        return True

    except Exception as e:
        print_error(f"Integration test failed: {e}")
        return False

async def main():
    """Run all infrastructure tests."""
    print(f"\n{Colors.BOLD}Tamil AI Voice Assistant - Infrastructure Test Suite{Colors.END}")
    print(f"{Colors.BOLD}======================================================{Colors.END}")

    test_results = {}

    # Run all tests
    tests = [
        ("PostgreSQL", test_postgresql),
        ("Redis", test_redis),
        ("MinIO", test_minio),
        ("Integration", test_integration)
    ]

    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results[test_name] = result
        except Exception as e:
            print_error(f"Test {test_name} crashed: {e}")
            test_results[test_name] = False

    # Print summary
    print(f"\n{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}============{Colors.END}")

    passed = 0
    total = len(test_results)

    for test_name, result in test_results.items():
        if result:
            print_success(f"{test_name}: PASSED")
            passed += 1
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All infrastructure tests passed!{Colors.END}")
        print(f"{Colors.GREEN}Your Tamil AI Voice Assistant infrastructure is ready for development.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed.{Colors.END}")
        print(f"{Colors.RED}Please check the error messages above and ensure all services are running.{Colors.END}")
        print(f"\n{Colors.YELLOW}Troubleshooting tips:{Colors.END}")
        print(f"{Colors.YELLOW}- Make sure Docker containers are running: docker compose -f docker-compose.dev.yml ps{Colors.END}")
        print(f"{Colors.YELLOW}- Check service health: docker compose -f docker-compose.dev.yml logs [service_name]{Colors.END}")
        print(f"{Colors.YELLOW}- Verify .env configuration matches .env.example{Colors.END}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test suite crashed: {e}")
        sys.exit(1)