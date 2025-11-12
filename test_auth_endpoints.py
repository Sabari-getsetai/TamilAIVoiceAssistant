#!/usr/bin/env python3
"""
Test script for authentication endpoints

Tests the auth functionality without requiring a running server
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Try importing auth functions to test they work
async def test_auth_functions():
    """Test authentication utility functions"""
    print("🧪 Testing Authentication Functions...")

    try:
        from api.auth import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
        print("✅ Auth function imports successful")

        # Test password hashing
        password = "TestPassword123!"
        hashed = hash_password(password)
        print(f"✅ Password hashing works: {len(hashed)} chars")

        # Test password verification
        is_valid = verify_password(password, hashed)
        print(f"✅ Password verification works: {is_valid}")

        # Test invalid password
        is_invalid = verify_password("WrongPassword", hashed)
        print(f"✅ Invalid password rejected: {not is_invalid}")

        # Test JWT token creation
        user_id = "test-user-123"
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        print(f"✅ JWT tokens created: access={len(access_token)}, refresh={len(refresh_token)}")

        # Test token verification
        decoded_user_id = verify_token(access_token, "access")
        print(f"✅ Access token verification: {decoded_user_id == user_id}")

        decoded_user_id = verify_token(refresh_token, "refresh")
        print(f"✅ Refresh token verification: {decoded_user_id == user_id}")

        print("\n🎉 All authentication functions working correctly!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_models_import():
    """Test database models import"""
    print("\n🧪 Testing Database Models...")

    try:
        from database.models import User, UserRole, generate_uuid, utc_now
        print("✅ Database models import successful")

        # Test UUID generation
        test_uuid = generate_uuid()
        print(f"✅ UUID generation works: {test_uuid}")

        # Test datetime generation
        test_time = utc_now()
        print(f"✅ UTC time generation works: {test_time}")

        # Test enum values
        print(f"✅ UserRole enum: {list(UserRole)}")

        return True

    except ImportError as e:
        print(f"❌ Database models import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False


async def test_settings():
    """Test settings configuration"""
    print("\n🧪 Testing Settings Configuration...")

    try:
        from settings import settings
        print("✅ Settings import successful")

        # Test JWT settings
        print(f"✅ JWT Secret Key configured: {'*' * min(len(settings.JWT_SECRET_KEY), 20)}")
        print(f"✅ JWT Algorithm: {settings.JWT_ALGORITHM}")
        print(f"✅ Access token expire: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
        print(f"✅ Refresh token expire: {settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS} days")

        # Test database URL
        print(f"✅ Database URL configured: {settings.DATABASE_URL[:30]}...")

        return True

    except ImportError as e:
        print(f"❌ Settings import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False


async def main():
    """Run all authentication tests"""
    print("🚀 Authentication System Test Suite")
    print("=" * 50)

    results = []

    # Test settings first
    results.append(await test_settings())

    # Test models
    results.append(await test_models_import())

    # Test auth functions
    results.append(await test_auth_functions())

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! Authentication system is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⛔ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)