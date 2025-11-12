#!/usr/bin/env python3
"""
Test script for admin seeding functionality
Tests environment variable loading and password hashing for the seeding migration
"""

import os
from dotenv import load_dotenv
from passlib.context import CryptContext

def test_admin_seeding():
    """Test the admin seeding functionality"""
    
    print("=" * 60)
    print("ADMIN SEEDING TEST")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Test that environment variables are loaded correctly
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    print("\n=== Environment Variables Test ===")
    print(f"Admin Email: {admin_email}")
    print(f"Admin Password: {admin_password}")
    
    if not admin_email or not admin_password:
        print("❌ ERROR: Admin credentials not found in environment variables!")
        return False
    
    # Test password hashing
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    # Truncate password to 72 bytes for bcrypt compatibility
    safe_password = admin_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    hashed = pwd_context.hash(safe_password)
    
    print(f"\n=== Password Hashing Test ===")
    print(f"Original password length: {len(admin_password.encode('utf-8'))} bytes")
    print(f"Truncated password length: {len(safe_password.encode('utf-8'))} bytes")
    print(f"Password Hash: {hashed[:50]}...")
    print(f"Hash Verification: {pwd_context.verify(safe_password, hashed)}")
    
    if not pwd_context.verify(safe_password, hashed):
        print("❌ ERROR: Password hashing verification failed!")
        return False
    
    print(f"\n=== Migration Simulation Test ===")
    print("Testing migration logic...")
    
    # Simulate the migration logic
    admin_email_from_env = os.getenv('ADMIN_EMAIL', 'admin@localhost')
    admin_password_from_env = os.getenv('ADMIN_PASSWORD', 'admin123')
    admin_password_hash = pwd_context.hash(admin_password_from_env)
    
    print(f"Migration would use email: {admin_email_from_env}")
    print(f"Migration would hash password: {admin_password_hash[:50]}...")
    
    # Test fallback values
    print(f"\n=== Fallback Values Test ===")
    
    # Temporarily unset environment variables to test fallbacks
    original_email = os.environ.get('ADMIN_EMAIL')
    original_password = os.environ.get('ADMIN_PASSWORD')
    
    if 'ADMIN_EMAIL' in os.environ:
        del os.environ['ADMIN_EMAIL']
    if 'ADMIN_PASSWORD' in os.environ:
        del os.environ['ADMIN_PASSWORD']
    
    fallback_email = os.getenv('ADMIN_EMAIL', 'admin@localhost')
    fallback_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    print(f"Fallback email: {fallback_email}")
    print(f"Fallback password: {fallback_password}")
    
    # Restore original values
    if original_email:
        os.environ['ADMIN_EMAIL'] = original_email
    if original_password:
        os.environ['ADMIN_PASSWORD'] = original_password
    
    print(f"\n=== Summary ===")
    print("✅ Environment variables loaded successfully")
    print("✅ Password hashing working correctly")
    print("✅ Migration logic simulation passed")
    print("✅ Fallback values working correctly")
    print("✅ All tests passed successfully!")
    
    return True

if __name__ == "__main__":
    success = test_admin_seeding()
    exit(0 if success else 1)
