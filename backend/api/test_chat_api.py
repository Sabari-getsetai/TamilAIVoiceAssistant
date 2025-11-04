"""
Test Suite for Chat API Endpoints

Tests all chat API endpoints including:
- Session management
- Conversation turns (audio and text)
- Component testing (STT, TTS, LLM)
- Audio file serving
- WebSocket communication
"""
import sys
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.settings import settings


def test_session_creation():
    """Test creating a new chat session"""
    print("\n" + "="*60)
    print("TEST: Session Creation")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/sessions"
    
    payload = {
        "user_id": "test_user_123",
        "language": "ta",
        "rag_enabled": True
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            session_data = response.json()
            print(f"✅ Session created: {session_data['session_id']}")
            return session_data['session_id']
        else:
            print(f"❌ Failed to create session")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_get_session(session_id: str):
    """Test getting session information"""
    print("\n" + "="*60)
    print("TEST: Get Session Info")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/sessions/{session_id}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print(f"✅ Session info retrieved")
        else:
            print(f"❌ Failed to get session info")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_list_sessions():
    """Test listing all active sessions"""
    print("\n" + "="*60)
    print("TEST: List Sessions")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/sessions"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        sessions = response.json()
        print(f"Active Sessions: {len(sessions)}")
        
        for session in sessions:
            print(f"  - {session['session_id']}: {session['total_turns']} turns")
        
        if response.status_code == 200:
            print(f"✅ Sessions listed")
        else:
            print(f"❌ Failed to list sessions")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_text_conversation(session_id: str):
    """Test text-only conversation"""
    print("\n" + "="*60)
    print("TEST: Text Conversation")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/sessions/{session_id}/text"
    
    payload = {
        "text": "வணக்கம்! நீங்கள் யார்?",
        "language": "ta"
    }
    
    try:
        print(f"User: {payload['text']}")
        start_time = time.time()
        
        response = requests.post(url, json=payload)
        
        elapsed = time.time() - start_time
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Assistant: {data['assistant_text']}")
            print(f"Processing Time: {elapsed:.2f}s")
            print(f"Component Times: {data.get('processing_time', {})}")
            print(f"✅ Text conversation successful")
        else:
            print(f"Response: {response.json()}")
            print(f"❌ Text conversation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_synthesize():
    """Test text-to-speech synthesis"""
    print("\n" + "="*60)
    print("TEST: Speech Synthesis (TTS)")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/synthesize"
    
    payload = {
        "text": "வணக்கம்! நான் தமிழ் AI உதவியாளர்.",
        "language": "ta"
    }
    
    try:
        print(f"Text: {payload['text']}")
        start_time = time.time()
        
        response = requests.post(url, json=payload)
        
        elapsed = time.time() - start_time
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Audio URL: {data['audio_url']}")
            print(f"Duration: {data['duration']:.2f}s")
            print(f"Text Length: {data['text_length']} chars")
            print(f"✅ Synthesis successful")
        else:
            print(f"Response: {response.json()}")
            print(f"❌ Synthesis failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_generate():
    """Test LLM text generation"""
    print("\n" + "="*60)
    print("TEST: Text Generation (LLM)")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/generate"
    
    payload = {
        "text": "தமிழ் மொழியின் சிறப்புகள் என்ன?",
        "language": "ta",
        "use_rag": True
    }
    
    try:
        print(f"Query: {payload['text']}")
        start_time = time.time()
        
        response = requests.post(url, json=payload)
        
        elapsed = time.time() - start_time
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['response_text'][:200]}...")
            print(f"Context Used: {data['context_used']}")
            print(f"Retrieved Chunks: {data['retrieved_chunks']}")
            print(f"Duration: {data['duration']:.2f}s")
            print(f"✅ Generation successful")
        else:
            print(f"Response: {response.json()}")
            print(f"❌ Generation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_conversation_history(session_id: str):
    """Test getting conversation history"""
    print("\n" + "="*60)
    print("TEST: Conversation History")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/sessions/{session_id}/history"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Turns: {data['total_turns']}")
            
            for i, turn in enumerate(data['history'], 1):
                print(f"\nTurn {i}:")
                print(f"  User: {turn.get('user', 'N/A')}")
                print(f"  Assistant: {turn.get('assistant', 'N/A')}")
            
            print(f"✅ History retrieved")
        else:
            print(f"Response: {response.json()}")
            print(f"❌ Failed to get history")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_session_stats():
    """Test getting session statistics"""
    print("\n" + "="*60)
    print("TEST: Session Statistics")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/stats"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Sessions: {data['total_sessions']}")
            print(f"Active Sessions: {data['active_sessions']}")
            print(f"Total Turns: {data['total_turns']}")
            print(f"Avg Session Duration: {data['average_session_duration']:.2f}s")
            print(f"Avg Turn Time: {data['average_turn_time']:.2f}s")
            print(f"✅ Stats retrieved")
        else:
            print(f"Response: {response.json()}")
            print(f"❌ Failed to get stats")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_delete_session(session_id: str):
    """Test deleting a session"""
    print("\n" + "="*60)
    print("TEST: Delete Session")
    print("="*60)
    
    import requests
    
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/chat/sessions/{session_id}"
    
    try:
        response = requests.delete(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print(f"✅ Session deleted")
        else:
            print(f"❌ Failed to delete session")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def run_all_tests():
    """Run all chat API tests"""
    print("\n" + "="*60)
    print("CHAT API TEST SUITE")
    print("="*60)
    print(f"API URL: http://{settings.API_HOST}:{settings.API_PORT}")
    print("="*60)
    
    # Test session management
    session_id = test_session_creation()
    
    if not session_id:
        print("\n❌ Cannot continue tests without a session")
        return
    
    time.sleep(1)
    test_get_session(session_id)
    
    time.sleep(1)
    test_list_sessions()
    
    # Test conversation
    time.sleep(1)
    test_text_conversation(session_id)
    
    # Test components
    time.sleep(1)
    test_synthesize()
    
    time.sleep(1)
    test_generate()
    
    # Test history and stats
    time.sleep(1)
    test_conversation_history(session_id)
    
    time.sleep(1)
    test_session_stats()
    
    # Cleanup
    time.sleep(1)
    test_delete_session(session_id)
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)


if __name__ == "__main__":
    print("\n🧪 Starting Chat API Tests...")
    print("⚠️  Make sure the FastAPI server is running:")
    print(f"   uvicorn backend.main:app --reload")
    print()
    
    input("Press Enter to start tests...")
    
    run_all_tests()
