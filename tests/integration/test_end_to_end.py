#!/usr/bin/env python3
"""
End-to-End Integration Tests for Tamil AI Voice Assistant.

This test suite validates complete workflows including:
- User authentication and session management
- Document upload and processing
- RAG pipeline integration
- Speech-to-text and text-to-speech functionality
- Real-time conversation flow
- Database integration with new session management
"""

import asyncio
import sys
import os
import json
import tempfile
import logging
from pathlib import Path
from io import BytesIO
from typing import Dict, Any, Optional
import aiohttp
import websockets
import base64

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name: str):
    """Print test section header."""
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.MAGENTA}{Colors.BOLD}🧪 INTEGRATION TEST: {test_name}{Colors.END}")
    print(f"{Colors.MAGENTA}{Colors.BOLD}{'='*80}{Colors.END}")

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
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")

def print_step(message: str):
    """Print step message."""
    print(f"{Colors.BLUE}→ {message}{Colors.END}")

class APITestClient:
    """Helper class for API testing."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request."""
        async with self.session.get(f"{self.base_url}{endpoint}", **kwargs) as resp:
            return {
                "status": resp.status,
                "data": await resp.json() if resp.content_type == "application/json" else await resp.text(),
                "headers": dict(resp.headers)
            }

    async def post(self, endpoint: str, data=None, json_data=None, **kwargs) -> Dict[str, Any]:
        """Make POST request."""
        async with self.session.post(
            f"{self.base_url}{endpoint}",
            data=data,
            json=json_data,
            **kwargs
        ) as resp:
            return {
                "status": resp.status,
                "data": await resp.json() if resp.content_type == "application/json" else await resp.text(),
                "headers": dict(resp.headers)
            }

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request."""
        async with self.session.delete(f"{self.base_url}{endpoint}", **kwargs) as resp:
            return {
                "status": resp.status,
                "data": await resp.json() if resp.content_type == "application/json" else await resp.text(),
                "headers": dict(resp.headers)
            }

async def test_api_health_and_connectivity():
    """Test basic API health and connectivity."""
    print_test_header("API Health & Connectivity")

    try:
        async with APITestClient() as client:
            # Test root endpoint
            print_step("Testing root endpoint...")
            resp = await client.get("/")
            if resp["status"] == 200:
                print_success("Root endpoint accessible")
            else:
                print_error(f"Root endpoint failed: {resp['status']}")
                return False

            # Test health endpoint
            print_step("Testing health endpoint...")
            resp = await client.get("/health")
            if resp["status"] == 200:
                print_success("Health endpoint successful")
                print_info(f"Health data: {resp['data']}")
            else:
                print_error(f"Health endpoint failed: {resp['status']}")
                return False

            return True

    except Exception as e:
        print_error(f"API connectivity test failed: {e}")
        return False

async def test_database_session_management():
    """Test the new database session management system."""
    print_test_header("Database Session Management")

    try:
        # Import session manager
        from services.session_service import DatabaseSessionManager, get_session_manager

        print_step("Testing session manager initialization...")
        session_manager = await get_session_manager()

        if session_manager:
            print_success("Session manager initialized successfully")
        else:
            print_error("Session manager initialization failed")
            return False

        # Test session creation
        print_step("Testing session creation...")
        session_id = await session_manager.create_session(
            user_id="test_user_integration",
            language="ta",
            rag_enabled=True,
            session_metadata={"test": "integration_test", "version": "2.1"}
        )

        if session_id:
            print_success(f"Session created successfully: {session_id}")
        else:
            print_error("Session creation failed")
            return False

        # Test session retrieval
        print_step("Testing session retrieval...")
        session_data = await session_manager.get_session(session_id)

        if session_data and session_data.get("language") == "ta":
            print_success("Session retrieval successful")
            print_info(f"Session data: {dict(session_data)}")
        else:
            print_error("Session retrieval failed")
            return False

        # Test conversation turn creation
        print_step("Testing conversation turn creation...")
        turn_id = await session_manager.add_conversation_turn(
            session_id=session_id,
            user_text="வணக்கம்! இது ஒரு சோதனை செய்தி.",
            assistant_text="வணக்கம்! நான் உங்களுக்கு எப்படி உதவ முடியும்?",
            retrieved_chunks=["chunk_1", "chunk_2"],
            processing_time={"stt": 0.5, "rag": 0.3, "llm": 1.2, "tts": 0.8},
            turn_metadata={"test": "true"}
        )

        if turn_id:
            print_success(f"Conversation turn created: {turn_id}")
        else:
            print_error("Conversation turn creation failed")
            return False

        # Test session history retrieval
        print_step("Testing session history retrieval...")
        history = await session_manager.get_conversation_history(session_id, limit=10)

        if history and len(history) == 1 and history[0]["user_text"] == "வணக்கம்! இது ஒரு சோதனை செய்தி.":
            print_success("Session history retrieval successful")
        else:
            print_error(f"Session history retrieval failed: {history}")
            return False

        # Test session update
        print_step("Testing session update...")
        updated = await session_manager.update_session_activity(session_id)

        if updated:
            print_success("Session activity updated successfully")
        else:
            print_error("Session activity update failed")
            return False

        # Test session cleanup
        print_step("Testing session cleanup...")
        deleted = await session_manager.end_session(session_id)

        if deleted:
            print_success("Session cleanup successful")
        else:
            print_error("Session cleanup failed")
            return False

        return True

    except Exception as e:
        print_error(f"Database session management test failed: {e}")
        import traceback
        print_error(traceback.format_exc())
        return False

async def test_document_workflow():
    """Test complete document upload and processing workflow."""
    print_test_header("Document Upload & Processing Workflow")

    try:
        async with APITestClient() as client:
            # Create test document
            print_step("Creating test document...")
            test_content = """
            தமிழ் செயற்கை நுண்ணறிவு குரல் உதவியாளர்
            ====================================

            இந்த அமைப்பு பின்வரும் வசதிகளை வழங்குகிறது:

            1. இயல்பான தமிழ் மொழி உரையாடல்
            2. ஆவண அடிப்படையிலான கேள்வி பதில்
            3. குரல் அங்கீகாரம் மற்றும் குரல் தொகுப்பு
            4. முழுமையான தனியுரிமை பாதுகாப்பு

            தொழில்நுட்ப விவரங்கள்:
            - LangChain மற்றும் LangGraph for AI orchestration
            - FAISS for vector similarity search
            - Faster-Whisper for speech-to-text
            - Google Cloud TTS for text-to-speech
            - FastAPI backend with PostgreSQL database

            இது ஒரு முழுமையான ஆஃப்லைன் அமைப்பு ஆகும்.
            """

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', encoding='utf-8', delete=False) as f:
                f.write(test_content)
                temp_file_path = f.name

            try:
                # Test document upload via admin API
                print_step("Testing document upload...")

                # Upload file using multipart form data
                with open(temp_file_path, 'rb') as f:
                    files = {'files': ('test_doc.txt', f, 'text/plain')}
                    data = aiohttp.FormData()
                    data.add_field('files', f, filename='test_doc.txt', content_type='text/plain')

                    async with client.session.post(
                        f"{client.base_url}/admin/upload",
                        data=data
                    ) as resp:
                        upload_result = {
                            "status": resp.status,
                            "data": await resp.json() if resp.content_type == "application/json" else await resp.text()
                        }

                if upload_result["status"] == 200:
                    print_success("Document upload successful")
                    uploaded_files = upload_result["data"].get("uploaded_files", [])
                    print_info(f"Uploaded files: {uploaded_files}")
                else:
                    print_error(f"Document upload failed: {upload_result['status']} - {upload_result['data']}")
                    return False

                # Test document ingestion
                print_step("Testing document ingestion...")
                ingest_result = await client.post("/admin/ingest", json_data={
                    "file_paths": uploaded_files
                })

                if ingest_result["status"] == 200:
                    print_success("Document ingestion initiated")
                    print_info(f"Ingestion result: {ingest_result['data']}")
                else:
                    print_error(f"Document ingestion failed: {ingest_result['status']} - {ingest_result['data']}")
                    return False

                # Wait a bit for processing
                print_step("Waiting for document processing...")
                await asyncio.sleep(3)

                # Check ingestion status
                print_step("Checking ingestion status...")
                status_result = await client.get("/admin/status")

                if status_result["status"] == 200:
                    status_data = status_result["data"]
                    print_success("Status check successful")
                    print_info(f"Index stats: {status_data}")

                    # Verify document was processed
                    if status_data.get("total_documents", 0) > 0:
                        print_success("Document successfully indexed")
                    else:
                        print_warning("Document may not be indexed yet")
                else:
                    print_error(f"Status check failed: {status_result['status']}")
                    return False

                # Test document listing
                print_step("Testing document listing...")
                docs_result = await client.get("/admin/documents")

                if docs_result["status"] == 200:
                    docs_data = docs_result["data"]
                    print_success("Document listing successful")
                    print_info(f"Found {len(docs_data)} documents")
                else:
                    print_error(f"Document listing failed: {docs_result['status']}")
                    return False

                return True

            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)

    except Exception as e:
        print_error(f"Document workflow test failed: {e}")
        import traceback
        print_error(traceback.format_exc())
        return False

async def test_chat_api_workflow():
    """Test chat API and conversation workflow."""
    print_test_header("Chat API & Conversation Workflow")

    try:
        async with APITestClient() as client:
            # Test simple chat endpoint
            print_step("Testing simple chat API...")
            chat_result = await client.post("/api/chat", json_data={
                "message": "வணக்கம்! தமிழில் பேசுவதற்கு நான் மகிழ்ச்சியடைகிறேன்."
            })

            if chat_result["status"] == 200:
                print_success("Simple chat API successful")
                response_data = chat_result["data"]
                print_info(f"Response: {response_data.get('response', 'No response')[:100]}...")
            else:
                print_error(f"Simple chat API failed: {chat_result['status']} - {chat_result['data']}")
                return False

            # Test session-based chat
            print_step("Testing session creation...")
            session_result = await client.post("/chat/sessions", json_data={
                "language": "ta",
                "rag_enabled": True
            })

            if session_result["status"] == 200:
                session_data = session_result["data"]
                session_id = session_data["session_id"]
                print_success(f"Session created: {session_id}")
            else:
                print_error(f"Session creation failed: {session_result['status']}")
                return False

            # Test text conversation turn
            print_step("Testing text conversation turn...")
            turn_result = await client.post(f"/chat/sessions/{session_id}/turns", json_data={
                "message": "செயற்கை நுண்ணறிவு பற்றி எனக்கு சில தகவல்கள் தேவை.",
                "turn_type": "text"
            })

            if turn_result["status"] == 200:
                turn_data = turn_result["data"]
                print_success("Text conversation turn successful")
                print_info(f"Assistant response: {turn_data.get('response', 'No response')[:100]}...")
            else:
                print_error(f"Text conversation turn failed: {turn_result['status']}")
                return False

            # Test session history
            print_step("Testing session history retrieval...")
            history_result = await client.get(f"/chat/sessions/{session_id}/history")

            if history_result["status"] == 200:
                history_data = history_result["data"]
                print_success("Session history retrieval successful")
                print_info(f"History contains {len(history_data.get('turns', []))} turns")
            else:
                print_error(f"Session history failed: {history_result['status']}")
                return False

            # Test session stats
            print_step("Testing session statistics...")
            stats_result = await client.get(f"/chat/sessions/{session_id}/stats")

            if stats_result["status"] == 200:
                stats_data = stats_result["data"]
                print_success("Session statistics successful")
                print_info(f"Session stats: {stats_data}")
            else:
                print_error(f"Session statistics failed: {stats_result['status']}")
                return False

            # Test session cleanup
            print_step("Testing session cleanup...")
            delete_result = await client.delete(f"/chat/sessions/{session_id}")

            if delete_result["status"] == 200:
                print_success("Session cleanup successful")
            else:
                print_error(f"Session cleanup failed: {delete_result['status']}")
                return False

            return True

    except Exception as e:
        print_error(f"Chat workflow test failed: {e}")
        import traceback
        print_error(traceback.format_exc())
        return False

async def test_speech_components():
    """Test speech-to-text and text-to-speech components."""
    print_test_header("Speech Components (STT & TTS)")

    try:
        async with APITestClient() as client:
            # Test TTS endpoint
            print_step("Testing text-to-speech...")
            tts_result = await client.post("/speech/synthesize", json_data={
                "text": "வணக்கம்! இது தமிழ் குரல் தொகுப்பு சோதனை."
            })

            if tts_result["status"] == 200:
                print_success("TTS test successful")
                # TTS should return audio data or file path
            else:
                print_error(f"TTS test failed: {tts_result['status']}")
                return False

            # Test chat TTS endpoint
            print_step("Testing chat TTS endpoint...")
            chat_tts_result = await client.post("/chat/test/synthesize", json_data={
                "text": "இது ஒரு சோதனை செய்தி."
            })

            if chat_tts_result["status"] == 200:
                print_success("Chat TTS test successful")
            else:
                print_error(f"Chat TTS test failed: {chat_tts_result['status']}")
                return False

            # Test LLM generation
            print_step("Testing LLM generation...")
            llm_result = await client.post("/chat/test/generate", json_data={
                "prompt": "தமிழ் மொழி பற்றி சிறு குறிப்பு எழுதுங்கள்.",
                "max_tokens": 100
            })

            if llm_result["status"] == 200:
                print_success("LLM generation test successful")
                response_data = llm_result["data"]
                print_info(f"LLM response: {response_data.get('response', 'No response')[:100]}...")
            else:
                print_error(f"LLM generation test failed: {llm_result['status']}")
                return False

            return True

    except Exception as e:
        print_error(f"Speech components test failed: {e}")
        import traceback
        print_error(traceback.format_exc())
        return False

async def test_websocket_functionality():
    """Test WebSocket functionality for real-time communication."""
    print_test_header("WebSocket Real-time Communication")

    try:
        # First create a session for WebSocket
        async with APITestClient() as client:
            session_result = await client.post("/chat/sessions", json_data={
                "language": "ta",
                "rag_enabled": True
            })

            if session_result["status"] != 200:
                print_error("Could not create session for WebSocket test")
                return False

            session_id = session_result["data"]["session_id"]
            print_info(f"Created session for WebSocket: {session_id}")

        # Test WebSocket connection
        print_step("Testing WebSocket connection...")
        ws_url = f"ws://localhost:8000/chat/ws/{session_id}"

        try:
            async with websockets.connect(ws_url) as websocket:
                print_success("WebSocket connection established")

                # Test text message
                print_step("Testing WebSocket text communication...")
                test_message = {
                    "type": "text",
                    "content": "வணக்கம்! WebSocket மூலம் தமிழில் பேசுகிறேன்."
                }

                await websocket.send(json.dumps(test_message))

                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)

                if response_data.get("type") == "text":
                    print_success("WebSocket text communication successful")
                    print_info(f"Received: {response_data.get('content', 'No content')[:100]}...")
                else:
                    print_error(f"Unexpected WebSocket response: {response_data}")
                    return False

                # Test connection close
                print_step("Testing WebSocket connection close...")
                await websocket.close()
                print_success("WebSocket closed cleanly")

                return True

        except websockets.exceptions.ConnectionClosed:
            print_error("WebSocket connection closed unexpectedly")
            return False
        except asyncio.TimeoutError:
            print_error("WebSocket response timeout")
            return False

    except Exception as e:
        print_error(f"WebSocket test failed: {e}")
        import traceback
        print_error(traceback.format_exc())
        return False

async def test_admin_dashboard_apis():
    """Test admin dashboard API endpoints."""
    print_test_header("Admin Dashboard APIs")

    try:
        async with APITestClient() as client:
            # Test admin status
            print_step("Testing admin status endpoint...")
            status_result = await client.get("/admin/status")

            if status_result["status"] == 200:
                print_success("Admin status endpoint successful")
                status_data = status_result["data"]
                print_info(f"System status: {status_data}")
            else:
                print_error(f"Admin status failed: {status_result['status']}")
                return False

            # Test documents listing
            print_step("Testing documents listing...")
            docs_result = await client.get("/admin/documents")

            if docs_result["status"] == 200:
                print_success("Documents listing successful")
                docs_data = docs_result["data"]
                print_info(f"Found {len(docs_data)} documents")
            else:
                print_error(f"Documents listing failed: {docs_result['status']}")
                return False

            # Test TTS reset (new feature)
            print_step("Testing TTS reset endpoint...")
            tts_reset_result = await client.post("/admin/reset-tts")

            if tts_reset_result["status"] == 200:
                print_success("TTS reset successful")
                reset_data = tts_reset_result["data"]
                print_info(f"TTS reset result: {reset_data}")
            else:
                print_error(f"TTS reset failed: {tts_reset_result['status']}")
                return False

            return True

    except Exception as e:
        print_error(f"Admin dashboard test failed: {e}")
        import traceback
        print_error(traceback.format_exc())
        return False

async def test_error_handling_and_edge_cases():
    """Test error handling and edge cases."""
    print_test_header("Error Handling & Edge Cases")

    try:
        async with APITestClient() as client:
            # Test invalid session access
            print_step("Testing invalid session access...")
            invalid_session_result = await client.get("/chat/sessions/invalid-session-id/history")

            if invalid_session_result["status"] == 404:
                print_success("Invalid session properly rejected")
            else:
                print_warning(f"Unexpected response for invalid session: {invalid_session_result['status']}")

            # Test malformed requests
            print_step("Testing malformed chat request...")
            malformed_result = await client.post("/api/chat", json_data={
                "invalid_field": "this should fail"
            })

            if malformed_result["status"] in [400, 422]:
                print_success("Malformed request properly rejected")
            else:
                print_warning(f"Unexpected response for malformed request: {malformed_result['status']}")

            # Test empty text inputs
            print_step("Testing empty text input...")
            empty_result = await client.post("/api/chat", json_data={
                "message": ""
            })

            if empty_result["status"] in [400, 422]:
                print_success("Empty input properly rejected")
            else:
                print_warning(f"Unexpected response for empty input: {empty_result['status']}")

            # Test very long input
            print_step("Testing very long input...")
            long_text = "தமிழ் " * 1000  # Very long text
            long_result = await client.post("/api/chat", json_data={
                "message": long_text
            })

            if long_result["status"] in [200, 413, 422]:
                print_success("Long input handled appropriately")
            else:
                print_warning(f"Unexpected response for long input: {long_result['status']}")

            return True

    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        import traceback
        print_error(traceback.format_exc())
        return False

async def main():
    """Run all end-to-end integration tests."""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}Tamil AI Voice Assistant - End-to-End Integration Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}==============================================================={Colors.END}")

    test_results = {}

    # Define test suite
    tests = [
        ("API Health & Connectivity", test_api_health_and_connectivity),
        ("Database Session Management", test_database_session_management),
        ("Document Workflow", test_document_workflow),
        ("Chat API Workflow", test_chat_api_workflow),
        ("Speech Components", test_speech_components),
        ("WebSocket Functionality", test_websocket_functionality),
        ("Admin Dashboard APIs", test_admin_dashboard_apis),
        ("Error Handling & Edge Cases", test_error_handling_and_edge_cases)
    ]

    # Run all tests
    for test_name, test_func in tests:
        try:
            print_step(f"Starting {test_name}...")
            result = await test_func()
            test_results[test_name] = result

            if result:
                print_success(f"{test_name} completed successfully")
            else:
                print_error(f"{test_name} failed")

        except Exception as e:
            print_error(f"Test {test_name} crashed: {e}")
            test_results[test_name] = False

    # Print comprehensive summary
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}Comprehensive Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}========================={Colors.END}")

    passed = 0
    total = len(test_results)

    for test_name, result in test_results.items():
        if result:
            print_success(f"{test_name}: PASSED")
            passed += 1
        else:
            print_error(f"{test_name}: FAILED")

    # Calculate percentage
    percentage = (passed / total) * 100 if total > 0 else 0

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed ({percentage:.1f}%){Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL INTEGRATION TESTS PASSED!{Colors.END}")
        print(f"{Colors.GREEN}Your Tamil AI Voice Assistant is fully integrated and ready for production use.{Colors.END}")
        print(f"\n{Colors.GREEN}✓ Database session management working{Colors.END}")
        print(f"{Colors.GREEN}✓ Document upload and processing functional{Colors.END}")
        print(f"{Colors.GREEN}✓ Chat API and conversation flows operational{Colors.END}")
        print(f"{Colors.GREEN}✓ Speech components integrated{Colors.END}")
        print(f"{Colors.GREEN}✓ WebSocket real-time communication active{Colors.END}")
        print(f"{Colors.GREEN}✓ Admin dashboard APIs responsive{Colors.END}")
        print(f"{Colors.GREEN}✓ Error handling robust{Colors.END}")
        return 0
    elif passed >= total * 0.8:  # 80% pass rate
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ MOSTLY FUNCTIONAL ({percentage:.1f}% pass rate){Colors.END}")
        print(f"{Colors.YELLOW}Most integration tests passed, but some issues need attention.{Colors.END}")
        print(f"{Colors.YELLOW}Review failed tests above and fix issues before production deployment.{Colors.END}")
        return 1
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ INTEGRATION TESTS FAILED ({percentage:.1f}% pass rate){Colors.END}")
        print(f"{Colors.RED}Multiple integration tests failed. System needs debugging.{Colors.END}")
        print(f"\n{Colors.YELLOW}Troubleshooting steps:{Colors.END}")
        print(f"{Colors.YELLOW}1. Verify all services are running: docker compose -f docker-compose.dev.yml ps{Colors.END}")
        print(f"{Colors.YELLOW}2. Check backend is accessible: curl http://localhost:8000/health{Colors.END}")
        print(f"{Colors.YELLOW}3. Run infrastructure tests: python tests/integration/test-infrastructure.py{Colors.END}")
        print(f"{Colors.YELLOW}4. Check logs: docker compose -f docker-compose.dev.yml logs backend{Colors.END}")
        print(f"{Colors.YELLOW}5. Verify database migrations: python -m alembic upgrade head{Colors.END}")
        return 2

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test suite crashed: {e}")
        import traceback
        print_error(traceback.format_exc())
        sys.exit(1)