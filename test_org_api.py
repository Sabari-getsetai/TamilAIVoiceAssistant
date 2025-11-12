#!/usr/bin/env python3
import requests
import json

# Test organization API endpoints
BASE_URL = "http://localhost:8000"

def test_organization_api():
    print("Testing Organization API...")
    
    # 1. Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "username": "orgtest4",
        "email": "orgtest4@example.com", 
        "password": "TestPass123",
        "full_name": "Org Test User 4"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✅ User registered successfully")
        elif "already exists" in response.text:
            print("ℹ️  User already exists, continuing...")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    # 2. Login to get token
    print("\n2. Logging in...")
    login_data = {
        "username_or_email": "orgtest4",
        "password": "TestPass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create organization
    print("\n3. Creating organization...")
    org_data = {
        "name": "Test Organization API",
        "description": "Testing organization creation with enum serialization",
        "industry": "Technology",
        "size": "startup"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/organizations/", json=org_data, headers=headers)
        if response.status_code == 201:
            org = response.json()
            print("✅ Organization created successfully")
            print(f"   ID: {org['id']}")
            print(f"   Name: {org['name']}")
            print(f"   User Role: {org['user_role']}")  # This should be a string, not enum object
            print(f"   Member Count: {org['member_count']}")
            org_id = org['id']
        else:
            print(f"❌ Organization creation failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Organization creation error: {e}")
        return
    
    # 4. List organizations
    print("\n4. Listing organizations...")
    try:
        response = requests.get(f"{BASE_URL}/organizations/", headers=headers)
        if response.status_code == 200:
            orgs = response.json()
            print(f"✅ Found {len(orgs)} organizations")
            for org in orgs:
                print(f"   - {org['name']} (Role: {org['user_role']})")  # Should be string
        else:
            print(f"❌ List organizations failed: {response.text}")
    except Exception as e:
        print(f"❌ List organizations error: {e}")
    
    # 5. Get organization details
    print("\n5. Getting organization details...")
    try:
        response = requests.get(f"{BASE_URL}/organizations/{org_id}", headers=headers)
        if response.status_code == 200:
            org = response.json()
            print("✅ Organization details retrieved")
            print(f"   User Role: {org['user_role']}")  # Should be string
            print(f"   Member Count: {org['member_count']}")
        else:
            print(f"❌ Get organization failed: {response.text}")
    except Exception as e:
        print(f"❌ Get organization error: {e}")
    
    # 6. Test organization switching
    print("\n6. Testing organization switching...")
    try:
        response = requests.post(f"{BASE_URL}/organizations/{org_id}/switch", headers=headers)
        if response.status_code == 200:
            print("✅ Organization switch successful")
        else:
            print(f"❌ Organization switch failed: {response.text}")
    except Exception as e:
        print(f"❌ Organization switch error: {e}")
    
    print("\n🎉 Organization API testing completed!")

if __name__ == "__main__":
    test_organization_api()
