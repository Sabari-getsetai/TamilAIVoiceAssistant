# Chat API Documentation

Complete API reference for the Tamil AI Voice Assistant Chat endpoints.

## Base URL

```
http://localhost:8000/chat
```

## Authentication

Currently, no authentication is required. This will be added in future versions.

---

## Session Management

### Create Session

Create a new chat session.

**Endpoint:** `POST /chat/sessions`

**Request Body:**
```json
{
  "user_id": "user123",           // Optional
  "language": "ta",                // Default: "ta"
  "rag_enabled": true              // Default: true
}
```

**Response:** `201 Created`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "language": "ta",
  "rag_enabled": true,
  "created_at": "2025-10-31T17:00:00",
  "last_activity": null,
  "total_turns": 0,
  "session_duration": null,
  "status": "active"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "language": "ta", "rag_enabled": true}'
```

---

### Get Session Info

Get information about a specific session.

**Endpoint:** `GET /chat/sessions/{session_id}`

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
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

**Example:**
```bash
curl http://localhost:8000/chat/sessions/550e8400-e29b-41d4-a716-446655440000
```

---

### List Sessions

List all active sessions.

**Endpoint:** `GET /chat/sessions`

**Response:** `200 OK`
```json
[
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123",
    "language": "ta",
    "rag_enabled": true,
    "created_at": "2025-10-31T17:00:00",
    "last_activity": "2025-10-31T17:05:00",
    "total_turns": 3,
    "session_duration": 300.5,
    "status": "active"
  }
]
```

**Example:**
```bash
curl http://localhost:8000/chat/sessions
```

---

### Delete Session

Delete a chat session.

**Endpoint:** `DELETE /chat/sessions/{session_id}`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Session 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/chat/sessions/550e8400-e29b-41d4-a716-446655440000
```

---

### Get Conversation History

Get the conversation history for a session.

**Endpoint:** `GET /chat/sessions/{session_id}/history`

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_turns": 2,
  "history": [
    {
      "user": "வணக்கம்",
      "assistant": "வணக்கம்! நான் உங்கள் உதவியாளர்.",
      "timestamp": "2025-10-31T17:01:00"
    },
    {
      "user": "நீங்கள் யார்?",
      "assistant": "நான் தமிழ் AI உதவியாளர்.",
      "timestamp": "2025-10-31T17:02:00"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/chat/sessions/550e8400-e29b-41d4-a716-446655440000/history
```

---

### Get Session Statistics

Get global session statistics.

**Endpoint:** `GET /chat/stats`

**Response:** `200 OK`
```json
{
  "total_sessions": 10,
  "active_sessions": 3,
  "total_turns": 45,
  "average_session_duration": 450.5,
  "average_turn_time": 12.3
}
```

**Example:**
```bash
curl http://localhost:8000/chat/stats
```

---

## Conversation

### Process Turn (Audio → Audio)

Process a conversation turn with audio input and audio output.

**Endpoint:** `POST /chat/sessions/{session_id}/turn`

**Request:** `multipart/form-data`
- `audio`: Audio file (WAV, MP3, OGG, M4A)
- `language`: Language code (default: "ta")

**Response:** `200 OK`
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_text": "வணக்கம்",
  "assistant_text": "வணக்கம்! நான் உங்கள் உதவியாளர்.",
  "audio_output_url": "/chat/audio/response_abc123_20251031_170500.wav",
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

**Example:**
```bash
curl -X POST http://localhost:8000/chat/sessions/550e8400-e29b-41d4-a716-446655440000/turn \
  -F "audio=@input.wav" \
  -F "language=ta"
```

---

### Process Text Turn

Process a text-only conversation turn.

**Endpoint:** `POST /chat/sessions/{session_id}/text`

**Request Body:**
```json
{
  "text": "வணக்கம்! நீங்கள் யார்?",
  "language": "ta"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_text": "வணக்கம்! நீங்கள் யார்?",
  "assistant_text": "வணக்கம்! நான் தமிழ் AI உதவியாளர்.",
  "processing_time": {
    "retrieve": 0.3,
    "generate": 4.8,
    "history": 0.01
  },
  "total_time": 5.11,
  "error": null
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat/sessions/550e8400-e29b-41d4-a716-446655440000/text \
  -H "Content-Type: application/json" \
  -d '{"text": "வணக்கம்! நீங்கள் யார்?", "language": "ta"}'
```

---

## Component Testing

### Transcribe Audio (STT)

Transcribe audio to text using Speech-to-Text.

**Endpoint:** `POST /chat/transcribe`

**Request:** `multipart/form-data`
- `audio`: Audio file
- `language`: Language code (default: "ta")

**Response:** `200 OK`
```json
{
  "success": true,
  "text": "வணக்கம்",
  "language": "ta",
  "confidence": null,
  "duration": 5.2
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat/transcribe \
  -F "audio=@input.wav" \
  -F "language=ta"
```

---

### Synthesize Speech (TTS)

Synthesize speech from text using Text-to-Speech.

**Endpoint:** `POST /chat/synthesize`

**Request Body:**
```json
{
  "text": "வணக்கம்! நான் தமிழ் AI உதவியாளர்.",
  "language": "ta"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "audio_url": "/chat/audio/synth_abc123_20251031_170500.wav",
  "duration": 2.1,
  "text_length": 35
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "வணக்கம்! நான் தமிழ் AI உதவியாளர்.", "language": "ta"}'
```

---

### Generate Text (LLM)

Generate text response using the Language Model.

**Endpoint:** `POST /chat/generate`

**Request Body:**
```json
{
  "text": "தமிழ் மொழியின் சிறப்புகள் என்ன?",
  "language": "ta",
  "use_rag": true
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "response_text": "தமிழ் மொழி உலகின் பழமையான மொழிகளில் ஒன்று...",
  "context_used": true,
  "retrieved_chunks": 3,
  "duration": 4.8
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "தமிழ் மொழியின் சிறப்புகள் என்ன?", "language": "ta", "use_rag": true}'
```

---

## Audio File Serving

### Download Audio File

Download a generated audio file.

**Endpoint:** `GET /chat/audio/{filename}`

**Response:** `200 OK`
- Content-Type: `audio/wav`
- Binary audio data

**Example:**
```bash
curl http://localhost:8000/chat/audio/response_abc123_20251031_170500.wav \
  --output response.wav
```

---

## WebSocket

### Real-time Conversation

WebSocket endpoint for real-time conversation.

**Endpoint:** `WS /chat/ws/{session_id}`

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/chat/ws/550e8400-e29b-41d4-a716-446655440000');
```

**Message Format:**

**Client → Server (Text Message):**
```json
{
  "type": "text",
  "data": {
    "text": "வணக்கம்",
    "language": "ta"
  }
}
```

**Server → Client (Response):**
```json
{
  "type": "response",
  "data": {
    "user_text": "வணக்கம்",
    "assistant_text": "வணக்கம்! நான் உங்கள் உதவியாளர்.",
    "processing_time": {...}
  },
  "timestamp": "2025-10-31T17:05:00"
}
```

**Client → Server (Ping):**
```json
{
  "type": "ping",
  "data": {}
}
```

**Server → Client (Pong):**
```json
{
  "type": "pong",
  "data": {},
  "timestamp": "2025-10-31T17:05:00"
}
```

**Client → Server (Close):**
```json
{
  "type": "close",
  "data": {}
}
```

**Server → Client (Error):**
```json
{
  "type": "error",
  "data": {
    "message": "Error description"
  },
  "timestamp": "2025-10-31T17:05:00"
}
```

---

## Error Responses

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - File too large
- `415 Unsupported Media Type` - Invalid file format
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

---

## Rate Limits

Currently, no rate limits are enforced. This will be added in future versions.

---

## File Upload Limits

- **Maximum file size:** 10 MB
- **Allowed formats:** WAV, MP3, OGG, M4A
- **Audio cleanup:** Files older than 24 hours are automatically deleted

---

## Testing

Run the test suite:

```bash
python backend/api/test_chat_api.py
```

Make sure the FastAPI server is running first:

```bash
uvicorn backend.main:app --reload
```

---

## Examples

### Complete Conversation Flow

```bash
# 1. Create session
SESSION_ID=$(curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"language": "ta", "rag_enabled": true}' \
  | jq -r '.session_id')

# 2. Send text message
curl -X POST http://localhost:8000/chat/sessions/$SESSION_ID/text \
  -H "Content-Type: application/json" \
  -d '{"text": "வணக்கம்", "language": "ta"}'

# 3. Get conversation history
curl http://localhost:8000/chat/sessions/$SESSION_ID/history

# 4. Delete session
curl -X DELETE http://localhost:8000/chat/sessions/$SESSION_ID
```

### Audio Conversation

```bash
# 1. Create session
SESSION_ID=$(curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"language": "ta"}' \
  | jq -r '.session_id')

# 2. Send audio
curl -X POST http://localhost:8000/chat/sessions/$SESSION_ID/turn \
  -F "audio=@input.wav" \
  -F "language=ta" \
  | jq -r '.audio_output_url' \
  | xargs -I {} curl http://localhost:8000{} --output response.wav

# 3. Play response
play response.wav
```

---

## Support

For issues or questions, please refer to the project documentation or create an issue in the repository.
