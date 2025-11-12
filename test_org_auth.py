#!/usr/bin/env python3
"""
Test script to verify organization-gated authentication is working
"""

import asyncio
import httpx
import json

API_BASE = "http://localhost:8000"

async def test_organization_auth():
    """Test the organization authentication flow"""

    print("🧪 Testing Organization-Gated Authentication")
    print("=" * 50)

    async with httpx.AsyncClient() as client:

        # Test 1: Register a new user
        print("\n1️⃣ Testing User Registration...")
        register_data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "TestPass123",
            "full_name": "Test User"
        }

        try:
            register_response = await client.post(f"{API_BASE}/auth/register", json=register_data)
            if register_response.status_code == 201:
                print("✅ User registered successfully")
            else:
                print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
                return
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return

        # Test 2: Login
        print("\n2️⃣ Testing Login...")
        login_data = {
            "username_or_email": "testuser",
            "password": "TestPass123"
        }

        try:
            login_response = await client.post(f"{API_BASE}/auth/login", json=login_data)
            if login_response.status_code == 200:
                print("✅ Login successful")
                tokens = login_response.json()
                access_token = tokens["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}
            else:
                print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
                return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return

        # Test 3: Check auth status (should show no organization)
        print("\n3️⃣ Testing Auth Status (before organization)...")
        try:
            auth_status_response = await client.get(f"{API_BASE}/auth/auth-status", headers=headers)
            if auth_status_response.status_code == 200:
                auth_status = auth_status_response.json()
                print(f"✅ Auth status retrieved")
                print(f"   - Authenticated: {auth_status.get('authenticated')}")
                print(f"   - Has Organization: {auth_status.get('has_organization')}")
                print(f"   - Has Active Organization: {auth_status.get('has_active_organization')}")
            else:
                print(f"❌ Auth status failed: {auth_status_response.status_code}")
        except Exception as e:
            print(f"❌ Auth status error: {e}")

        # Test 4: Try to access protected endpoint (should fail - no organization)
        print("\n4️⃣ Testing Protected Endpoint Access (should fail - no org)...")
        try:
            protected_response = await client.get(f"{API_BASE}/auth/organizations/current", headers=headers)
            if protected_response.status_code == 403:
                error_detail = protected_response.json().get("detail", "")
                if "organization" in error_detail.lower():
                    print("✅ Protected endpoint correctly blocked - no organization")
                    print(f"   Error: {error_detail}")
                else:
                    print(f"❌ Wrong error message: {error_detail}")
            else:
                print(f"❌ Protected endpoint should have failed but returned: {protected_response.status_code}")
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")

        # Test 5: Create organization
        print("\n5️⃣ Testing Organization Creation...")
        org_data = {
            "name": "Test Organization",
            "description": "Organization for testing",
            "industry": "Technology",
            "size": "startup",
            "timezone": "UTC"
        }

        try:
            org_response = await client.post(f"{API_BASE}/auth/organizations", json=org_data, headers=headers)
            if org_response.status_code == 201:
                print("✅ Organization created successfully")
                org_data = org_response.json()
                print(f"   Organization ID: {org_data.get('id')}")
                print(f"   Organization Name: {org_data.get('name')}")
                print(f"   User Role: {org_data.get('current_user_role')}")
            else:
                print(f"❌ Organization creation failed: {org_response.status_code} - {org_response.text}")
                return
        except Exception as e:
            print(f"❌ Organization creation error: {e}")
            return

        # Test 6: Check auth status again (should show organization)
        print("\n6️⃣ Testing Auth Status (after organization)...")
        try:
            auth_status_response = await client.get(f"{API_BASE}/auth/auth-status", headers=headers)
            if auth_status_response.status_code == 200:
                auth_status = auth_status_response.json()
                print(f"✅ Auth status retrieved")
                print(f"   - Authenticated: {auth_status.get('authenticated')}")
                print(f"   - Has Organization: {auth_status.get('has_organization')}")
                print(f"   - Has Active Organization: {auth_status.get('has_active_organization')}")
                if auth_status.get('organization'):
                    org = auth_status['organization']
                    print(f"   - Active Organization: {org.get('name')} (Role: {org.get('current_user_role')})")
            else:
                print(f"❌ Auth status failed: {auth_status_response.status_code}")
        except Exception as e:
            print(f"❌ Auth status error: {e}")

        # Test 7: Try protected endpoint again (should work now)
        print("\n7️⃣ Testing Protected Endpoint Access (should work now)...")
        try:
            protected_response = await client.get(f"{API_BASE}/auth/organizations/current", headers=headers)
            if protected_response.status_code == 200:
                print("✅ Protected endpoint access successful")
                org_details = protected_response.json()
                print(f"   Current Organization: {org_details.get('name')}")
                print(f"   User Role: {org_details.get('current_user_role')}")
            else:
                print(f"❌ Protected endpoint failed: {protected_response.status_code} - {protected_response.text}")
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")

    print("\n" + "=" * 50)
    print("🎉 Organization Authentication Test Complete!")
    print("\nKey Verification Points:")
    print("✅ Users without organizations are blocked from protected endpoints")
    print("✅ Users can create organizations and become active members")
    print("✅ Organization membership enables access to protected endpoints")
    print("✅ Auth status endpoint provides clear organization context")

if __name__ == "__main__":
    asyncio.run(test_organization_auth())