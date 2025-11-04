# Phase 7: Chat API Endpoints - Implementation Plan

## Overview

Phase 7 will expose the conversational chat pipeline (Phase 6) through REST API and WebSocket endpoints, allowing external clients (web frontend, mobile apps, etc.) to interact with the Tamil AI Voice Assistant.

## Architecture

```
Client (Web/Mobile)
    ↓
FastAPI Endpoints (/chat/*)
    ↓
Chat Graph Pipeline (backend/graphs/chat_graph.py)
    ↓
STT → RAG → LLM → TTS
    ↓
Audio Response
```

## Implementation Tasks

### 7.1 Create Chat API Router (`backend/api/chat.py`)

**File Structure:**
```python
backend/api/chat.py
├── Request/Response Models (Pydantic)
├── Session Management Endpoints
├── Conversation Endpoints
├── Component Testing Endpoints
└── WebSocket Handler
```

**Key Components:**

1. **Pydantic Models:**
   - `SessionCreateRequest` - Create new session
   - `SessionResponse` - Session information
   - `ConversationTurnRequest` - Process conversation turn
   - `ConversationTurnResponse` - Turn results
   - `TranscribeRequest` - STT only
   - `SynthesizeRequest` - TTS only
   - `GenerateRequest` - LLM only

2. **Session Endpoints:**
   ```python
   POST   /chat/sessions              # Create new session
   GET    /chat/sessions/{id}         # Get session info
   GET    /chat/sessions              # List active sessions
   DELETE /chat/sessions/{id}         # Delete session
   GET    /chat/sessions/{id}/history # Get conversation history
   GET    /chat/stats                 # Global statistics
   ```

3. **Conversation Endpoints:**
   ```python
   POST   /chat/sessions/{id}/turn    # Process conversation turn
   POST   /chat/sessions/{id}/text    # Text-only conversation
   ```

4. **Component Testing Endpoints:**
   ```python
   POST   /chat/transcribe            # STT only
   POST   /chat/synthesize            # TTS only
   POST   /chat/generate              # LLM only
   ```

5. **Audio File Endpoints:**
   ```python
   GET    /chat/audio/{filename}      # Download audio file
   POST   /chat/upload-audio          # Upload audio for processing
   ```

6. **WebSocket Endpoint:**
   ```python
   WebSocket /chat/ws/{session_id}    # Real-time conversation
   ```

### 7.2 Request/Response Models

**Session Models:**
```python
class SessionCreateRequest(BaseModel):
    user_id: Optional[str] = None
    language: str = "ta"
    rag_enabled: bool = True

class SessionResponse(BaseModel):
    session_id: str
    user_id: Optional[str]
    language: str
    rag_enabled: bool
    created_at: str
    total_turns: int
    status: str
```

**Conversation Models:**
```python
class ConversationTurnResponse(BaseModel):
    success: bool
    session_id: str
    user_text: str
    assistant_text: str
    audio_output_url: Optional[str]
    processing_time: Dict[str, float]
    total_time: float
    error: Optional[str]
```

**Component Models:**
```python
class TranscribeRequest(BaseModel):
    language: str = "ta"

class TranscribeResponse(BaseModel):
    success: bool
    text: str
    language: str
    confidence: float
    duration: float

class SynthesizeRequest(BaseModel):
    text: str
    language: str = "ta"

class SynthesizeResponse(BaseModel):
    success: bool
    audio_url: str
    duration: float
    text_length: int
```

### 7.3 File Upload/Download Handling

**Audio Upload:**
- Accept WAV, MP3, OGG formats
- Max file size: 10MB
- Validate audio format and duration
- Save to temporary directory
- Clean up after processing

**Audio Download:**
- Serve generated audio files
- Set appropriate headers (Content-Type: audio/wav)
- Implement file cleanup after download
- Add expiration for old files

### 7.4 WebSocket Implementation

**Features:**
- Real-time bidirectional communication
- Audio streaming support
- Connection management
- Error handling and reconnection
- Session state synchronization

**Message Format:**
```json
{
  "type": "audio_chunk" | "text" | "status" | "error",
  "data": {...},
  "timestamp": "ISO-8601"
}
```

### 7.5 Integration with Chat Graph

**Direct Integration:**
```python
from backend.graphs.chat_graph import (
    create_session,
    process_conversation_turn,
    get_session_info,
    get_conversation_history,
    delete_session,
    get_session_stats
)
```

**Error Handling:**
- Wrap chat graph calls in try-except
- Return appropriate HTTP status codes
- Provide detailed error messages
- Log errors for debugging

### 7.6 Testing Strategy

**Unit Tests:**
- Test each endpoint independently
- Mock chat graph responses
- Validate request/response models
- Test error scenarios

**Integration Tests:**
- Test complete conversation flow
- Test audio upload/download
- Test WebSocket connection
- Test session management

**Performance Tests:**
- Measure response times
- Test concurrent sessions
- Test memory usage
- Test file cleanup

## Implementation Steps

### Step 1: Create Chat API Router
- [ ] Create `backend/api/chat.py`
- [ ] Define all Pydantic models
- [ ] Create router instance
- [ ] Add CORS configuration

### Step 2: Implement Session Endpoints
- [ ] POST /chat/sessions (create)
- [ ] GET /chat/sessions/{id} (get info)
- [ ] GET /chat/sessions (list all)
- [ ] DELETE /chat/sessions/{id} (delete)
- [ ] GET /chat/sessions/{id}/history (get history)
- [ ] GET /chat/stats (statistics)

### Step 3: Implement Conversation Endpoints
- [ ] POST /chat/sessions/{id}/turn (audio → audio)
- [ ] POST /chat/sessions/{id}/text (text → text)
- [ ] Add file upload handling
- [ ] Add audio file serving

### Step 4: Implement Component Endpoints
- [ ] POST /chat/transcribe (STT only)
- [ ] POST /chat/synthesize (TTS only)
- [ ] POST /chat/generate (LLM only)

### Step 5: Implement Audio File Management
- [ ] GET /chat/audio/{filename} (download)
- [ ] POST /chat/upload-audio (upload)
- [ ] Add file validation
- [ ] Add cleanup mechanism

### Step 6: Implement WebSocket
- [ ] WebSocket /chat/ws/{session_id}
- [ ] Connection management
- [ ] Message handling
- [ ] Error handling

### Step 7: Integration
- [ ] Update `backend/main.py` to include chat router
- [ ] Update `backend/api/__init__.py`
- [ ] Test all endpoints
- [ ] Update documentation

### Step 8: Testing
- [ ] Create `backend/api/test_chat_api.py`
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test with real audio files

### Step 9: Documentation
- [ ] Create API documentation
- [ ] Add usage examples
- [ ] Create Postman collection
- [ ] Update README

## API Endpoint Details

### Session Management

#### Create Session
```http
POST /chat/sessions
Content-Type: application/json

{
  "user_id": "user123",
  "language": "ta",
  "rag_enabled": true
}

Response:
{
  "session_id": "uuid-here",
  "user_id": "user123",
  "language": "ta",
  "rag_enabled": true,
  "created_at": "2025-10-31T17:00:00",
  "total_turns": 0,
  "status": "active"
}
```

#### Get Session Info
```http
GET /chat/sessions/{session_id}

Response:
{
  "session_id": "uuid-here",
  "user_id": "user123",
  "language": "ta",
  "rag_enabled": true,
  "created_at": "2025-10-31T17:00:00",
  "last_activity": "2025-10-31T17:05:00",
  "total_turns": 3,
  "session_duration": 300.5,
  "status": "active"
}
```

### Conversation

#### Process Turn (Audio → Audio)
```http
POST /chat/sessions/{session_id}/turn
Content-Type: multipart/form-data

audio: <audio-file.wav>
language: ta

Response:
{
  "success": true,
  "session_id": "uuid-here",
  "user_text": "வணக்கம்",
  "assistant_text": "வணக்கம்! நான் உங்கள் உதவியாளர்.",
  "audio_output_url": "/chat/audio/response_uuid_timestamp.wav",
  "processing_time": {
    "transcribe": 5.2,
    "retrieve": 0.3,
    "generate": 4.8,
    "synthesize": 2.1,
    "history": 0.01
  },
  "total_time": 12.41,
  "error": null
}
```

#### Text Conversation
```http
POST /chat/sessions/{session_id}/text
Content-Type: application/json

{
  "text": "வணக்கம்",
  "language": "ta"
}

Response:
{
  "success": true,
  "session_id": "uuid-here",
  "user_text": "வணக்கம்",
  "assistant_text": "வணக்கம்! நான் உங்கள் உதவியாளர்.",
  "processing_time": {...},
  "total_time": 5.2
}
```

### Component Testing

#### Transcribe
```http
POST /chat/transcribe
Content-Type: multipart/form-data

audio: <audio-file.wav>
language: ta

Response:
{
  "success": true,
  "text": "வணக்கம்",
  "language": "ta",
  "confidence": 0.98,
  "duration": 5.2
}
```

#### Synthesize
```http
POST /chat/synthesize
Content-Type: application/json

{
  "text": "வணக்கம்! நான் உங்கள் உதவியாளர்.",
  "language": "ta"
}

Response:
{
  "success": true,
  "audio_url": "/chat/audio/synth_uuid_timestamp.wav",
  "duration": 2.1,
  "text_length": 35
}
```

## Error Handling

**HTTP Status Codes:**
- 200: Success
- 201: Created (new session)
- 400: Bad Request (invalid input)
- 404: Not Found (session not found)
- 413: Payload Too Large (file too big)
- 415: Unsupported Media Type (invalid audio format)
- 500: Internal Server Error

**Error Response Format:**
```json
{
  "success": false,
  "error": "Error message here",
  "error_type": "ValidationError",
  "details": {...}
}
```

## Security Considerations

1. **File Upload:**
   - Validate file types
   - Limit file sizes
   - Sanitize filenames
   - Use temporary storage

2. **Session Management:**
   - Implement session timeouts
   - Clean up expired sessions
   - Limit concurrent sessions per user

3. **Rate Limiting:**
   - Limit requests per minute
   - Prevent abuse
   - Implement backoff strategies

4. **CORS:**
   - Configure allowed origins
   - Set appropriate headers
   - Handle preflight requests

## Performance Optimization

1. **Async Processing:**
   - Use async/await for I/O operations
   - Background tasks for cleanup
   - Non-blocking file operations

2. **Caching:**
   - Cache session data
   - Cache model instances
   - Cache audio files temporarily

3. **Resource Management:**
   - Limit concurrent sessions
   - Clean up old files
   - Monitor memory usage

## Testing Checklist

- [ ] All endpoints return correct status codes
- [ ] Request validation works correctly
- [ ] File upload/download works
- [ ] Session management works
- [ ] Conversation flow maintains context
- [ ] Error handling works properly
- [ ] WebSocket connection stable
- [ ] Performance meets requirements
- [ ] Memory usage acceptable
- [ ] File cleanup works

## Success Criteria

✅ All API endpoints implemented and tested
✅ Audio file upload/download working
✅ Session management functional
✅ Conversation flow maintains context
✅ WebSocket real-time communication working
✅ Error handling comprehensive
✅ Performance acceptable (<15s per turn)
✅ Documentation complete
✅ Integration tests passing

## Next Steps After Phase 7

With Phase 7 complete, you'll be able to:
- Test the complete flow via REST API
- Use Postman/curl to interact with the assistant
- Build frontend applications (Phase 8)
- Deploy the backend service
- Monitor and optimize performance

Ready to implement Phase 7!
