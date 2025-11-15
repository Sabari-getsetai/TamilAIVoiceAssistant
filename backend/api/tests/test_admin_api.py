#!/usr/bin/env python3
"""
Admin API Test Script

Tests the admin endpoints:
- POST /admin/upload (file upload)
- POST /admin/ingest (trigger ingestion)
- GET /admin/status/{session_id} (check status)
- GET /admin/documents (list documents)
- GET /admin/stats (vector store stats)
- DELETE /admin/documents/{doc_id} (delete document)

Prerequisites:
1. Start the FastAPI server: python -m uvicorn backend.main:app --reload
2. Run this script: python backend/api/test_admin_api.py
"""
import requests
import time
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("🏥 Testing Health Check")
    print("="*70)

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    print("✅ Health check passed")


def test_upload_documents():
    """Test document upload"""
    print("\n" + "="*70)
    print("📤 Testing Document Upload")
    print("="*70)

    # Create a test document
    test_file = Path("data/docs/test_api.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    test_content = """தமிழ் AI உதவியாளர் சோதனை

இது ஒரு சோதனை ஆவணம். Admin API-ஐ சோதிக்க பயன்படுகிறது.

முக்கிய அம்சங்கள்:
- ஆவணம் பதிவேற்றம்
- உட்பொதிப்பு உருவாக்கம்
- வெக்டர் ஸ்டோர் குறியீட்டு

இது தானியங்கு சோதனைக்கான கோப்பு.
"""

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    print(f"Created test file: {test_file}")

    # Upload file
    with open(test_file, 'rb') as f:
        files = {'files': (test_file.name, f, 'text/plain')}
        response = requests.post(f"{BASE_URL}/admin/upload", files=files)

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    assert response.status_code == 200
    assert data['success'] == True
    print("✅ Document upload passed")

    return data['files'][0]['path']


def test_ingest_documents(file_path):
    """Test document ingestion"""
    print("\n" + "="*70)
    print("🔄 Testing Document Ingestion")
    print("="*70)

    payload = {
        "file_paths": [file_path],
        "vector_store_name": "test_admin"
    }

    response = requests.post(
        f"{BASE_URL}/admin/ingest",
        json=payload
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    assert response.status_code == 200
    assert data['success'] == True
    print("✅ Document ingestion started")

    return data['session_id']


def test_check_status(session_id):
    """Test status checking"""
    print("\n" + "="*70)
    print("📊 Testing Status Check")
    print("="*70)

    # Poll status until complete
    max_attempts = 30
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/admin/status/{session_id}")

        print(f"\nAttempt {attempt + 1}/{max_attempts}")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Ingestion status: {data['status']}")

        if data['status'] in ['completed', 'failed']:
            print(f"\nFinal Response: {json.dumps(data, indent=2)}")

            if data['status'] == 'completed':
                print("✅ Ingestion completed successfully")
                return True
            else:
                print(f"❌ Ingestion failed: {data.get('error')}")
                return False

        time.sleep(2)  # Wait 2 seconds before next check

    print("⚠️  Ingestion timed out")
    return False


def test_list_documents():
    """Test listing documents"""
    print("\n" + "="*70)
    print("📋 Testing Document Listing")
    print("="*70)

    response = requests.get(f"{BASE_URL}/admin/documents?vector_store_name=test_admin")

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total documents: {data['total']}")

    if data['documents']:
        print(f"\nFirst document:")
        print(f"  ID: {data['documents'][0]['id']}")
        print(f"  Preview: {data['documents'][0]['text_preview'][:100]}...")

    assert response.status_code == 200
    print("✅ Document listing passed")

    return data['documents']


def test_get_stats():
    """Test getting vector store stats"""
    print("\n" + "="*70)
    print("📈 Testing Vector Store Stats")
    print("="*70)

    response = requests.get(f"{BASE_URL}/admin/stats?vector_store_name=test_admin")

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    assert response.status_code == 200
    print("✅ Stats retrieval passed")


def test_delete_document(doc_id):
    """Test document deletion"""
    print("\n" + "="*70)
    print("🗑️  Testing Document Deletion")
    print("="*70)

    response = requests.delete(
        f"{BASE_URL}/admin/documents/{doc_id}?vector_store_name=test_admin"
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    assert response.status_code == 200
    assert data['success'] == True
    print("✅ Document deletion passed")


def main():
    """Run all tests"""
    print("="*70)
    print("🧪 Tamil AI Voice Assistant - Admin API Tests")
    print("="*70)
    print("\nℹ️  Make sure the FastAPI server is running:")
    print("   python -m uvicorn backend.main:app --reload")
    print()

    try:
        # Test 1: Health check
        test_health_check()

        # Test 2: Upload documents
        file_path = test_upload_documents()

        # Test 3: Trigger ingestion
        session_id = test_ingest_documents(file_path)

        # Test 4: Check status (wait for completion)
        success = test_check_status(session_id)

        if not success:
            print("\n❌ Ingestion failed, skipping remaining tests")
            return False

        # Test 5: List documents
        documents = test_list_documents()

        # Test 6: Get stats
        test_get_stats()

        # Test 7: Delete a document (if any exist)
        if documents:
            test_delete_document(documents[0]['id'])

        # Summary
        print("\n" + "="*70)
        print("✅ All Admin API Tests Passed!")
        print("="*70)

        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("   Make sure FastAPI is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
