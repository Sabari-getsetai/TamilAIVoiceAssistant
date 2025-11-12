# Chat API Documentation

Complete API reference for the Tamil AI Voice Assistant Chat endpoints with organization-based multi-tenancy support.

## Base URL

```
http://localhost:8000/api/chat
```

## Authentication

All chat endpoints require authentication and organization membership. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

The token must contain:
- Valid user authentication
- Organization context (organization ID and user's role within the organization)
- Active organization membership

## Organization Context

All chat operations are scoped to the user's current organization. The organization context is automatically extracted from the JWT token and used to:

- Isolate chat sessions between organizations
- Apply organization-specific settings and quotas
- Ensure data privacy and security
- Track usage per organization

### Organization Switching

To switch organization context, update your JWT token with the new organization ID using the authentication API.

---

## Session Management

### Create Session

Create a new chat session within the current organization context.

**Endpoint:** `POST /api/chat/sessions`

**Headers:**
```
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "language": "ta",                // Default: "ta"
  "rag_enabled": true,             // Default: true
  "title": "My Chat Session",      // Optional session title
  "metadata": {                    // Optional metadata
    "source": "web_app",
    "device": "desktop"
  }
}
```

**Response:** `201 Created`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "org-123",
  "user_id": "user-456",
  "language": "ta",
  "rag_enabled": true,
  "title": "My Chat Session",
  "created_at": "2025-10-31T17:00:00Z",
  "last_activity": null,
  "total_turns": 0,
  "session_duration": null,
  "status": "active",
  "metadata": {
    "source": "web_app",
    "device": "desktop"
  }
}
```

**Status Codes:**
- `201` - Session created successfully
- `400` - Invalid request data
- `401` - Authentication required
- `403` - Organization membership required
- `429` - Rate limit exceeded

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/sessions \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language": "ta", "rag_enabled": true, "title": "My Chat Session"}'
```

---

### Get Session Info

Get information about a specific session. User must be the session owner and a member of the organization.

**Endpoint:** `GET /api/chat/sessions/{session_id}`

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "org-123",
  "user_id": "user-456",
  "language": "ta",
  "rag_enabled": true,
  "title": "My Chat Session",
  "created_at": "2025-10-31T17:00:00Z",
  "last_activity": "2025-10-31T17:05:00Z",
  "total_turns": 3,
  "session_duration": 300.5,
  "status": "active",
  "metadata": {
    "source": "web_app",
    "device": "desktop"
  }
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Access denied (not session owner or organization member)
- `404` - Session not found

**Example:**
```bash
curl http://localhost:8000/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### List Sessions

List chat sessions for the current user within the organization context.

**Endpoint:** `GET /api/chat/sessions`

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `completed`, `archived`)
- `limit` (optional): Number of results per page (default: 20, max: 100)
- `offset` (optional): Number of results to skip (default: 0)
- `sort` (optional): Sort field (`created_at`, `last_activity`, `total_turns`) (default: `last_activity`)
- `order` (optional): Sort order (`asc`, `desc`) (default: `desc`)

**Response:** `200 OK`
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_id": "org-123",
      "user_id": "user-456",
      "language": "ta",
      "rag_enabled": true,
      "title": "My Chat Session",
      "created_at": "2025-10-31T17:00:00Z",
      "last_activity": "2025-10-31T17:05:00Z",
      "total_turns": 3,
      "session_duration": 300.5,
      "status": "active"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0,
  "has_next": false,
  "has_previous": false
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Organization membership required

**Example:**
```bash
curl "http://localhost:8000/api/chat/sessions?status=active&limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Delete Session

Delete a chat session. User must be the session owner.

**Endpoint:** `DELETE /api/chat/sessions/{session_id}`

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Session 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

**Status Codes:**
- `200` - Session deleted successfully
- `401` - Authentication required
- `403` - Access denied (not session owner)
- `404` - Session not found

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Get Conversation History

Get the conversation history for a session. User must be the session owner.

**Endpoint:** `GET /api/chat/sessions/{session_id}/history`

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Query Parameters:**
- `limit` (optional): Number of turns to return (default: 50, max: 200)
- `offset` (optional): Number of turns to skip (default: 0)
- `include_metadata` (optional): Include processing metadata (default: false)

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "org-123",
  "total_turns": 2,
  "limit": 50,
  "offset": 0,
  "history": [
    {
      "turn_id": "turn-001",
      "user": "வணக்கம்",
      "assistant": "வணக்கம்! நான் உங்கள் உதவியாளர்.",
      "timestamp": "2025-10-31T17:01:00Z",
      "processing_time": 2.5,
      "metadata": {
        "rag_used": true,
        "retrieved_chunks": 2,
        "confidence": 0.95
      }
    },
    {
      "turn_id": "turn-002",
      "user": "நீங்கள் யார்?",
      "assistant": "நான் தமிழ் AI உதவியாளர்.",
      "timestamp": "2025-10-31T17:02:00Z",
      "processing_time": 1.8,
      "metadata": {
        "rag_used": false,
        "confidence": 0.98
      }
    }
  ]
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Access denied (not session owner)
- `404` - Session not found

**Example:**
```bash
curl "http://localhost:8000/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000/history?limit=10&include_metadata=true" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Get Organization Chat Statistics

Get chat statistics for the current organization. Requires organization admin or owner role.

**Endpoint:** `GET /api/chat/stats`

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Query Parameters:**
- `period` (optional): Time period (`day`, `week`, `month`, `year`) (default: `month`)
- `start_date` (optional): Start date in ISO format
- `end_date` (optional): End date in ISO format

**Response:** `200 OK`
```json
{
  "organization_id": "org-123",
  "period": "month",
  "start_date": "2025-10-01T00:00:00Z",
  "end_date": "2025-10-31T23:59:59Z",
  "statistics": {
    "total_sessions": 150,
    "active_sessions": 12,
    "total_turns": 2340,
    "total_users": 25,
    "average_session_duration": 450.5,
    "average_turn_time": 12.3,
    "total_processing_time": 15600.8
  },
  "usage_by_feature": {
    "text_chat": 1800,
    "voice_chat": 540,
    "rag_enabled": 1950,
    "rag_disabled": 390
  },
  "daily_breakdown": [
    {
      "date": "2025-10-01",
      "sessions": 8,
      "turns": 95,
      "users": 5
    },
    {
      "date": "2025-10-02",
      "sessions": 12,
      "turns": 140,
      "users": 7
    }
  ]
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Admin access required (organization admin or owner)

**Example:**
```bash
curl "http://localhost:8000/api/chat/stats?period=week" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Conversation

### Process Turn (Audio → Audio)

Process a conversation turn with audio input and audio output. User must be the session owner.

**Endpoint:** `POST /api/chat/sessions/{session_id}/turn`

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Request:** `multipart/form-data`
- `audio`: Audio file (WAV, MP3, OGG, M4A)
- `language`: Language code (default: "ta")

**Response:** `200 OK`
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "org-123",
  "turn_id": "turn-003",
  "user_text": "வணக்கம்",
  "assistant_text": "வணக்கம்! நான் உங்கள் உதவியாளர்.",
  "audio_output_url": "/api/chat/audio/response_abc123_20251031_170500.wav",
  "processing_time": {
    "transcribe": 5.2,
    "retrieve": 0.3,
    "generate": 4.8,
    "synthesize": 2.1,
    "history": 0.01
  },
  "total_time": 12.41,
  "metadata": {
    "rag_used": true,
    "retrieved_chunks": 2,
    "confidence": 0.95
  },
  "error": null
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid audio file or parameters
- `401` - Authentication required
- `403` - Access denied (not session owner)
- `404` - Session not found
- `413` - File too large
- `415` - Unsupported audio format

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000/turn \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "audio=@input.wav" \
  -F "language=ta"
```

---

### Process Text Turn

Process a text-only conversation turn. User must be the session owner.

**Endpoint:** `POST /api/chat/sessions/{session_id}/text`

**Headers:**
```
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

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
  "organization_id": "org-123",
  "turn_id": "turn-004",
  "user_text": "வணக்கம்! நீங்கள் யார்?",
  "assistant_text": "வணக்கம்! நான் தமிழ் AI உதவியாளர்.",
  "processing_time": {
    "retrieve": 0.3,
    "generate": 4.8,
    "history": 0.01
  },
  "total_time": 5.11,
  "metadata": {
    "rag_used": false,
    "confidence": 0.98
  },
  "error": null
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request data
- `401` - Authentication required
- `403` - Access denied (not session owner)
- `404` - Session not found

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000/text \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "வணக்கம்! நீங்கள் யார்?", "language": "ta"}'
```

---

## Component Testing

### Transcribe Audio (STT)

Transcribe audio to text using Speech-to-Text. Requires authentication.

**Endpoint:** `POST /api/chat/transcribe`

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Request:** `multipart/form-data`
- `audio`: Audio file
- `language`: Language code (default: "ta")

**Response:** `200 OK`
```json
{
  "success": true,
  "text": "வணக்கம்",
  "language": "ta",
  "confidence": 0.95,
  "duration": 5.2,
  "organization_id": "org-123"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid audio file
- `401` - Authentication required
- `403` - Organization membership required
- `413` - File too large
- `415` - Unsupported audio format

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/transcribe \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "audio=@input.wav" \
  -F "language=ta"
```

---

### Synthesize Speech (TTS)

Synthesize speech from text using Text-to-Speech. Requires authentication.

**Endpoint:** `POST /api/chat/synthesize`

**Headers:**
```
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

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
  "audio_url": "/api/chat/audio/synth_abc123_20251031_170500.wav",
  "duration": 2.1,
  "text_length": 35,
  "organization_id": "org-123"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request data
- `401` - Authentication required
- `403` - Organization membership required

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/synthesize \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "வணக்கம்! நான் தமிழ் AI உதவியாளர்.", "language": "ta"}'
```

---

### Generate Text (LLM)

Generate text response using the Language Model with organization-scoped knowledge base.

**Endpoint:** `POST /api/chat/generate`

**Headers:**
```
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

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
  "duration": 4.8,
  "organization_id": "org-123",
  "metadata": {
    "model_used": "sarvam-2b",
    "tokens_generated": 150,
    "confidence": 0.92
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request data
- `401` - Authentication required
- `403` - Organization membership required

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/generate \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "தமிழ் மொழியின் சிறப்புகள் என்ன?", "language": "ta", "use_rag": true}'
```

---

## Audio File Serving

### Download Audio File

Download a generated audio file. Requires authentication and the file must belong to the user's organization.

**Endpoint:** `GET /api/chat/audio/{filename}`

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Response:** `200 OK`
- Content-Type: `audio/wav`
- Binary audio data

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Access denied (file not owned by user's organization)
- `404` - File not found

**Example:**
```bash
curl http://localhost:8000/api/chat/audio/response_abc123_20251031_170500.wav \
  -H "Authorization: Bearer $JWT_TOKEN" \
  --output response.wav
```

---

## WebSocket

### Real-time Conversation

WebSocket endpoint for real-time conversation. Requires authentication via query parameter or header.

**Endpoint:** `WS /api/chat/ws/{session_id}?token={jwt_token}`

**Connection:**
```javascript
const ws = new WebSocket(`ws://localhost:8000/api/chat/ws/550e8400-e29b-41d4-a716-446655440000?token=${jwtToken}`);
```

**Authentication:**
- Include JWT token as query parameter: `?token={jwt_token}`
- Or send token in first message after connection

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
# Set JWT token
JWT_TOKEN="your-jwt-token-here"

# 1. Create session
SESSION_ID=$(curl -X POST http://localhost:8000/api/chat/sessions \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language": "ta", "rag_enabled": true, "title": "Test Session"}' \
  | jq -r '.session_id')

# 2. Send text message
curl -X POST http://localhost:8000/api/chat/sessions/$SESSION_ID/text \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "வணக்கம்", "language": "ta"}'

# 3. Get conversation history
curl http://localhost:8000/api/chat/sessions/$SESSION_ID/history \
  -H "Authorization: Bearer $JWT_TOKEN"

# 4. Delete session
curl -X DELETE http://localhost:8000/api/chat/sessions/$SESSION_ID \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Audio Conversation

```bash
# Set JWT token
JWT_TOKEN="your-jwt-token-here"

# 1. Create session
SESSION_ID=$(curl -X POST http://localhost:8000/api/chat/sessions \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language": "ta", "title": "Audio Session"}' \
  | jq -r '.session_id')

# 2. Send audio
curl -X POST http://localhost:8000/api/chat/sessions/$SESSION_ID/turn \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "audio=@input.wav" \
  -F "language=ta" \
  | jq -r '.audio_output_url' \
  | xargs -I {} curl http://localhost:8000{} \
    -H "Authorization: Bearer $JWT_TOKEN" \
    --output response.wav

# 3. Play response
play response.wav
```

### Organization Statistics

```bash
# Get organization chat statistics
curl "http://localhost:8000/api/chat/stats?period=month" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Get detailed member activity
curl "http://localhost:8000/api/organizations/org-123/analytics/members" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Organization Features

### Data Isolation
- All chat sessions are isolated by organization
- Users can only access sessions within their current organization
- Knowledge base (RAG) is scoped to organization-specific documents
- Audio files are organization-scoped and access-controlled

### Quotas and Limits
Organizations may have different quotas based on their subscription:
- Maximum concurrent sessions
- Monthly message limits
- Storage limits for audio files
- API rate limits

### Analytics and Monitoring
- Organization-level usage statistics
- Member activity tracking
- Feature usage analytics
- Performance metrics

## Migration Notes

When migrating from single-tenant to multi-tenant:
1. Existing sessions will need organization assignment
2. Audio files will need organization-scoped access control
3. Knowledge base will need organization-specific indexing
4. User authentication will require organization context

## Related Documentation

- [Organization Management](../features/organization-management.md)
- [Member Management](../features/member-management.md)
- [Organization API](./organization-api.md)
- [Authentication System](../features/authentication.md)
- [Migration Guide](../migration/single-to-multi-tenant.md)

## Support

For issues or questions, please refer to the project documentation or create an issue in the repository.
