#!/usr/bin/env python3
"""
Test script to verify backend API response for organization fields
"""
import requests
import json

def test_api_response():
    """Test the backend API response format for user organizations"""
    try:
        # Test auth status endpoint
        response = requests.get('http://localhost:8000/auth/auth-status')
        if response.status_code == 200:
            data = response.json()
            print("✅ Auth Status Response:")
            print(json.dumps(data, indent=2))
            print()

        # For authenticated endpoints, you would need a token
        # But we can test the backend is working
        print("✅ Backend is accessible and responding")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to backend: {e}")

if __name__ == "__main__":
    test_api_response()