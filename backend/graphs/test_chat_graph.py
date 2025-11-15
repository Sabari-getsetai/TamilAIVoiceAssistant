"""
Test suite for Conversational Chat Graph

Tests the complete conversation workflow including:
- Session management
- Individual node processing
- End-to-end conversation flow
- Error handling and recovery
- Performance monitoring
"""

import sys
import os
import time
import tempfile
from pathlib import Path
from typing import Dict, Any


from backend.graphs.chat_graph import (
    # Core functions
    create_session, delete_session, get_session_info,
    get_conversation_history, get_session_stats,
    process_conversation_turn,
    transcribe_node, retrieve_node, generate_node,
    synthesize_node, history_node,
    # State management
    ChatState
)
from backend.speech import synthesize_speech, save_audio
from backend.settings import settings
import numpy as np


def create_test_audio(text: str, filename: str) -> str:
    """
    Create test audio file for testing
    
    Args:
        text: Text to synthesize
        filename: Output filename
        
    Returns:
        Path to created audio file
    """
    output_path = settings.AUDIO_OUT_DIR / filename
    
    # Try to create real audio with TTS
    try:
        audio = synthesize_speech(text, output_path=str(output_path))
        if audio is not None:
            return str(output_path)
    except Exception as e:
        print(f"TTS failed, creating mock audio: {e}")
    
    # Fallback: create mock audio file (sine wave)
    sample_rate = 16000
    duration = 2.0
    frequency = 440.0
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    save_audio(str(output_path), audio_data, sample_rate)
    return str(output_path)


def test_session_management():
    """Test session creation, retrieval, and cleanup"""
    print("="*70)
    print("🧪 Test 1: Session Management")
    print("="*70)
    
    results = {
        "create_session": False,
        "get_session": False,
        "session_info": False,
        "delete_session": False,
        "session_stats": False
    }
    
    try:
        # Test session creation
        session_id = create_session(
            user_id="test_user",
            language="ta",
            rag_enabled=True
        )
        
        if session_id:
            print(f"✅ Session created: {session_id}")
            results["create_session"] = True
        
        # Test session retrieval
        session_state = session_manager.get_session(session_id)
        if session_state:
            print(f"✅ Session retrieved: {session_state['session_id']}")
            results["get_session"] = True
        
        # Test session info
        info = get_session_info(session_id)
        if info:
            print(f"✅ Session info: {info['language']}, RAG: {info['rag_enabled']}")
            results["session_info"] = True
        
        # Test session stats
        stats = get_session_stats()
        if stats["total_sessions"] > 0:
            print(f"✅ Session stats: {stats['total_sessions']} active sessions")
            results["session_stats"] = True
        
        # Test session deletion
        if delete_session(session_id):
            print(f"✅ Session deleted: {session_id}")
            results["delete_session"] = True
        
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nSession Management: {passed}/{total} tests passed")
    
    return passed == total


def test_individual_nodes():
    """Test individual graph nodes"""
    print("\n" + "="*70)
    print("🧪 Test 2: Individual Node Processing")
    print("="*70)
    
    results = {
        "transcribe_node": False,
        "retrieve_node": False,
        "generate_node": False,
        "synthesize_node": False,
        "history_node": False
    }
    
    # Create test session
    session_id = create_session(language="ta", rag_enabled=False)
    
    try:
        # Create mock state
        from datetime import datetime
        
        test_state: ChatState = {
            "session_id": session_id,
            "user_id": "test_user",
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "audio_input": None,
            "audio_input_path": None,
            "user_text": "",
            "assistant_text": "",
            "audio_output": None,
            "audio_output_path": None,
            "conversation_history": [],
            "retrieved_documents": [],
            "context_used": "",
            "rag_enabled": False,
            "current_step": "testing",
            "error_message": None,
            "processing_time": {},
            "language": "ta",
            "max_history_turns": 10,
            "total_turns": 0,
            "session_duration": 0.0
        }
        
        # Test transcribe node (with mock audio)
        print("\nTesting transcribe_node...")
        try:
            # Create test audio
            test_audio_path = create_test_audio("வணக்கம்", "test_transcribe.wav")
            test_state["audio_input_path"] = test_audio_path
            
            result_state = transcribe_node(test_state.copy())
            if "transcribe" in result_state["processing_time"]:
                print(f"✅ Transcribe node: {result_state['processing_time']['transcribe']:.3f}s")
                results["transcribe_node"] = True
            else:
                print(f"⚠️  Transcribe node completed but may have failed")
        except Exception as e:
            print(f"❌ Transcribe node failed: {e}")
        
        # Test retrieve node
        print("\nTesting retrieve_node...")
        try:
            test_state["user_text"] = "செயற்கை நுண்ணறிவு என்றால் என்ன?"
            result_state = retrieve_node(test_state.copy())
            if "retrieve" in result_state["processing_time"]:
                print(f"✅ Retrieve node: {result_state['processing_time']['retrieve']:.3f}s")
                results["retrieve_node"] = True
        except Exception as e:
            print(f"❌ Retrieve node failed: {e}")
        
        # Test generate node
        print("\nTesting generate_node...")
        try:
            test_state["user_text"] = "வணக்கம்"
            result_state = generate_node(test_state.copy())
            if result_state["assistant_text"]:
                print(f"✅ Generate node: '{result_state['assistant_text'][:50]}...'")
                results["generate_node"] = True
        except Exception as e:
            print(f"❌ Generate node failed: {e}")
        
        # Test synthesize node
        print("\nTesting synthesize_node...")
        try:
            test_state["assistant_text"] = "வணக்கம்! நான் உங்கள் உதவியாளர்."
            result_state = synthesize_node(test_state.copy())
            if result_state.get("audio_output_path"):
                print(f"✅ Synthesize node: {result_state['audio_output_path']}")
                results["synthesize_node"] = True
        except Exception as e:
            print(f"❌ Synthesize node failed: {e}")
        
        # Test history node
        print("\nTesting history_node...")
        try:
            test_state["user_text"] = "வணக்கம்"
            test_state["assistant_text"] = "வணக்கம்! நான் உங்கள் உதவியாளர்."
            result_state = history_node(test_state.copy())
            if len(result_state["conversation_history"]) > 0:
                print(f"✅ History node: {len(result_state['conversation_history'])} turns")
                results["history_node"] = True
        except Exception as e:
            print(f"❌ History node failed: {e}")
        
    except Exception as e:
        print(f"❌ Individual nodes test failed: {e}")
    
    finally:
        # Cleanup
        delete_session(session_id)
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nIndividual Nodes: {passed}/{total} tests passed")
    
    return passed == total


def test_end_to_end_conversation():
    """Test complete conversation flow"""
    print("\n" + "="*70)
    print("🧪 Test 3: End-to-End Conversation Flow")
    print("="*70)
    
    results = {
        "session_creation": False,
        "first_turn": False,
        "second_turn": False,
        "conversation_history": False,
        "performance": False
    }
    
    try:
        # Create session
        session_id = create_session(language="ta", rag_enabled=False)
        if session_id:
            print(f"✅ Session created: {session_id}")
            results["session_creation"] = True
        
        # First conversation turn
        print("\nFirst turn: User says 'வணக்கம்'")
        test_audio_1 = create_test_audio("வணக்கம்", "test_turn_1.wav")
        
        start_time = time.time()
        result_1 = process_conversation_turn(
            session_id=session_id,
            audio_input_path=test_audio_1,
            language="ta"
        )
        turn_1_time = time.time() - start_time
        
        if result_1["success"]:
            print(f"✅ First turn successful:")
            print(f"   User: {result_1.get('user_text', 'N/A')}")
            print(f"   Assistant: {result_1.get('assistant_text', 'N/A')[:50]}...")
            print(f"   Total time: {result_1.get('total_time', 0):.2f}s")
            results["first_turn"] = True
        else:
            print(f"❌ First turn failed: {result_1.get('error', 'Unknown error')}")
        
        # Second conversation turn
        print("\nSecond turn: User asks question")
        test_audio_2 = create_test_audio("நீங்கள் யார்?", "test_turn_2.wav")
        
        start_time = time.time()
        result_2 = process_conversation_turn(
            session_id=session_id,
            audio_input_path=test_audio_2,
            language="ta"
        )
        turn_2_time = time.time() - start_time
        
        if result_2["success"]:
            print(f"✅ Second turn successful:")
            print(f"   User: {result_2.get('user_text', 'N/A')}")
            print(f"   Assistant: {result_2.get('assistant_text', 'N/A')[:50]}...")
            print(f"   Total time: {result_2.get('total_time', 0):.2f}s")
            results["second_turn"] = True
        else:
            print(f"❌ Second turn failed: {result_2.get('error', 'Unknown error')}")
        
        # Check conversation history
        history = get_conversation_history(session_id)
        if history and len(history) >= 2:
            print(f"✅ Conversation history: {len(history)} turns recorded")
            results["conversation_history"] = True
        
        # Performance check
        avg_time = (turn_1_time + turn_2_time) / 2
        if avg_time < 10.0:  # Should complete within 10 seconds
            print(f"✅ Performance: Average {avg_time:.2f}s per turn")
            results["performance"] = True
        else:
            print(f"⚠️  Performance: Slow response time {avg_time:.2f}s")
        
        # Session info
        info = get_session_info(session_id)
        if info:
            print(f"\nSession Summary:")
            print(f"   Total turns: {info['total_turns']}")
            print(f"   Duration: {info['session_duration']:.1f}s")
            print(f"   Language: {info['language']}")
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
    
    finally:
        # Cleanup
        if 'session_id' in locals():
            delete_session(session_id)
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nEnd-to-End Flow: {passed}/{total} tests passed")
    
    return passed == total


def test_error_handling():
    """Test error handling and recovery"""
    print("\n" + "="*70)
    print("🧪 Test 4: Error Handling & Recovery")
    print("="*70)
    
    results = {
        "invalid_session": False,
        "missing_audio": False,
        "invalid_audio": False,
        "graceful_degradation": False
    }
    
    try:
        # Test invalid session
        print("\nTesting invalid session...")
        result = process_conversation_turn(
            session_id="invalid-session-id",
            audio_input_path="dummy.wav",
            language="ta"
        )
        if not result["success"] and "not found" in result.get("error", "").lower():
            print("✅ Invalid session handled correctly")
            results["invalid_session"] = True
        
        # Test missing audio file
        print("\nTesting missing audio file...")
        session_id = create_session(language="ta", rag_enabled=False)
        result = process_conversation_turn(
            session_id=session_id,
            audio_input_path="nonexistent_file.wav",
            language="ta"
        )
        if not result["success"]:
            print("✅ Missing audio file handled correctly")
            results["missing_audio"] = True
        
        # Test invalid audio file
        print("\nTesting invalid audio file...")
        # Create empty file
        invalid_audio_path = settings.AUDIO_OUT_DIR / "invalid.wav"
        with open(invalid_audio_path, 'w') as f:
            f.write("not audio data")
        
        result = process_conversation_turn(
            session_id=session_id,
            audio_input_path=str(invalid_audio_path),
            language="ta"
        )
        if not result["success"]:
            print("✅ Invalid audio file handled correctly")
            results["invalid_audio"] = True
        
        # Test graceful degradation (RAG failure)
        print("\nTesting graceful degradation...")
        # This should work even if RAG components fail
        test_audio = create_test_audio("வணக்கம்", "test_degradation.wav")
        result = process_conversation_turn(
            session_id=session_id,
            audio_input_path=test_audio,
            language="ta"
        )
        # Should succeed even with potential component failures
        if result.get("assistant_text"):
            print("✅ Graceful degradation working")
            results["graceful_degradation"] = True
        
        # Cleanup
        delete_session(session_id)
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nError Handling: {passed}/{total} tests passed")
    
    return passed == total


def test_performance_monitoring():
    """Test performance monitoring and metrics"""
    print("\n" + "="*70)
    print("🧪 Test 5: Performance Monitoring")
    print("="*70)
    
    results = {
        "timing_metrics": False,
        "session_analytics": False,
        "memory_usage": False
    }
    
    try:
        # Create session and run multiple turns
        session_id = create_session(language="ta", rag_enabled=False)
        
        # Run multiple conversation turns
        turn_times = []
        for i in range(3):
            test_audio = create_test_audio(f"டெஸ்ட் {i+1}", f"perf_test_{i+1}.wav")
            
            start_time = time.time()
            result = process_conversation_turn(
                session_id=session_id,
                audio_input_path=test_audio,
                language="ta"
            )
            turn_time = time.time() - start_time
            turn_times.append(turn_time)
            
            if result["success"]:
                processing_time = result.get("processing_time", {})
                print(f"Turn {i+1}: {turn_time:.2f}s total")
                for step, step_time in processing_time.items():
                    print(f"   {step}: {step_time:.3f}s")
        
        # Check timing metrics
        if turn_times and all(t < 15.0 for t in turn_times):  # All turns under 15s
            print("✅ Timing metrics within acceptable range")
            results["timing_metrics"] = True
        
        # Check session analytics
        stats = get_session_stats()
        if stats and stats["total_sessions"] > 0:
            print(f"✅ Session analytics: {stats}")
            results["session_analytics"] = True
        
        # Basic memory usage check
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        if memory_mb < 2000:  # Under 2GB
            print(f"✅ Memory usage: {memory_mb:.1f} MB")
            results["memory_usage"] = True
        else:
            print(f"⚠️  High memory usage: {memory_mb:.1f} MB")
        
        # Cleanup
        delete_session(session_id)
        
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nPerformance Monitoring: {passed}/{total} tests passed")
    
    return passed == total


def main():
    """Run all chat graph tests"""
    print("="*70)
    print("🎯 Tamil AI Voice Assistant - Chat Graph Tests")
    print("="*70)
    
    test_results = {
        "Session Management": False,
        "Individual Nodes": False,
        "End-to-End Flow": False,
        "Error Handling": False,
        "Performance Monitoring": False
    }
    
    # Run all tests
    try:
        test_results["Session Management"] = test_session_management()
    except Exception as e:
        print(f"❌ Session management test suite failed: {e}")
    
    try:
        test_results["Individual Nodes"] = test_individual_nodes()
    except Exception as e:
        print(f"❌ Individual nodes test suite failed: {e}")
    
    try:
        test_results["End-to-End Flow"] = test_end_to_end_conversation()
    except Exception as e:
        print(f"❌ End-to-end test suite failed: {e}")
    
    try:
        test_results["Error Handling"] = test_error_handling()
    except Exception as e:
        print(f"❌ Error handling test suite failed: {e}")
    
    try:
        test_results["Performance Monitoring"] = test_performance_monitoring()
    except Exception as e:
        print(f"❌ Performance monitoring test suite failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 Chat Graph Test Results Summary")
    print("="*70)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print("\n" + "="*70)
    print(f"Total: {passed_tests}/{total_tests} test suites passed ({passed_tests/total_tests*100:.0f}%)")
    print("="*70)
    
    if passed_tests == total_tests:
        print("\n🎉 All chat graph tests passed! Conversation pipeline is ready!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test suite(s) failed. Check logs above.")
    
    print("\n📁 Generated test files in: data/out/")
    print("   - test_*.wav (test audio files)")
    print("   - response_*.wav (generated responses)")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    main()
