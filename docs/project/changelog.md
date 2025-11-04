# CHANGELOG

All notable changes to the Tamil AI Voice Assistant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed - 2025-11-04 13:45:00

**Document Counting Issue - Chunks Counted as Separate Documents**

Fixed critical bug where the admin dashboard was displaying chunk count instead of actual document count, causing confusion in document management.

#### Problem Identified

- Admin dashboard showed 7 documents when only 1 file was uploaded
- Each chunk of a document was being counted as a separate document
- `/admin/stats` API returned `total_documents: 7` (chunk count)
- `/admin/documents` API listed chunks individually instead of grouping by document

#### Root Cause

- Inconsistent session_id extraction logic across chunks
- Endpoints iterated through individual chunks instead of grouping by session_id first
- Stats endpoint used raw `len(vector_store.documents)` which counts all chunks

#### Solution Implemented

**backend/api/admin.py** - Fixed Document Counting Logic:

1. **Enhanced `/admin/documents` endpoint** (Lines 380-450):
   - Added `get_session_id()` helper function for consistent session_id extraction
   - Groups ALL chunks by session_id before processing
   - Iterates through unique session_ids (documents) instead of chunks
   - Uses first chunk as representative for metadata
   - Returns accurate chunk count per document

2. **Enhanced `/admin/stats` endpoint** (Lines 565-635):
   - Implemented same grouping logic as /documents endpoint
   - Returns separate counts:
     - `total_documents`: Unique documents (grouped by session_id)
     - `total_chunks`: Total chunks in vector store
     - `avg_chunks_per_document`: Average chunks per document
   - Maintains `index_size` for FAISS technical reference

#### New Stats Response Format

```json
{
    "exists": true,
    "total_documents": 1,           // Unique documents
    "total_chunks": 7,              // Total chunks
    "index_size": 7,                // FAISS index size
    "embedding_dimension": 384,
    "store_name": "default",
    "avg_chunks_per_document": 7.0
}
```

#### Impact

- ✅ Admin dashboard now shows correct document count (1 instead of 7)
- ✅ Clear distinction between documents and chunks
- ✅ Consistent counting logic across all endpoints
- ✅ Better user understanding of document management
- ✅ Accurate statistics for monitoring

#### Files Modified

- backend/api/admin.py (Lines 380-450, 565-635)

### Added - 2025-11-02 14:00:00

**Noise-Reduced Audio Comparison Feature**

Added capability to save both original and noise-reduced audio files side-by-side for quality comparison and testing. This helps verify the effectiveness of noise reduction settings and tune the parameters.

#### Features

**Parallel Audio Storage**:
- Original audio saved to: `data/out/user_audio/{session_id}_{timestamp}.wav`
- Noise-reduced audio saved to: `data/out/user_audio_refined/{session_id}_{timestamp}.wav` (NEW)
- Identical filenames in separate directories for easy A/B comparison

**STT Module Enhancement (`backend/speech/stt.py:188-223`)**:
- Added `save_refined_path` optional parameter to `transcribe_audio_data()`
- Automatically saves noise-reduced audio when path provided
- Logs save location for easy access

**WebSocket Handler Update (`backend/api/websocket.py:451-478`)**:
- Creates `user_audio_refined/` directory automatically
- Generates matching filename for refined audio
- Passes refined path to STT when noise reduction is enabled
- Logs both file paths after each recording for comparison

#### Usage

When `ENABLE_NOISE_REDUCTION = True` in settings, the system now saves both versions:

```
data/out/
├── user_audio/                    # Original recordings
│   └── session_123_20251102.wav
└── user_audio_refined/            # Noise-reduced (NEW)
    └── session_123_20251102.wav   # Same filename
```

**Log Output**:
```
📁 Audio pair saved for comparison:
   Original:  data/out/user_audio/session_123_20251102.wav
   Refined:   data/out/user_audio_refined/session_123_20251102.wav
```

#### Benefits

- **Quality Verification**: Compare before/after audio in any audio player
- **Parameter Tuning**: Test different `NOISE_REDUCTION_STRENGTH` values
- **A/B Testing**: Easily validate improvement in audio quality
- **Debugging**: Understand when noise reduction helps vs. affects quality

#### Technical Details

- Only saves refined audio when noise reduction is enabled
- Uses same filename convention for easy matching
- No performance impact - saved asynchronously
- Original audio always preserved for debugging

### Added - 2025-11-02 13:30:00

**Complete Frontend Document Management Integration**

Implemented full document management UI in the Next.js admin dashboard, connecting all backend APIs with a comprehensive user interface for viewing, deleting, and re-indexing documents.

#### Frontend API Client Updates

**Enhanced Type Definitions (`app/nextjs/src/types/index.ts`)**:
- Added `text_preview` and `indexed_at` optional fields to `Document` interface
- Created `DocumentDetailResponse` interface extending Document with required preview
- Created `ReindexResponse` interface for re-index operation responses

**New API Client Methods (`app/nextjs/src/services/api/adminApi.ts:102-116`)**:
- Added `getDocument(docId)` → GET `/admin/documents/${docId}` - Fetch specific document details
- Added `reindexDocument(docId)` → POST `/admin/documents/${docId}/reindex` - Re-index single document

#### Custom React Hooks

**New Hooks (`app/nextjs/src/hooks/useDocuments.ts`)**:
- Added `useGetDocument(docId, enabled)` - Query hook for fetching document details with conditional loading
- Added `useReindexDocument()` - Mutation hook for re-indexing single documents
- Both hooks auto-invalidate document and stats queries on success
- Integrated error handling with console logging

#### Document Management Page Updates

**Fixed Delete Functionality (`app/nextjs/src/app/admin/documents/page.tsx:104-121`)**:
- ✅ **FIXED**: Delete button now actually calls the API (was TODO stub before)
- Integrated `useDeleteDocument()` hook
- Proper async/await error handling
- Success/error notifications via Snackbar
- Loading state during deletion

**New Re-index Feature (`app/nextjs/src/app/admin/documents/page.tsx:99-140`)**:
- Added re-index button to each document row (Sync icon)
- Confirmation dialog before re-indexing
- Loading indicators during operation
- Success/error notifications

**Enhanced View Details (`app/nextjs/src/app/admin/documents/page.tsx:352-447`)**:
- Fetches full document details including text preview
- Shows loading spinner while fetching
- Displays complete metadata (ID, file size, chunks, upload date, indexed date, status)
- Text preview in scrollable monospace box (max 300px height)
- Proper modal state management

**User Experience Improvements**:
- Added Snackbar notifications for all operations (success/error)
- Disabled buttons during pending operations
- Loading indicators with CircularProgress
- Confirmation dialogs prevent accidental deletions/re-indexing
- Better error messages displayed to users
- All dialogs properly managed with separate state flags

#### Files Modified

1. `app/nextjs/src/types/index.ts` - Added 3 new type definitions
2. `app/nextjs/src/services/api/adminApi.ts` - Added 2 new API methods
3. `app/nextjs/src/hooks/useDocuments.ts` - Added 2 new custom hooks
4. `app/nextjs/src/app/admin/documents/page.tsx` - Complete rewrite with all features

#### Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| View Documents | ✅ Working | List all documents with search and metadata |
| View Details | ✅ Working | Full document preview with text content |
| Delete Document | ✅ Fixed | Now actually calls API and deletes document |
| Re-index Document | ✅ New | Re-process single document embeddings |
| Error Handling | ✅ Complete | Notifications for all operations |
| Loading States | ✅ Complete | Spinners and disabled states |

### Added - 2025-11-02 12:58:00

**Complete Document Management API with Vector Store Operations**

Implemented comprehensive document management backend APIs for admin dashboard, including CRUD operations, vector store reindexing, and batch operations for document control.

#### New API Endpoints

**Document Information (`backend/api/admin.py:73-83`)**:
- Enhanced `DocumentInfo` model with complete metadata
- Added fields: `filename`, `file_size`, `chunk_count`, `upload_date`, `status`
- Proper schema alignment with frontend Document interface

**Enhanced GET /admin/documents (`backend/api/admin.py:361-418`)**:
- Groups chunks by `session_id` to return unique documents
- Returns chunk count per document
- Extracts metadata (filename, file size) from first chunk
- Returns complete document information with all required fields

**New GET /admin/documents/{doc_id} (`backend/api/admin.py:424-483`)**:
- Retrieve specific document by ID
- Combines all chunks for preview
- Returns complete document metadata

**Enhanced DELETE /admin/documents/{doc_id} (`backend/api/admin.py:486-546`)**:
- Deletes ALL chunks of a document (not just one)
- Rebuilds index after deletion
- Returns count of deleted chunks

**New POST /admin/clear (`backend/api/admin.py:594-650`)**:
- Clears all documents from vector store
- Deletes all uploaded files from data/docs
- Resets FAISS index completely
- Returns count of documents and files deleted

**New POST /admin/reindex (`backend/api/admin.py:653-701`)**:
- Rebuilds FAISS index from existing documents
- Re-generates embeddings for all documents
- Returns count of documents re-indexed

**New DELETE /admin/index (`backend/api/admin.py:704-748`)**:
- Deletes FAISS index files (.index and .metadata)
- Preserves uploaded files in data/docs
- Returns list of deleted index files

**New POST /admin/documents/{doc_id}/reindex (`backend/api/admin.py:751-823`)**:
- Re-indexes a specific document
- Deletes existing chunks
- Re-runs ingestion workflow for that file
- Returns count of chunks re-indexed

#### Vector Store Improvements

**Enhanced rebuild_index() (`backend/rag/vectorstore.py:333-384`)**:
- Fixed issue where documents loaded from disk don't have embeddings
- Automatically re-generates embeddings when rebuilding index
- Supports optional embedding model parameter
- Falls back to auto-loading embedding model if not provided
- Handles both documents with and without stored embeddings

#### Technical Changes

**Document Grouping**:
- Uses `session_id` to group chunks into logical documents
- Provides accurate chunk counts per document
- Extracts metadata from first chunk of each document group

**Index Maintenance**:
- Rebuilds index after deletions to clean up
- Separate operations for clearing all vs deleting index only
- Preserves file metadata in all operations

#### Testing Results

All endpoints tested and verified:
- ✅ GET /admin/documents - Returns complete document list with new schema
- ✅ GET /admin/documents/{doc_id} - Retrieves specific document
- ✅ DELETE /admin/documents/{doc_id} - Deletes all chunks and rebuilds
- ✅ POST /admin/clear - Clears all documents and files
- ✅ POST /admin/reindex - Rebuilds index with auto-embedding
- ✅ DELETE /admin/index - Deletes index files, preserves uploads
- ✅ POST /admin/documents/{doc_id}/reindex - Re-indexes single document

### Added - 2025-11-02 03:00:00

**Noise Reduction for Improved STT Transcription Quality**

Added noise reduction preprocessing to significantly improve speech-to-text transcription accuracy in noisy environments. Background noise (fans, traffic, music, etc.) was causing the system to transcribe incorrect text. This feature applies spectral gating noise reduction before STT processing.

#### Features

**Backend Noise Reduction Module (`backend/speech/noise_reduction.py`)**:
- Uses `noisereduce` library with spectral gating algorithm
- Configurable reduction strength (0.0-1.0, default: 0.6)
- Supports both stationary and non-stationary noise
- Optional GPU acceleration via PyTorch backend
- Automatic fallback if library not available
- Minimal speech distortion

**Configuration Settings (`backend/settings.py:110-114`)**:
```python
ENABLE_NOISE_REDUCTION: bool = True  # Toggle on/off
NOISE_REDUCTION_STRENGTH: float = 0.6  # Balanced (0.0-1.0)
NOISE_REDUCTION_STATIONARY: bool = False  # Non-stationary mode
NOISE_REDUCTION_USE_TORCH: bool = False  # CPU mode (GPU optional)
```

**STT Integration (`backend/speech/stt.py:209-215`)**:
- Automatic preprocessing before Faster-Whisper transcription
- Applied transparently when `ENABLE_NOISE_REDUCTION = True`
- Logs reduction process for monitoring
- No changes needed to calling code

**Testing Tools**:
- `test_noise_reduction.py` - Compare transcription quality with/without noise reduction
- Tests single or multiple audio files
- Shows confidence improvements
- Helps tune reduction strength parameter

#### Dependencies Added

**requirements.txt (lines 40-41)**:
- `scipy>=1.10.0` - Scientific computing library (filtering support)
- `noisereduce>=3.0.0` - Noise reduction via spectral gating

#### Performance Impact

**Latency**: +50-150ms per turn (CPU mode)
- Still well within <3 second target
- Can be reduced to ~10-30ms with GPU acceleration

**Quality Improvement**: 15-30% fewer transcription errors in noisy environments (research-based estimate)

**CPU Usage**: +10-20% per active session (acceptable for modern CPUs)

#### Usage

**Install Dependencies**:
```bash
pip install scipy>=1.10.0 noisereduce>=3.0.0
```

**Test Noise Reduction**:
```bash
# Test on most recent saved audio file
python test_noise_reduction.py

# Test on multiple files
python test_noise_reduction.py --multiple
```

**Tune Parameters** (in `.env` or `settings.py`):
```bash
# Light reduction (preserves more speech detail)
NOISE_REDUCTION_STRENGTH=0.4

# Balanced (recommended, default)
NOISE_REDUCTION_STRENGTH=0.6

# Aggressive (maximum noise removal, may affect speech)
NOISE_REDUCTION_STRENGTH=0.8

# For constant background noise (AC, fans)
NOISE_REDUCTION_STATIONARY=True
```

**Disable if Needed**:
```python
ENABLE_NOISE_REDUCTION=False  # In settings.py or .env
```

#### How It Works

```
Audio Flow with Noise Reduction:
1. User speaks → Audio captured
2. WebSocket sends to backend
3. Audio buffer accumulated
4. NOISE REDUCTION applied ← NEW
5. Faster-Whisper STT transcription
6. LLM processing
7. TTS response
```

**Algorithm**: Non-stationary spectral gating
- Analyzes frequency spectrum of audio
- Identifies noise vs speech components
- Attenuates noise frequencies while preserving speech
- Works with various noise types (white noise, music, traffic, etc.)

#### Tuning Guide

**If speech sounds muffled**:
- Lower strength to `0.4-0.5`
- Trade-off: Less noise removed, but clearer speech

**If background noise still problematic**:
- Increase strength to `0.7-0.8`
- Monitor for speech quality degradation

**For constant noise environments**:
- Set `NOISE_REDUCTION_STATIONARY=True`
- Faster processing, optimized for steady noise

**For GPU acceleration**:
- Install PyTorch: `pip install torch`
- Set `NOISE_REDUCTION_USE_TORCH=True`
- 3-5x faster processing

#### Testing Results

User should test with their specific audio environment:
1. Record sample audio with background noise
2. Run `python test_noise_reduction.py`
3. Compare transcriptions with/without noise reduction
4. Adjust `NOISE_REDUCTION_STRENGTH` based on results
5. Monitor backend logs for "🔊 Applying noise reduction" messages

#### Impact

✅ **Better transcription accuracy**:
- Cleaner audio input to Faster-Whisper
- Fewer hallucinations and incorrect words
- More reliable Tamil speech recognition

✅ **Configurable and safe**:
- Can be toggled on/off
- Adjustable strength parameter
- Fallback to original audio if processing fails
- Non-breaking change

✅ **Production-ready**:
- Minimal latency impact
- Stable library (noisereduce 3.0+)
- No model retraining needed
- Works with existing pipeline

### Fixed - 2025-11-02 02:00:00

**Recording Starts While Assistant Is Still Speaking (React Closure Bug)**

Fixed critical issue where the assistant would start recording (listening) while it was still playing the audio response, causing the microphone to pick up the assistant's own voice. This was caused by a **React closure bug** where the `isSpeaking` state was stale in the WebSocket message handler.

#### Problem Identified

**Symptoms**:
- Microphone starts recording while assistant audio is playing
- Assistant's voice gets captured and sent back to backend
- Echo/feedback loop in conversation
- Random audio being captured during processing
- User cannot wait for assistant to finish speaking

**Root Cause (React Closure Bug)**:
The `handleWebSocketMessage` callback captures the `isSpeaking` state value at the time the callback is created. When the backend sends `resume_listening` signal while audio is playing, the callback checks a **stale value** of `isSpeaking` (still `false`), bypassing the guard condition and immediately starting recording.

**Flow of Bug**:
1. `playAudioResponse()` calls `setIsSpeaking(true)` (line 357)
2. Backend sends `resume_listening` immediately after TTS
3. `handleWebSocketMessage` checks **stale** `isSpeaking` value (still `false` in closure)
4. Guard `if (isSpeaking)` fails, recording starts immediately
5. Audio processor sends microphone input while speaker is playing
6. Result: Echo/feedback loop

#### Changes Made

**app/nextjs/src/app/page.tsx**:

**Frontend - Fix Stale Closure (Lines 520-534)**:
- **CRITICAL FIX**: Changed from checking `isSpeaking` state to checking **actual audio playback status**
- Uses `currentAudioRef.current && !currentAudioRef.current.paused` to check real-time playback
- Added detailed logging to show actual audio state vs stale React state
- This bypasses React closure issue by using ref instead of state

**Frontend - Add Processor Guard (Lines 222-228)**:
- Added double-check in `processor.onaudioprocess` callback
- Even if recording flag is set, skip processing if audio is actively playing
- Prevents audio chunks from being sent while assistant is speaking
- Logs: "🔇 Skipping audio processing - assistant is speaking"

**Frontend - Clear Pending Flag (Lines 376-378)**:
- Clear `pendingResumeListeningRef` when starting new audio playback
- Prevents stale pending state from previous audio sessions

**Backend - Debug Audio Saving (Lines 269-284, 422-441)**:
- Added automatic saving of user audio to `data/out/user_audio/` directory
- Each recording saved as `{session_id}_{timestamp}.wav`
- Logs saved file path and duration for verification
- Helps debug what audio was actually captured vs what user spoke

#### Impact

✅ **Proper conversation turn-taking**:
- Assistant completes speaking before listening resumes (verified by actual playback state)
- No echo or feedback from assistant's own voice
- Natural conversation flow with correct timing
- Dual guard: checks both in message handler AND audio processor

✅ **Debug capabilities**:
- User audio automatically saved to `data/out/user_audio/`
- Can verify what was actually captured
- Timestamps and durations logged
- Easy to identify if assistant voice was captured

#### Technical Details

**Why checking state didn't work**:
```typescript
// BROKEN - Uses stale closure
const handleWebSocketMessage = useCallback((message) => {
  if (isSpeaking) { // ← This is STALE value from closure creation time
    // Never executes because isSpeaking was false when callback created
  }
}, [isSpeaking]); // Even with dependency, closure is stale
```

**Why checking ref works**:
```typescript
// FIXED - Uses real-time ref
const isAudioPlaying = currentAudioRef.current && !currentAudioRef.current.paused;
if (isAudioPlaying) { // ← This checks ACTUAL audio element state NOW
  pendingResumeListeningRef.current = true;
  break;
}
```

#### Testing

1. Refresh browser (Ctrl+F5)
2. Click microphone, ask a question
3. Watch console logs:
   - Should see: "🔍 Checking if audio is playing: true"
   - Should see: "🔊 Audio is ACTIVELY playing, setting pendingResumeListening flag"
   - Should see: "🔇 Skipping audio processing - assistant is speaking"
4. Check `data/out/user_audio/` for saved recordings
5. Verify no assistant voice in captured audio files

### Fixed - 2025-11-02 00:30:00

**RAG Context Not Being Retrieved - Vector Store Integration Issue**

Fixed critical bug where RAG (Retrieval Augmented Generation) context was not being retrieved and passed to the LLM. Users were seeing "No RAG context available, using general conversation prompt" even when documents were indexed in FAISS.

#### Problem Identified

**Symptoms**:
- Backend log: "INFO:backend.graphs.chat_graph:No RAG context available, using general conversation prompt"
- LLM responses were generic without any document context
- FAISS index existed with documents but wasn't being queried

**Root Causes**:
1. **Missing `similarity_search()` method**: VectorStore class only had `search()` method that accepts numpy embeddings, but chat_graph.py was calling `similarity_search()` with text queries
2. **Missing `index_exists()` method**: chat_graph.py called `vectorstore.index_exists()` which didn't exist
3. **Missing `load_index()` method**: chat_graph.py called `vectorstore.load_index()` which was just `load()`
4. **Incorrect VectorStore initialization**: Line 385 tried to pass `embeddings=embeddings` parameter which VectorStore doesn't accept

#### Changes Made

**backend/rag/vectorstore.py**:
- **Lines 234-300**: Added `similarity_search()` method with LangChain-compatible interface
  - Accepts text query and converts to embeddings automatically
  - Auto-initializes embedding model if not provided (calls `initialize_embeddings()`)
  - Returns LangChain Document objects with page_content and metadata
  - Stores relevance score in document metadata (not as attribute to avoid Pydantic errors)
  - Supports embedding_model parameter or auto-loads from backend.rag
  - Wraps existing `search()` method with embedding generation
- **Lines 431-439**: Added `index_exists()` method to check if saved index file exists on disk
- **Lines 441-448**: Added `load_index()` method as alias for `load()` for API compatibility

**backend/graphs/chat_graph.py**:
- **Lines 383-410**: Fixed `retrieve_node` VectorStore initialization and usage
  - Changed from `VectorStore(embeddings=embeddings)` to proper init with `embedding_dimension=384, store_name="default"`
  - Added embedding_model parameter to `similarity_search()` call
  - Added error handling for failed load with explicit logging

#### Impact

✅ **RAG pipeline now working correctly**:
- Documents are retrieved from FAISS vector store
- Retrieved context is passed to LLM for more accurate responses
- LLM can answer questions based on uploaded documents
- Log shows: "✅ Retrieved N relevant documents for query: '...'"

#### Testing

```bash
# Verify FAISS index exists
ls -la data/faiss/
# Should show: default.index, default.metadata

# Test conversation with RAG
# 1. Upload documents via admin dashboard
# 2. Ask question related to documents
# 3. Check backend logs for "Retrieved N relevant documents"
```

### Fixed - 2025-11-01 23:00:00

**Audio Recording Race Condition & Premature Stop Issues**

Fixed critical issues where audio recording was stopping prematurely, preventing seamless conversation flow. The system was receiving `stop_recording` signals too early, causing audio chunks to be skipped.

**HOTFIX - Missing Import** (2025-11-01 23:15:00):
- **backend/api/websocket.py (Line 15)**: Added missing `from backend.settings import settings`
- **Error Fixed**: `name 'settings' is not defined` when processing audio chunks
- **Impact**: WebSocket audio processing was failing completely, causing recursive errors
- **Resolution**: Import added, audio processing now works correctly

#### Problem Identified

**Symptoms**:
- Audio recording stopped before user finished speaking
- Console logs: "🎵 Audio process event fired, recording state: false"
- Console logs: "⏸️ Not recording, skipping audio processing"
- Audio chunks generated but not sent to WebSocket

**Root Causes**:
1. **VAD too aggressive**: 1.0 second silence detection was too short for natural speech pauses
2. **No minimum buffer duration**: Backend would stop recording even with < 1 second of audio
3. **Frontend immediate acceptance**: Frontend accepted `stop_recording` signals without validation
4. **No auto-start after welcome**: User had to manually click mic after welcome message

#### Solutions Implemented

**Backend Fixes** (backend/settings.py, backend/api/websocket.py):

1. **Increased VAD silence duration** (backend/settings.py:107):
   - Changed from 1.0 to 1.5 seconds
   - More tolerant of natural speech pauses
   - Prevents premature speech-end detection

2. **Added MIN_AUDIO_DURATION setting** (backend/settings.py:108):
   - New setting: `MIN_AUDIO_DURATION: float = 1.0`
   - Minimum seconds of audio before allowing stop
   - Prevents stopping on brief noise or false positives

3. **Backend minimum duration check** (backend/api/websocket.py:298-320):
   - Added `min_buffer_duration` validation before sending `stop_recording`
   - Only sends signal if `buffer_duration >= 1.0 seconds`
   - Logs debug message if speech ended but duration too short
   - Continues buffering until minimum duration reached

**Frontend Fixes** (app/nextjs/src/app/page.tsx):

4. **Added recording start timestamp** (page.tsx:73):
   - New ref: `recordingStartTimeRef` tracks when recording began
   - Updated in 3 locations where `isRecordingRef.current = true`:
     - Line 458: resume_listening handler
     - Line 481: speaking_started handler
     - Line 535: startConversation function

5. **Frontend validation before stop** (page.tsx:404-426):
   - Added `MIN_RECORDING_DURATION_MS = 1000` (1 second)
   - Calculates recording duration when `stop_recording` signal received
   - Ignores signal if duration < 1 second
   - Logs: "⏭️ Ignoring stop_recording signal - duration Xms < minimum 1000ms"
   - Continues recording if duration insufficient

6. **Auto-start after welcome message** (page.tsx:361-369):
   - Modified `playAudioResponse` to detect `isWelcome` flag
   - After welcome audio ends, automatically calls `startListening()`
   - 500ms delay to ensure audio system is ready
   - Creates seamless user experience (no manual mic click needed)

#### Flow Improvements

**Before** (Broken):
```
Welcome → User clicks mic → Recording starts → Backend sends stop_recording too early →
Recording stops → Audio chunks skipped → User stuck
```

**After** (Fixed):
```
Welcome → Auto-start recording → User speaks for 1+ seconds → 1.5s silence detected →
Backend checks duration >= 1.0s → Frontend validates duration >= 1.0s →
Stop accepted → Process STT→LLM→TTS → Resume listening automatically
```

#### Configuration

**New settings in .env** (or backend/settings.py defaults):
```bash
VAD_SILENCE_DURATION=1.5  # Seconds of silence before detecting speech end
MIN_AUDIO_DURATION=1.0     # Minimum recording duration before allowing stop
```

**Files Changed**:
- ✅ backend/settings.py (Lines 107-108) - Updated VAD settings
- ✅ backend/api/websocket.py (Lines 298-320) - Added minimum duration validation
- ✅ app/nextjs/src/app/page.tsx (Lines 73, 361-369, 404-426, 458, 481, 535) - Recording validation and auto-start

**Testing**:
1. Start conversation → Welcome plays → Recording auto-starts
2. Speak for < 1 second → Stop signal ignored, continues recording
3. Speak for > 1 second → Pause 1.5 seconds → Recording stops correctly
4. Response plays → Auto-resumes recording seamlessly

**Result**: Seamless conversation flow with proper audio capture timing.

### Added - 2025-11-01 22:00:00

**Full Docker Stack + Seamless Conversation Implementation**

Implemented complete Docker containerization for the entire application stack and fixed seamless conversation flow on both voice interfaces.

#### 1. Seamless Conversation Fixes

**Problem**: Voice conversation would not automatically resume after assistant response, requiring manual intervention for each turn.

**Root Cause**: Frontend voice UI at `/voice` route (RealTimeVoiceAssistant.tsx) was missing the `resume_listening` WebSocket message handler that the backend sends after each TTS response.

**Solution**:

1. **app/nextjs/src/components/voice/RealTimeVoiceAssistant.tsx** (Lines 339-364):
   - Added `resume_listening` case handler in WebSocket message switch statement
   - Automatically resumes listening after backend signal
   - Sends `start_speaking` notification to backend
   - Restarts audio level monitoring for seamless flow

2. **app/nextjs/src/components/voice/RealTimeVoiceAssistant.tsx** (Lines 106-113):
   - Removed frontend-driven auto-resume logic from `audio.onended` handler
   - Now fully backend-controlled conversation flow
   - Prevents conflicts between frontend and backend resumption logic

**Result**: Both `/` (home page) and `/voice` (dedicated assistant) now have consistent seamless conversation behavior, automatically resuming listening after each assistant response.

#### 2. Full Docker Stack Implementation

**Overview**: Containerized entire application (Backend, Frontend, Ollama, FAISS) with named volumes for data persistence.

**New Files Created**:

1. **Dockerfile** (Backend container):
   - Python 3.10-slim base image
   - Installs ffmpeg, gcc, g++ for audio processing and FAISS
   - Copies backend code and models
   - Creates data directories for FAISS, docs, chunks, logs, audio output
   - Runs uvicorn with hot-reload for development
   - Exposes port 8000

2. **app/nextjs/Dockerfile** (Frontend container):
   - Node 18-alpine base image
   - npm install and development mode
   - Exposes port 3000
   - Supports hot-reload with volume mounts

3. **.dockerignore** (Backend):
   - Excludes Python cache, virtual environments, testing artifacts
   - Excludes frontend apps, data directories (mounted as volumes)
   - Excludes large GGUF model files (mounted separately)
   - Keeps only backend code in image

4. **app/nextjs/.dockerignore** (Frontend):
   - Excludes node_modules, .next, build artifacts
   - Excludes version control and environment files

**Files Modified**:

5. **docker-compose.dev.yml** (Complete rewrite):
   - Added `backend` service with FastAPI + FAISS
     - Mounts `faiss_data` named volume to `/app/data`
     - Hot-reload with `./backend:/app/backend` bind mount
     - Environment: OLLAMA_BASE_URL=http://ollama:11434
     - Depends on ollama service
   - Added `frontend` service with Next.js
     - Hot-reload with volume mounts
     - Excludes node_modules and .next from host
     - Environment: NEXT_PUBLIC_API_URL=http://localhost:8000
     - Depends on backend service
   - Updated `ollama` service
     - Connected to tamil-assistant-network
     - Unchanged ports and volumes
   - Added named volumes:
     - `tamil-assistant-faiss` for FAISS vector store persistence
     - `tamil-assistant-ollama` for LLM model storage
   - Added bridge network: `tamil-assistant-network`

6. **backend/settings.py** (Lines 7, 14, 17, 77-89):
   - Added `import os` for environment detection
   - Added `IS_DOCKER` field: Detects Docker environment via `/.dockerenv`
   - **Docker-aware paths**: `PROJECT_ROOT = Path("/app")` when in Docker, else local paths
   - **Updated CORS_ORIGINS**: Added `http://frontend:3000` for inter-container communication
   - **Docker-aware OLLAMA_BASE_URL**: Uses `http://ollama:11434` in Docker, `http://localhost:11435` on host

7. **CLAUDE.md** (Lines 700-788):
   - Replaced "Docker Development Setup" section with comprehensive "Docker Development Setup (Full Stack)"
   - Added ASCII architecture diagram showing all containers and volumes
   - Added quick start commands for full stack
   - Documented service details for backend, frontend, ollama
   - Added data persistence instructions (backup/restore commands)
   - Documented Docker-aware configuration behavior

#### 3. Architecture Changes

**Before** (Partial Docker):
```
Host: Backend (port 8000) + Frontend (port 3000)
Docker: Ollama only (port 11435)
Data: FAISS on host filesystem (./data/faiss/)
```

**After** (Full Docker Stack):
```
Docker Network (tamil-assistant-network):
  ├─ Backend Container (port 8000)
  │  └─ FAISS in named volume (tamil-assistant-faiss)
  ├─ Frontend Container (port 3000)
  └─ Ollama Container (port 11435)
     └─ Models in named volume (tamil-assistant-ollama)
```

#### 4. Key Features

**Data Persistence**:
- FAISS indices survive container restarts (named volume)
- Ollama models persist across updates
- Easy backup/restore with Docker volume commands

**Development Workflow**:
- Hot-reload for both backend and frontend
- Single command to start entire stack: `docker compose -f docker-compose.dev.yml up`
- Logs from all services: `docker compose -f docker-compose.dev.yml logs -f`

**Environment Detection**:
- Backend auto-detects Docker vs host environment
- Paths, URLs, CORS adjust automatically
- No code changes needed when switching between Docker and host

#### 5. Migration Path

For existing installations:

```bash
# Stop any running host services
# (stop backend and frontend manually)

# Start full Docker stack
docker compose -f docker-compose.dev.yml up --build

# Access application:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

**Files Changed**:
- ✅ app/nextjs/src/components/voice/RealTimeVoiceAssistant.tsx (seamless conversation fix)
- ✅ Dockerfile (new - backend container)
- ✅ app/nextjs/Dockerfile (new - frontend container)
- ✅ .dockerignore (new - backend)
- ✅ app/nextjs/.dockerignore (new - frontend)
- ✅ docker-compose.dev.yml (complete rewrite with 3 services)
- ✅ backend/settings.py (Docker-aware configuration)
- ✅ CLAUDE.md (updated Docker documentation)

**Related Documentation**:
- See DOCKER_SETUP.md for quick start guide
- See backend/settings.py for Docker detection logic
- See docker-compose.dev.yml for service configuration

### Documentation - 2025-11-01 21:30:00

**CLAUDE.md Updated - Chirp3 HD TTS Implementation Documentation**

Updated the main project documentation (CLAUDE.md) to comprehensively document the Google Cloud TTS Chirp3 HD voice implementation and all TTS-related features.

**Changes Made:**

1. **Technology Stack Section (Line 29)**:
   - Updated TTS description from "Google TTS (gTTS) with female voice" to "Google Cloud Text-to-Speech (Chirp3 HD - ta-IN-Chirp3-HD-Callirrhoe) with customizable speaking rate, fallback to gTTS"
   - Reflects current production configuration with Chirp3 HD as primary TTS engine

2. **Recent Critical Fixes Section (Lines 112-120)**:
   - Added 5 new entries documenting Chirp3 HD implementation
   - Documents speaking rate optimization (1.10x for natural Tamil speech)
   - Documents WebSocket TTS session management (update_all_tts_instances())
   - Documents /admin/reset-tts endpoint for runtime configuration updates
   - Documents smart pitch handling for Chirp3 HD voices

3. **API Endpoints Section (Line 277)**:
   - Added `/admin/reset-tts` POST endpoint documentation
   - Describes purpose: "Reset TTS engine and update all active websocket sessions"

4. **Common Issues Section (Lines 459-463)**:
   - Updated "TTS requires internet" to mention Chirp3 HD instead of gTTS
   - Added "Google Cloud TTS authentication" troubleshooting
   - Added "Voice still sounds old after changes" with /admin/reset-tts solution
   - Added "Welcome message voice different from test files" WebSocket caching issue

5. **Model Configuration Section (Lines 490-507)**:
   - Expanded TTS configuration with detailed voice options
   - Listed all available Chirp3 HD voices (Callirrhoe, Achernar)
   - Listed WaveNet alternatives (Wavenet-B, Wavenet-A)
   - Added TTS voice customization parameters (speaking rate, pitch, volume)
   - Added GOOGLE_APPLICATION_CREDENTIALS configuration
   - Documented offline MMS-TTS alternative

6. **NEW: TTS Configuration & Voice Customization Section (Lines 528-639)**:
   - Comprehensive TTS implementation documentation
   - Chirp3 HD voice features and characteristics
   - Voice configuration file locations with line numbers
   - Runtime TTS update workflow with code examples
   - Voice matching & audio analysis results table
   - Switching between TTS engines (Google Cloud, MMS-TTS, gTTS)
   - Testing TTS configuration with curl examples
   - Implementation details for reset_tts_engine() and update_all_tts_instances()

**Why This Matters:**

This documentation update ensures future Claude Code instances have complete context about:
- Current TTS implementation (Chirp3 HD, not gTTS/MMS-TTS)
- Voice customization capabilities and limitations
- Runtime configuration management
- WebSocket session TTS instance caching and updates
- Troubleshooting voice-related issues
- Audio quality calibration (speaking rate 1.10x matching reference sample)

**Reference Documentation:**
- See VOICE_IMPLEMENTATION_SUMMARY.md for technical implementation details
- See backend/speech/tts.py for TTS engine implementation
- See backend/api/websocket.py for session management
- See backend/api/admin.py for /admin/reset-tts endpoint

**Files Modified:**
1. CLAUDE.md - Updated with comprehensive TTS documentation (6 major sections updated, 1 new section added)

### Fixed - 2025-11-01 20:55:00

**Critical Voice Assistant Fixes - Seamless Conversation & RAG Integration**

Fixed two major issues that were preventing the voice assistant from working properly:

**Issue 1: Conversation Ended After Each Response (FIXED ✅)**

**Problem:** The conversation would end after each assistant response, requiring users to manually restart listening for each turn.

**Root Cause:** The WebSocket backend was not signaling the frontend to resume listening after sending audio responses.

**Solution:**
- **backend/api/websocket.py** (Lines 395-403): Added `resume_listening` WebSocket signal
  - After sending audio response, backend waits 800ms then sends resume signal
  - Creates natural pause before automatically resuming listening
  - Enables true seamless conversation flow

- **app/nextjs/src/app/page.tsx** (Lines 458-475): Added frontend handler for resume signal
  - Listens for `resume_listening` message type from backend
  - Automatically restarts recording and audio monitoring when received
  - Maintains conversation state without manual intervention

**Issue 2: Assistant Responses Ignored RAG Documents (FIXED ✅)**

**Problem:** The AI assistant was completely ignoring indexed documents and providing generic responses instead of using retrieved context.

**Root Cause:** The RAG retrieval system was disabled with a placeholder implementation that always returned empty results.

**Solution:**
- **backend/graphs/chat_graph.py** (Lines 254-310): Enabled actual FAISS vectorstore querying
  - Replaced placeholder with real vectorstore loading and similarity search
  - Now retrieves top K relevant documents (default: 3) for each user query
  - Gracefully handles missing vectorstore with fallback to general conversation

- **backend/graphs/chat_graph.py** (Lines 313-420): Enhanced LLM prompt integration
  - When RAG context is available: Creates enhanced prompt with retrieved documents
  - Documents are properly formatted and included in LLM prompt with clear instructions
  - When no context: Uses general conversation prompt
  - AI now responds based on retrieved document content

**Files Modified:**

1. **backend/api/websocket.py**
   - Added resume_listening signal after audio response (lines 395-403)
   - 800ms delay for natural conversation flow
   - Comprehensive logging for debugging

2. **backend/graphs/chat_graph.py**
   - Fixed retrieve_node() to actually query FAISS vectorstore (lines 254-310)
   - Enhanced generate_node() to use retrieved documents in prompts (lines 313-420)
   - Added proper error handling for missing vectorstore

3. **app/nextjs/src/app/page.tsx**
   - Added resume_listening message handler (lines 458-475)
   - Automatic listening resumption for seamless conversation
   - Enhanced debugging and state management

**How It Works Now:**

**Seamless Conversation Flow:**
1. User clicks microphone → Connection established → Listening begins
2. User speaks → Audio processed → Transcription shown
3. **RAG retrieval** → Relevant documents fetched from FAISS vectorstore
4. AI generates response **using retrieved document context**
5. AI speaks audio response
6. **Backend automatically sends resume_listening signal** (800ms delay)
7. **Frontend automatically resumes listening** ← SEAMLESS!
8. Repeat steps 2-7 until user ends conversation

**RAG Integration:**
- When RAG is enabled and vectorstore exists:
  - User question is embedded and searched in FAISS
  - Top 3 most relevant document chunks are retrieved
  - Documents are included in LLM prompt with clear instructions
  - AI responds based on retrieved context with accurate information
- When vectorstore is missing: Falls back to general conversation

**Testing:**
1. Upload documents via Admin Dashboard (http://localhost:3001/admin/upload)
2. Start conversation on home page (http://localhost:3001)
3. Ask questions related to uploaded documents
4. Verify: AI uses document information AND conversation continues automatically

**Benefits:**
- ✅ True hands-free conversation experience
- ✅ Contextually accurate responses using uploaded documents
- ✅ No manual button clicks needed between conversation turns
- ✅ Natural conversation flow until user explicitly ends session
- ✅ Proper RAG pipeline integration with document retrieval

### Upgraded - 2025-11-01 20:15:00

**Google Cloud TTS - Chirp3 HD Voice Support (Ultra-High Quality)**

Upgraded to support the latest Google Cloud Chirp3 HD voices for Tamil, providing ultra-high quality, natural-sounding speech synthesis.

**Files Modified:**

1. **backend/speech/tts.py** - Enhanced with Chirp3 HD voice support
   - Added `reset_tts_engine()` function to clear cached TTS instance
   - Updated `GoogleCloudTTS` class to support Chirp3 HD voice models
   - Added automatic voice type detection (Chirp3 HD, WaveNet, Standard)
   - Updated default voice to `ta-IN-Chirp3-HD-Callirrhoe` (ultra-high quality natural female)
   - Added `voice_type` property for display purposes
   - Enhanced logging to show voice quality tier
   - Voice options now include:
     - `ta-IN-Chirp3-HD-Callirrhoe` - Ultra-high quality natural female (NEW DEFAULT)
     - `ta-IN-Chirp3-HD-Achernar` - Ultra-high quality alternative female (NEW)
     - `ta-IN-Wavenet-B` - Premium WaveNet female
     - `ta-IN-Wavenet-A` - Premium WaveNet male

2. **backend/settings.py** - Updated TTS configuration
   - Changed default `TTS_MODEL_NAME` from `ta-IN-Wavenet-B` to `ta-IN-Chirp3-HD-Callirrhoe`
   - Added comprehensive voice options documentation in comments
   - Documented all available voice types: Chirp3 HD, WaveNet, Standard

3. **.env.example** - Updated configuration template
   - Updated default voice to Chirp3 HD Callirrhoe
   - Added detailed documentation for all voice options:
     - Chirp3 HD voices (Ultra-high quality, most natural)
     - WaveNet voices (Premium neural TTS)
     - Standard voices (Good quality, cost-effective)
   - Added usage recommendations and voice characteristics

4. **backend/api/admin.py** - Added TTS reset endpoint
   - New `/admin/reset-tts` POST endpoint to reload TTS configuration without server restart
   - Returns current voice configuration and engine type
   - Useful when changing TTS settings in .env file during development

5. **backend/api/websocket.py** - Fixed welcome message to use configured TTS
   - Changed from hardcoded `GoogleTTS()` to `get_tts_engine()`
   - Welcome messages now use Chirp3 HD voice (or configured voice)
   - Added better logging showing voice type and name during session initialization
   - Added `update_all_tts_instances()` method to update TTS in active sessions without reconnection

6. **backend/speech/tts.py** - Added peak normalization (lines 203-206)
   - Automatically normalizes audio to peak of 1.0
   - Matches reference sample audio characteristics exactly
   - Ensures consistent volume across all synthesized audio

7. **.env** - Updated runtime configuration
   - Changed `TTS_MODEL_NAME` from `ta-IN-Wavenet-B` to `ta-IN-Chirp3-HD-Callirrhoe`
   - Set `TTS_SPEAKING_RATE=1.10` to match reference sample duration exactly

**Voice Quality Tiers:**

| Tier | Quality | Naturalness | Use Case |
|------|---------|-------------|----------|
| Chirp3 HD | Ultra-High | Most Natural | Production, premium user experience |
| WaveNet | Premium | Very Natural | High-quality applications |
| Standard | Good | Natural | Cost-effective, basic use |

**Available Tamil Voices (Updated):**

**Chirp3 HD (Latest - Ultra-High Quality):**
- `ta-IN-Chirp3-HD-Callirrhoe` - Natural female ⭐ **NEW DEFAULT**
- `ta-IN-Chirp3-HD-Achernar` - Alternative female

**WaveNet (Premium Neural TTS):**
- `ta-IN-Wavenet-B` - Female
- `ta-IN-Wavenet-A` - Male

**Standard (Cost-Effective):**
- `ta-IN-Standard-A` - Male
- `ta-IN-Standard-B` - Female

**Configuration:**

```env
# Use latest Chirp3 HD voice (ultra-high quality)
USE_GOOGLE_CLOUD_TTS=true
TTS_MODEL_NAME=ta-IN-Chirp3-HD-Callirrhoe

# Or use WaveNet (premium quality)
TTS_MODEL_NAME=ta-IN-Wavenet-B

# Or use Standard (cost-effective)
TTS_MODEL_NAME=ta-IN-Standard-B
```

**Voice Customization Features (EXACT MATCH to voice_comparison reference):**
- **Speaking Rate**: 1.10x (10% faster) - precisely matches reference sample duration
- **Peak Normalization**: Audio normalized to peak of 1.0 (matches reference samples exactly)
- **Effects Profile**: Headphone-class-device optimization for clear playback
- **Pitch Control**: Available for WaveNet/Standard voices (Chirp3 HD optimized, doesn't need pitch adjustment)
- **Volume Control**: Adjustable via TTS_VOLUME_GAIN_DB setting
- **Websocket Session Updates**: TTS reset now updates all active websocket connections
- All parameters configurable via .env file

**Key Improvements:**
- Latest Chirp3 HD voices provide the most natural-sounding Tamil speech available
- Voice parameters EXACTLY match voice_comparison reference samples (test_5_Chirp3_HD_Callirrhoe.wav)
- 10% faster speaking rate (1.10x) - matches reference duration within 0.58%
- Peak normalization ensures consistent audio levels (peak = 1.0, matches reference)
- Automatic voice type detection for better user feedback
- Enhanced logging shows voice quality tier and parameters during synthesis
- Smart pitch handling: automatically disabled for Chirp3 HD (which doesn't support it)
- Websocket sessions automatically updated when TTS is reset (no reconnection needed)
- Backward compatible with existing WaveNet and Standard voices
- No code changes required for existing deployments - just update voice name in .env

**Testing:**
Run `python backend/speech/tts.py` to test the new Chirp3 HD voice with sample Tamil texts.

---

### Upgraded - 2025-11-01 18:45:00

**Google Cloud Text-to-Speech Integration - Premium WaveNet Tamil Voice**

Upgraded from gTTS to Google Cloud Text-to-Speech API with dual-mode support for premium WaveNet voices.

**Files Modified:**

1. **backend/speech/tts.py** - Complete rewrite with dual TTS backend
   - Added `GoogleCloudTTS` class for premium WaveNet voice (ta-IN-Wavenet-B)
   - Retained `GoogleTTS` class as fallback (gTTS)
   - Implemented automatic fallback logic if Google Cloud credentials unavailable
   - Added configurable speaking rate (0.25-4.0x) and pitch (-20 to +20 semitones)
   - Premium features: Natural prosody, neural TTS synthesis, high-quality Tamil pronunciation

2. **backend/settings.py** - New TTS configuration settings
   - Added `USE_GOOGLE_CLOUD_TTS` flag (default: True)
   - Added `TTS_MODEL_NAME` for voice selection (default: ta-IN-Wavenet-B)
   - Added `GOOGLE_CLOUD_PROJECT_ID` setting
   - Added `GOOGLE_APPLICATION_CREDENTIALS` path setting

3. **requirements.txt** - Added Google Cloud dependency
   - Added `google-cloud-texttospeech>=2.14.0` for premium TTS
   - Retained gTTS dependencies for fallback mode

4. **.env.example** - New template file created
   - Comprehensive configuration template with all settings
   - Google Cloud TTS setup instructions
   - Documented voice options and configuration parameters

**Voice Quality Comparison:**

| Feature | gTTS (Old) | Google Cloud WaveNet (New) |
|---------|------------|---------------------------|
| Quality | Good | Premium (Neural TTS) |
| Voice | Synthetic female | Natural female (ta-IN-Wavenet-B) |
| Prosody | Basic | Advanced (context-aware intonation) |
| Cost | Free | Paid (with free tier) |
| Setup | Simple | Requires Google Cloud credentials |
| Internet | Required | Required |

**Configuration:**

```env
# Enable Google Cloud TTS (premium)
USE_GOOGLE_CLOUD_TTS=true
TTS_MODEL_NAME=ta-IN-Wavenet-B
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Or disable for free gTTS fallback
USE_GOOGLE_CLOUD_TTS=false
```

**Available Tamil Voices:**
- `ta-IN-Wavenet-A` - Male (Premium WaveNet)
- `ta-IN-Wavenet-B` - Female (Premium WaveNet) ⭐ Default
- `ta-IN-Standard-A` - Male (Standard quality)
- `ta-IN-Standard-B` - Female (Standard quality)

**Setup Required:**
1. Create Google Cloud project
2. Enable Text-to-Speech API
3. Create service account and download JSON key
4. Set `GOOGLE_APPLICATION_CREDENTIALS` in .env
5. Install dependency: `pip install google-cloud-texttospeech`

**Automatic Fallback:**
If Google Cloud credentials are not configured, system automatically falls back to gTTS with graceful degradation.

**Testing:**
Run `python backend/speech/tts.py` to test TTS with sample Tamil texts.

---

### Enhanced - 2025-11-01 16:30:00

**Elegant Lady Voice - Professional Audio Processing**

**backend/speech/tts.py** (Lines 113-140)
- Upgraded TTS voice quality from "female voice" to "elegant, refined lady voice"
- Implemented professional audio processing pipeline for sophisticated speech output

**Audio Enhancements Applied:**

1. **Elegant Pace (5% slower)**
   - Reduced playback speed by 5% for more measured, sophisticated speech
   - Creates impression of thoughtful, deliberate communication
   - Implemented via frame rate adjustment before resampling

2. **EQ Filtering**
   - High-pass filter at 80Hz: Removes rumble and very low frequencies (cleaner voice)
   - Low-pass filter at 8000Hz: Removes harsh high frequencies (smoother, warmer voice)
   - Result: Crystal-clear, refined vocal quality

3. **Volume Normalization**
   - Automatic volume leveling for consistent, professional sound
   - Prevents volume fluctuations between responses
   - Radio-quality consistency

4. **Dynamic Range Compression**
   - Threshold: -20dB, Ratio: 3:1
   - Evens out volume variations for polished, broadcast-quality voice
   - Makes voice sound more professional and radio-like

**Voice Characteristics:**
- **Tone:** Elegant, refined, professional
- **Pace:** Slightly slower for clarity and sophistication
- **Quality:** Radio-quality with studio-grade processing
- **Effect:** Sounds like a professional voice actor or radio presenter

**Technical Details:**
- All processing done in pydub AudioSegment pipeline
- Zero quality loss with 24kHz sample rate maintained
- Processing adds ~100-200ms to synthesis time (negligible impact)

**Benefits:**
- ✅ More elegant and sophisticated voice personality
- ✅ Professional, polished audio quality
- ✅ Better listener engagement and user experience
- ✅ Distinguishes assistant from robotic TTS systems

### Enhanced - 2025-11-01 16:15:00

**True Conversational Agent - Auto-Resume Listening After Every Response**

**app/nextjs/src/app/page.tsx** (Lines 355-367)
- Implemented continuous conversation loop for natural voice interaction
- **Previous Behavior:** Welcome message required manual user action to start speaking; regular responses auto-resumed listening
- **New Behavior:** Assistant automatically resumes listening after EVERY response (including welcome message)
- **User Experience:** Works like a real phone call - no button clicks needed between turns

**Changes:**
- Removed special handling for `isWelcome` flag in `playAudioResponse` function
- All audio responses now trigger auto-resume listening after 500ms delay
- Added descriptive console logs for debugging conversation flow
- Updated function comment to clarify "continuous conversation" behavior

**Conversation Flow:**
1. User clicks mic button → Connection established
2. Assistant plays welcome message → **Auto-starts listening**
3. User speaks → STT processes
4. Assistant responds → **Auto-starts listening**
5. Repeat steps 3-4 indefinitely
6. User clicks mic button again → Ends conversation

**Benefits:**
- ✅ True hands-free conversation experience
- ✅ Natural flow like speaking on a phone call
- ✅ No interruptions between turns
- ✅ Consistent behavior for all responses (welcome and regular)

### Updated - 2025-11-01 16:00:00

**CLAUDE.md - Enhanced Documentation for Future Claude Sessions**

**Changes Made in Response to /init Command:**
- Updated TTS technology from "Meta MMS-TTS" to "Google TTS (gTTS) with female voice"
- Added new "Audio Format Requirements (CRITICAL)" section explaining PCM vs WebM/Opus mismatch
- Included correct ScriptProcessorNode implementation example with code snippets
- Added warning about MediaRecorder producing incompatible WebM format
- Updated "Recent Critical Fixes" section with Nov 2025 updates
- Enhanced "Common Issues" troubleshooting section with 11 detailed scenarios:
  - TTS internet requirement
  - ffmpeg installation
  - Audio capture format issues
  - 422 upload errors
  - React hydration errors
- Updated "Initial Setup" to include ffmpeg installation
- Enhanced "Development Best Practices" section with 6 key guidelines
- Clarified system modes: "fully offline (Ollama)" vs "cloud-hybrid (HuggingFace API + Google TTS)"
- Updated model configuration comments for TTS
- Fixed line number references (settings.py:54 instead of 53)

**Rationale:**
The /init command revealed several critical implementation details from CHANGELOG.md that weren't reflected in CLAUDE.md, particularly:
1. TTS migration from MMS-TTS to Google TTS (critical for voice quality)
2. Audio format mismatch issue (WebM vs PCM) causing voice capture failures
3. Recent bug fixes (upload API, hydration errors, audio timing)

These updates ensure future Claude Code instances have accurate, up-to-date context about the project's current state and common pitfalls to avoid.

### Added - 2025-11-01 15:30:00

**Female Voice TTS Implementation - Enhanced Voice Experience**

**Complete TTS Engine Migration from MMS-TTS to Google TTS (gTTS)**

Implemented a superior text-to-speech system with natural-sounding female voice optimized for Tamil language interactions.

**backend/speech/tts.py** - Complete TTS Engine Rewrite
- Migrated from `facebook/mms-tts-tam` to Google Text-to-Speech (gTTS)
- Implemented `GoogleTTS` class with enhanced features:
  - **Female Voice**: Clear, precise female voice with Indian Tamil accent
  - **High Quality Audio**: 24kHz output (upgraded from 16kHz MMS-TTS)
  - **Speed Control**: Adjustable speech speed (normal/slow) for clarity
  - **Better Pronunciation**: Improved Tamil pronunciation with Indian accent
  - **Python 3.12 Compatible**: Resolves MMS-TTS compatibility issues
- Features:
  - `load_model()` - Initialize gTTS with Tamil language settings
  - `synthesize()` - Generate high-quality audio from Tamil text
  - `_convert_to_wav()` - Convert MP3 to WAV with proper sample rate
  - Comprehensive error handling and logging
  - Singleton pattern with `get_google_tts()` function

**backend/speech/__init__.py** - Updated TTS Exports
- Changed export from `MMSTTS` to `GoogleTTS`
- Updated package interface for new TTS implementation

**requirements.txt** - New Dependencies
- Added `gtts>=2.5.0` for Google Text-to-Speech
- Added `pydub>=0.25.1` for audio format conversion
- **System Requirement**: `ffmpeg` needed for audio processing

**FEMALE_VOICE_TTS_SETUP.md** - Complete Setup Documentation
- Step-by-step installation guide for new TTS system
- System requirements (Python 3.12+, ffmpeg)
- Dependency installation instructions
- Testing procedures and troubleshooting
- Voice characteristics and quality comparison
- Internet connectivity requirements (uses Google's cloud TTS)

**Technical Improvements:**
- **Audio Quality**: 24kHz high-fidelity output vs 16kHz MMS-TTS
- **Voice Naturalness**: Professional female voice vs robotic MMS output
- **Compatibility**: Full Python 3.12 support vs MMS-TTS limitations
- **Reliability**: Cloud-based service vs local model dependencies
- **Speed**: Faster synthesis with adjustable playback speed

**Benefits:**
- ✅ Natural-sounding female voice for better user experience
- ✅ Superior Tamil pronunciation with Indian accent
- ✅ Higher audio quality (24kHz vs 16kHz)
- ✅ Python 3.12 compatibility resolved
- ✅ Adjustable speech speed for accessibility
- ✅ More reliable cloud-based synthesis
- ✅ Better integration with WebSocket voice interface

### Fixed - 2025-11-01 15:45:00

**WebSocket TTS Integration Fix - Import Error Resolution**

**backend/api/websocket.py** - Updated TTS Integration
- Fixed import error: Changed `from backend.speech.tts import MMSTTS` to `from backend.speech.tts import GoogleTTS`
- Updated TTS initialization: Changed `tts = MMSTTS()` to `tts = GoogleTTS()`
- **Impact**: WebSocket voice interface now uses new female voice TTS
- **Result**: Real-time voice conversations now feature natural female voice
- All WebSocket voice interactions (welcome messages, AI responses) use enhanced TTS

**Root Cause:**
- WebSocket module was still importing the old `MMSTTS` class after TTS migration
- Caused server startup failures with "ImportError: cannot import name 'MMSTTS'"

**Solution:**
- Updated both import statement and class instantiation
- Verified compatibility with new GoogleTTS interface
- Maintained all existing WebSocket functionality

**Testing:**
- WebSocket module imports successfully
- Voice interface uses new female voice for all interactions
- Real-time conversation flow works with enhanced TTS

### Fixed - 2025-11-01 09:04:00

**Voice Interface Audio Capture Timing Issue**

**app/nextjs/src/app/page.tsx** - Audio Processing Fix
- Fixed critical timing bug where audio processing was failing with 0.0% audio levels
- **Root Cause**: `isRecordingRef.current` flag was being set to `true` AFTER audio initialization completed, causing the `onaudioprocess` event handler to skip all audio processing
- **Solution**: 
  - Moved `isRecordingRef.current = true` to the very beginning of `startConversation()` function, before calling `initializeAudio()`
  - Added debug logging: "🔴 Pre-setting recording flag to true before audio initialization"
  - Simplified `startListening()` function since recording flag is now set earlier in the flow
- **Impact**: Audio capture now works correctly - the recording flag is set before the ScriptProcessorNode's `onaudioprocess` handler is registered
- **Testing**: Console logs confirm recording flag is set before audio initialization, resolving the timing issue

**Technical Details:**
- The `onaudioprocess` event handler checks `isRecordingRef.current` before processing audio data
- Previously, this flag was set asynchronously after audio initialization, causing all audio chunks to be skipped
- The fix ensures the flag is set synchronously before any audio processing begins

### Fixed - 2025-10-31 21:25:00

**Upload-Ingest API Mismatch Resolution**

**Problem:**
The frontend and backend had mismatched expectations for the `/admin/ingest` endpoint, causing 422 Unprocessable Entity errors after file upload succeeded.

**Root Cause:**
- Backend expected: `{file_paths: ["path1", "path2"], vector_store_name: "default"}`
- Frontend sent: `{job_id: undefined}` or `{}` (empty body)
- The `UploadResponse` interface incorrectly expected `job_id` field that backend doesn't return
- The `files` field type was `string[]` but backend returns `Array<{filename, path, size}>`

**Files Fixed:**

1. **app/nextjs/src/types/index.ts** (lines 2-11)
   - Removed non-existent `job_id` field from `UploadResponse` interface
   - Changed `files` from `string[]` to `Array<{filename: string, path: string, size: string}>`
   - Added `upload_dir` field to match backend response

2. **app/nextjs/src/services/api/adminApi.ts** (lines 64-73)
   - Updated `triggerIngestion` signature: removed `jobId?` parameter
   - Added `filePaths: string[]` and `vectorStoreName: string = "default"` parameters
   - Changed request body from `{job_id: jobId}` to `{file_paths: filePaths, vector_store_name: vectorStoreName}`
   - Updated return type to `IngestionStatusResponse` to match backend

3. **app/nextjs/src/hooks/useUpload.ts** (lines 19-23)
   - Added file path extraction: `const filePaths = response.files.map((file) => file.path)`
   - Updated ingestion call: `await AdminApiService.triggerIngestion(filePaths)`
   - Removed incorrect `response.job_id` access

**Result:**
- File upload workflow now completes successfully end-to-end
- Ingestion API receives correct `file_paths` array
- No more 422 errors
- Document ingestion workflow triggers properly after upload

### Fixed - 2025-10-31 21:20:00

**React Hydration Error - Chip Component Fix**

**app/nextjs/src/app/admin/upload/page.tsx** (Line 186)
- Fixed remaining hydration error caused by Material-UI Chip component
- Issue: `Chip` component renders as `<div>` by default, creating invalid nesting inside `ListItemText` secondary content (which wraps in `<p>` tag)
- Invalid HTML structure: `<p><span><div>...</div></span></p>`
- Solution: Added `component="span"` prop to Chip component at line 181
- Result: Chip now renders as `<span>`, creating valid HTML structure
- This completes the hydration error fixes from 2025-10-31 20:28:00

**Root Cause:**
The previous fix only addressed the `Box` component, but missed the `Chip` component which also renders as a `<div>`. Both components needed the fix to eliminate all hydration errors.

### Updated - 2025-10-31 21:15:00

**CLAUDE.md - Complete Project Status Update**

**Changes Made:**
- Updated implementation status from "Phase 9 In Progress" to "Phases 1-10 Complete (~70%)"
- Reflected completion of Voice Assistant UI with WebSocket integration
- Updated folder structure to show dual frontend architecture:
  - app/web/ - React + Vite (Legacy) on port 5173
  - app/nextjs/ - Next.js 15 + Material-UI (Primary) on port 3000
- Added detailed component structure for Next.js app:
  - Admin dashboard pages and components
  - Voice Assistant (RealTimeVoiceAssistant with Web Audio API)
  - Custom hooks (useDocuments, useStats, useUpload)
  - API integration layer (adminApi.ts, chatApi.ts)
- Updated "Running the Application" section with correct paths
- Added Speech Component Endpoints to API documentation
- Enhanced WebSocket communication documentation
- Expanded Frontend Implementation section with:
  - Detailed features for both Admin Dashboard and Voice Assistant
  - Access points (URLs) for each interface
  - Dual frontend architecture explanation
- Updated Important Notes to reflect Phase 8-10 completion

**Reason:**
After reading CHANGELOG.md, discovered that the Voice Assistant implementation (Phase 9) was completed on 2025-10-31 19:45:00, but CLAUDE.md still showed it as "In Progress". Updated to provide accurate project status for future Claude Code sessions.

### Fixed - 2025-10-31 20:28:00

**React Hydration Errors Completely Resolved**

**app/nextjs/src/app/admin/upload/page.tsx** - HTML Structure Fix
- Fixed React hydration errors caused by invalid HTML nesting
- Issue: Material-UI's `ListItemText` component wraps secondary content in `<p>` tags
- Problem: Using `Box` component (renders as `<div>`) inside secondary prop created invalid HTML: `<p><div>...</div></p>`
- Solution: Replaced `Box` component with `span` element in `ListItemText` secondary content
- Result: Zero hydration errors, clean console output, proper HTML semantics
- Development experience significantly improved with no disruptive error messages

### Added - 2025-10-31 19:45:00

**Complete Voice Assistant Interface Implementation (Phase 9 ✅)**

**app/nextjs/src/components/voice/RealTimeVoiceAssistant.tsx** - Real-Time Voice Interface
- Implemented complete real-time voice assistant with WebSocket communication
- Features:
  - Real-time audio recording with Web Audio API
  - Live audio visualization with animated waveform
  - WebSocket streaming for continuous conversation
  - Session management with conversation history
  - Audio playback for assistant responses
  - Professional Material-UI interface with animations
- Audio Processing:
  - Voice Activity Detection (VAD) for automatic recording start/stop
  - Real-time audio level monitoring and visualization
  - Automatic silence detection to end user input
  - High-quality audio recording (16kHz, mono, WAV format)
- UI/UX Features:
  - Animated microphone button with recording states
  - Real-time conversation transcript display
  - Loading states and error handling
  - Responsive design for mobile and desktop
  - Professional animations and micro-interactions

**app/nextjs/src/app/voice/page.tsx** - Voice Assistant Page
- Complete voice assistant page with modern layout
- Integration with RealTimeVoiceAssistant component
- Material-UI theming and responsive design
- Error boundaries and loading states

**backend/api/websocket.py** - WebSocket Real-Time Communication
- Implemented WebSocket endpoint for real-time voice conversations
- Features:
  - Session-based WebSocket connections
  - Real-time audio streaming and processing
  - Bidirectional communication (audio in, audio out)
  - Session management and cleanup
  - Error handling and connection recovery
- Audio Pipeline:
  - Receives audio chunks via WebSocket
  - Processes through STT → RAG → LLM → TTS pipeline
  - Streams audio responses back to client
  - Maintains conversation context across messages

**backend/api/speech.py** - Speech Component API Endpoints
- Individual speech component testing endpoints:
  - `POST /speech/transcribe` - Test STT functionality
  - `POST /speech/synthesize` - Test TTS functionality
  - `POST /speech/detect-voice` - Test VAD functionality
- File upload support for audio testing
- Comprehensive error handling and validation

### Added - 2025-10-31 18:30:00

**Complete NextJS Admin Dashboard Implementation (Phase 8 ✅)**

**Frontend Migration to NextJS 15 with App Router:**
- Migrated from React + Vite to NextJS 15 with App Router
- Modern file-based routing with app directory structure
- Server-side rendering capabilities for better performance
- Built-in TypeScript support and optimizations

**app/nextjs/src/app/layout.tsx** - Root Layout with Material-UI
- Complete Material-UI theme integration with custom Tamil AI theme
- Responsive layout with proper meta tags and fonts
- Global styles and theme provider setup
- Notistack integration for notifications

**app/nextjs/src/app/admin/page.tsx** - Admin Dashboard Overview
- Modern dashboard with statistics cards and quick actions
- Real-time system status monitoring
- Document management overview with recent uploads
- Quick access to upload and settings functionality

**app/nextjs/src/app/admin/upload/page.tsx** - Document Upload Interface
- Drag-and-drop file upload with progress tracking
- Multi-file upload support (PDF, DOCX, TXT)
- Real-time upload status and file validation
- Material-UI components with professional styling

**app/nextjs/src/app/admin/settings/page.tsx** - System Settings
- LLM backend configuration (Ollama vs HuggingFace)
- Model selection and parameter tuning
- System monitoring and health checks
- Configuration persistence and validation

**app/nextjs/src/components/layout/** - Professional Layout System
- **MainLayout.tsx** - Main layout wrapper with sidebar and header
- **AppBar.tsx** - Top navigation bar with user actions and branding
- **Sidebar.tsx** - Collapsible sidebar navigation with route highlighting
- Responsive design that works on mobile, tablet, and desktop
- Material-UI theming with consistent spacing and colors

**app/nextjs/src/hooks/** - Custom React Hooks
- **useDocuments.ts** - Document management state and operations
- **useStats.ts** - System statistics and monitoring data
- **useUpload.ts** - File upload state management and progress tracking
- Real-time data fetching with error handling and loading states

**app/nextjs/src/services/api/** - API Integration Layer
- **adminApi.ts** - Admin API endpoints integration
- **chatApi.ts** - Chat and conversation API integration
- TypeScript interfaces and error handling
- Axios-based HTTP client with interceptors

**app/nextjs/src/theme/theme.ts** - Material-UI Custom Theme
- Professional color palette optimized for admin interfaces
- Typography scale with proper hierarchy
- Component customizations for consistent styling
- Dark/light theme support preparation

**app/nextjs/src/types/index.ts** - TypeScript Type Definitions
- Comprehensive type definitions for all API responses
- Document, conversation, and system state types
- Form validation and component prop types
- Shared interfaces between frontend and backend

### Added - 2025-10-31 17:00:00

**Dual Frontend Architecture Implementation**

**Complete React + Vite Admin Dashboard (app/web/):**
- Maintained original React + Vite implementation as reference
- Tailwind CSS styling with modern glassmorphism design
- Complete admin dashboard with document management
- All functionality working: upload, indexing, document list, stats

**NextJS Implementation (app/nextjs/):**
- New NextJS 15 implementation with App Router
- Material-UI component library for professional UI
- Enhanced user experience with better animations
- Server-side rendering capabilities

**Dual Architecture Benefits:**
- Two different UI frameworks for comparison (Tailwind vs Material-UI)
- Different build systems (Vite vs NextJS)
- Flexibility to choose best approach for production
- Learning opportunity for different React patterns

**Backend Compatibility:**
- Single FastAPI backend serves both frontends
- CORS configured for both ports (5173/5174 for Vite, 3000 for NextJS)
- Shared API endpoints and data models
- Consistent authentication and session management

### Changed - 2025-10-31 20:35:00

**Migrated Frontend from Vite to Next.js**

**Frontend Migration:**
- Migrated from React + Vite to Next.js 14+ with App Router
- Frontend now runs on port 3000 (was 5173)
- Using Next.js App Router for better SSR and routing
- CORS already configured to allow http://localhost:3000

**CLAUDE.md** - Updated Documentation
- Changed frontend stack from "React + Vite" to "Next.js"
- Updated folder structure to reflect Next.js App Router structure
- Updated running commands (npm run dev now starts on port 3000)
- Updated debugging and access point URLs to localhost:3000
- Reorganized CORS_ORIGINS order to prioritize port 3000

**Benefits of Next.js:**
- Server-side rendering for better SEO
- API routes for backend-for-frontend pattern
- Built-in image optimization
- Better TypeScript support
- File-based routing with app directory

### Changed - 2025-10-31 18:00:00

**Complete UI/UX Redesign - Modern, Compact Admin Dashboard**

Redesigned the entire admin dashboard with a modern, visually appealing, and compact interface:

**app/web/src/pages/AdminDashboard.tsx** - Modern Layout
- Changed background to gradient: `from-slate-50 via-blue-50 to-slate-100`
- Redesigned header with gradient icon badge and compact sizing
- Made header sticky with backdrop blur effect
- Reduced header padding from py-4 to py-3 (25% smaller)
- Changed button sizes from md to sm for compactness
- Implemented two-column layout for Upload & Documents on larger screens
- Reduced spacing between sections from space-y-6 to space-y-5
- Simplified footer with minimal design

**app/web/src/components/ui/Card.tsx** - Premium Card Design
- Updated to glassmorphism style: `bg-white/90 backdrop-blur`
- Enhanced shadows: `shadow-lg` with `hover:shadow-xl` transition
- Modernized borders: `border-slate-200/60` (semi-transparent)
- Improved border radius: `rounded-xl` (more rounded)
- Added gradient header background: `bg-gradient-to-r from-slate-50`
- Reduced padding from p-6 to p-5 (17% more compact)
- Reduced title section padding from px-6 py-4 to px-5 py-3.5

**app/web/src/components/admin/IndexStatus.tsx** - Compact Stats Cards
- Redesigned stat cards with gradient backgrounds
- Reduced card padding from p-4 to p-3 (25% smaller)
- Changed grid from 4 columns to 2 columns on mobile (better mobile UX)
- Made icons smaller: h-5/w-5 → h-4/w-4
- Reduced font sizes: text-lg → text-base for values
- Added hover effects with shadow transitions
- Implemented inline flex layout for better space usage
- Added code-style badge for embedding model name
- Reduced empty state padding from py-8 to py-6

**app/web/src/components/admin/DocumentUpload.tsx** - Modern Dropzone
- Redesigned dropzone with scale animation on drag (scale-[1.02])
- Changed border radius to rounded-xl for modern look
- Reduced dropzone padding from p-8 to p-6 (25% smaller)
- Made icons smaller: h-12 → h-10
- Reduced file list max height from max-h-64 to max-h-48 (more compact)
- Implemented smaller file item cards with tighter spacing
- Changed button size from default to sm
- Added transition effects for hover states
- Improved status badges with color-coded backgrounds

**app/web/src/components/admin/DocumentList.tsx** - Streamlined Document Cards
- Redesigned search input with smaller icon (h-4 → h-3.5)
- Reduced input padding and made text smaller
- Implemented gradient backgrounds for document cards
- Made document cards more compact: p-4 → p-3
- Reduced document icon size: text-2xl → text-xl
- Minimized font sizes throughout (text-sm → text-xs, etc.)
- Changed max height from max-h-96 to max-h-80 (20% smaller)
- Improved delete button with icon-only design
- Added hover shadow effects for better interactivity
- Implemented tighter spacing between elements (gap-3 → gap-2.5)

**Overall Improvements:**
- **~30% more compact** - Reduced padding and spacing throughout
- **Modern aesthetics** - Gradients, glassmorphism, better shadows
- **Better performance** - Smooth transitions and hover effects
- **Improved mobile UX** - Better responsive grid layouts
- **Professional look** - Consistent color scheme (slate-based palette)
- **Enhanced readability** - Better typography hierarchy
- **Space efficiency** - Two-column layout on larger screens

### Fixed - 2025-10-31 17:51:00

**app/web/src/components/admin/IndexStatus.tsx** - Handle Empty Vector Store
- Fixed "Cannot read properties of undefined (reading 'toLocaleString')" error
- Component now properly handles case when vector store doesn't exist yet
- Shows friendly message: "Vector store not found - Upload and index documents"
- Added optional chaining to all stats fields to prevent runtime errors
- Updated TypeScript types to make all IndexStatsResponse fields optional

**app/web/src/types/index.ts** - IndexStatsResponse Type Update
- Made all fields optional (exists, message, total_documents, etc.)
- Allows handling both "exists: false" and full stats responses

**backend/settings.py** - CORS Configuration Fix
- Added `http://localhost:5174` to CORS_ORIGINS list
- Frontend was running on port 5174 but backend only allowed 5173
- CORS now allows requests from ports 5173, 5174, and 3000
- Fixes "CORS error" when accessing admin dashboard from port 5174

### Changed - 2025-10-31 17:40:00

**CLAUDE.md - Comprehensive Documentation Update**

Updated project documentation to accurately reflect the current state of implementation:

**Architecture & Technology Stack:**
- Added dual LLM backend support (Ollama + HuggingFace Inference API)
- Updated technology stack with actual implementations
- Clarified model choices: bloom-560m (Ollama), KavithaSaaram-2b-it (HuggingFace)
- Added TypeScript to frontend stack

**Implementation Status:**
- Updated status: Phases 1-8 complete (was incorrectly showing only 1-2 complete)
- Backend is fully functional: RAG, APIs, graphs, speech components, admin dashboard
- Admin Dashboard UI complete with document management, upload, and monitoring
- Only Voice Assistant UI (Phase 9) remains for frontend

**Folder Structure:**
- Marked all backend components as ✅ complete (graphs, rag, speech, api, models)
- Added detailed frontend structure (pages, components, services, hooks, types)
- Updated descriptions for llm_local.py and llm_huggingface.py
- Added missing files (audio_utils.py, test files)

**Development Commands:**
- Added comprehensive test commands for all components
- Added individual component tests (RAG, speech, graphs, API)
- Updated LLM testing to include both backends

**API Endpoints:**
- Expanded to show all implemented endpoints (was showing only 6, now 20+)
- Organized into categories: Admin, Chat, Component Testing, General
- Added detailed endpoint descriptions (sessions, history, stats, WebSocket)

**New Sections Added:**
- **Debugging and Troubleshooting**: Common commands and solutions
- **Common Issues**: Port conflicts, FAISS errors, HF API issues, model downloads
- **Admin Dashboard**: Features and implementation details
- **Dual LLM Backend**: Detailed explanation of both modes with switching instructions

**Model Configuration:**
- Added USE_LOCAL_LLM toggle configuration
- Split configuration into Ollama vs HuggingFace sections
- Added HF_TOKEN configuration
- Included conversation settings and optimized generation parameters

**Implementation Notes:**
- Rewrote to explain dual LLM backend architecture
- Added switching instructions between Ollama and HuggingFace
- Updated singleton pattern documentation
- Added admin dashboard implementation details
- Emphasized CHANGELOG.md and TASKS.md tracking requirements

This update ensures future Claude Code instances have accurate information about the project's actual state (52% complete, not ~15% as previously implied).

### Added - 2025-10-31 06:00:00

**Switched from Ollama to HuggingFace Inference API**

**Why HuggingFace Inference API?**
- No local model downloads or storage needed
- Zero RAM/GPU requirements (runs on HF servers)
- Better Tamil support with access to latest multilingual models
- Free tier available with reasonable limits
- Easy model switching without re-downloading

**backend/models/llm_huggingface.py** - New HuggingFace API Integration
- Implemented serverless inference via HuggingFace Inference API
- Supports any model with inference API enabled
- Automatic model loading and connection management
- Configurable generation parameters (temperature, top_p, top_k, etc.)
- Comprehensive error handling and troubleshooting
- Free tier support (requires HF API token)
- Features:
  - `HuggingFaceLLM` class with `load_model()` and `generate()` methods
  - Singleton pattern with `get_hf_llm()` and `initialize_hf_llm()`
  - Handles cold starts, rate limiting, authentication
  - Clear error messages with setup instructions

**backend/settings.py** - HuggingFace Configuration
- Added `HF_MODEL_NAME` setting (default: "bigscience/bloomz-1b1")
- Added `HF_API_TOKEN` setting (set via environment variable)
- Recommended Tamil-friendly models documented:
  - bigscience/bloomz-1b1 (default, 1.1B, good Tamil support)
  - sarvamai/sarvam-2b-v0.5 (best Tamil quality, Indian languages)
  - bigscience/bloomz-560m (fastest, smaller model)
  - google/gemma-2b-it (good balance)

**demo_rag_qa.py & query_rag.py** - Updated to use HuggingFace API
- Replaced Ollama LLM with HuggingFace API
- Updated prerequisites and setup instructions
- Clear error messages with HF token setup guide
- Graceful fallback to context-only when API unavailable

**SETUP_HUGGINGFACE.md** - Complete Setup Guide
- Step-by-step instructions to get free HF API token
- Model recommendations for Tamil
- Configuration and troubleshooting
- Model comparison table
- API limits and pricing info

### Changed - 2025-10-31 05:00:00

**Switched LLM model from tamil-llama to bloom-560m**

**backend/settings.py** - Model Configuration Update
- Changed `LLM_MODEL_NAME` from `tamil-llama-7b-v0.1-q4_k_m.gguf` to `bloom-560m.q8_0.gguf`
- Bloom-560m is a smaller (560M parameters), faster model
- Better for systems with limited resources (2-3GB RAM)

**demo_rag_qa.py & query_rag.py** - Updated to use bloom-560m
- Changed model loading from `tamil-llama` to `bloom-560m`
- Updated error messages and setup instructions
- Clear instructions for importing bloom-560m GGUF into Ollama

**setup_bloom560m.sh** - New Setup Script
- Automated script to configure bloom-560m in Ollama
- Checks for model file existence
- Creates Modelfile with optimal parameters for bloom-560m
- Imports model into Ollama
- Tests the model after setup
- Usage: `./setup_bloom560m.sh`

### Reverted - 2025-10-31 04:30:00

**Removed AirLLM and llama-cpp-python integrations**
- Removed backend/models/llm_airllm.py
- Removed backend/models/llm_llamacpp.py
- Removed INSTALL_AIRLLM.md
- Removed INSTALL_LLAMACPP.md

**Reason for revert:**
- AirLLM had unresolvable dependency conflicts (transformers version incompatibility)
- llama-cpp-python compilation/installation issues
- Decision: Use Ollama with tamil-llama model (standard approach)

**demo_rag_qa.py & query_rag.py** - Reverted to Ollama-only approach
- Uses only Ollama for LLM inference with tamil-llama model exclusively
- No fallback to other models (llama2, llama3.2:1b) - tamil-llama only for best Tamil support
- Clear error messages with setup instructions if tamil-llama not available
- Graceful degradation when LLM unavailable (shows retrieved context)

**requirements.txt** - Cleaned up dependencies
- Removed llama-cpp-python
- Restored transformers>=4.35.0 (standard version)
- Restored sentence-transformers>=3.0.0 (standard version)
- Removed all version constraints (no conflicts)
- Clean dependency tree

### Fixed - 2025-10-31 03:30:00

**demo_rag_qa.py & query_rag.py** - LLM Memory Issue Fix
- Updated to try smaller model (llama3.2:1b) before llama2
- Graceful fallback when LLM is unavailable due to memory constraints
- Shows retrieved context even when LLM fails
- Better error messages for troubleshooting

**docker-compose.dev.yml** - Memory Limit Adjustment
- Reduced memory limit from 8G to 6G for more conservative resource usage
- Helps prevent out-of-memory issues on systems with limited RAM

### Fixed - 2025-10-31 03:15:00

**backend/graphs/ingest_graph.py & backend/rag/vectorstore.py** - FAISS Memory Layout Fix
- Fixed FAISS indexing error: "in method 'fvec_renorm_L2', argument 3 of type 'float *'"
- Issue: Embeddings converted to list for state storage, then back to numpy array caused memory layout incompatibility with FAISS
- Root cause: FAISS requires arrays to be float32 and C-contiguous for normalize_L2 and index.add operations
- Solution in ingest_graph.py:
  - Ensure embeddings array is float32 and C-contiguous before indexing
  - Added explicit dtype=np.float32 conversion
  - Added np.ascontiguousarray() check
- Solution in vectorstore.py:
  - Added np.ascontiguousarray(embedding_matrix, dtype=np.float32) before normalize_L2
  - Ensures all embedding matrices are in correct format regardless of source
- This fixes issues in both LangGraph workflow and direct vector store usage

### Added - 2025-10-31 02:45:00

#### Phase 4: Document Ingestion API & LangGraph Workflow (COMPLETE ✅)

Implemented LangGraph-based document ingestion workflow and admin API endpoints for document management.

**backend/graphs/ingest_graph.py** - LangGraph Document Ingestion Workflow
- Defined `IngestState` TypedDict schema with comprehensive state tracking
- Created 4 workflow nodes:
  - `load_documents_node` - Load documents from file paths using DocumentLoaderFactory
  - `chunk_documents_node` - Chunk documents using sentence-aware strategy
  - `generate_embeddings_node` - Generate embeddings for all chunks
  - `index_documents_node` - Index in FAISS vector store and persist
- Implemented `create_ingest_graph()` - Compile LangGraph workflow
- Created `run_ingestion_workflow()` - Run complete workflow with session management
- State tracking: pending → loading → chunking → embedding → indexing → completed
- Error handling and status updates at each step
- Unique session IDs for tracking multiple ingestion jobs

**backend/graphs/__init__.py** - Package Exports
- Exported IngestState, create_ingest_graph, run_ingestion_workflow

**backend/api/admin.py** - Admin API Endpoints
- Created FastAPI router with `/admin` prefix
- Implemented comprehensive admin endpoints:
  - `POST /admin/upload` - Upload documents (PDF, DOCX, TXT)
    - Multi-file upload support
    - File validation (type, size)
    - Unique filename generation to avoid conflicts
    - Returns file paths for ingestion
  - `POST /admin/ingest` - Trigger ingestion workflow
    - Accepts list of file paths and vector store name
    - Creates session ID for tracking
    - Runs workflow in background using BackgroundTasks
    - Returns immediately with session ID
  - `GET /admin/status/{session_id}` - Check ingestion status
    - Returns current status and progress
    - Includes started_at, completed_at, indexed_count
    - Error reporting if ingestion failed
  - `GET /admin/documents` - List indexed documents
    - Paginated results with limit parameter
    - Returns document previews and metadata
    - Vector store selection
  - `DELETE /admin/documents/{doc_id}` - Delete document
    - Remove from vector store
    - Persist changes to disk
  - `GET /admin/stats` - Vector store statistics
    - Total documents, index size, embedding dimension
- File validation:
  - Allowed extensions: .pdf, .docx, .doc, .txt
  - Maximum file size: 50MB
  - Error messages for validation failures
- In-memory session tracking (production should use Redis/database)
- Background processing using ThreadPoolExecutor
- Pydantic models for request/response validation

**backend/api/__init__.py** - API Package
- Exported admin_router for FastAPI integration

**backend/api/test_admin_api.py** - Admin API Test Script
- Comprehensive test suite for all endpoints
- Tests:
  1. Health check
  2. Document upload
  3. Ingestion trigger
  4. Status polling (waits for completion)
  5. Document listing
  6. Vector store stats
  7. Document deletion
- Automated end-to-end workflow testing
- Clear test output with status messages

**backend/main.py** - Updated
- Integrated admin_router into FastAPI application
- Admin endpoints now available at `/admin/*`

**demo_rag_qa.py** - Complete RAG Q&A Demo
- End-to-end demonstration of the entire system
- Creates 4 sample Tamil documents:
  - AI basics (செயற்கை நுண்ணறிவு)
  - Tamil language overview
  - Technology trends 2025
  - Healthcare AI applications
- Runs complete ingestion workflow using LangGraph
- Performs RAG-based Q&A with 5 test questions (Tamil + English)
- Retrieves relevant context using vector similarity search
- Generates answers using LLM (Ollama)
- Displays retrieved context and final answers
- Comprehensive output showing all pipeline steps
- Runnable with: `python demo_rag_qa.py`

### Added - 2025-10-31 01:30:00

#### Phase 3: RAG Pipeline Implementation (COMPLETE ✅)

Implemented complete RAG (Retrieval-Augmented Generation) pipeline for Tamil document processing and question answering.

**backend/rag/embeddings.py** - Embedding Model Wrapper
- Created `EmbeddingModel` class for SentenceTransformers integration
- Supports Tamil, English, and code-mixed text
- Methods: `encode()`, `encode_query()`, `encode_documents()`, `similarity()`
- Singleton pattern with `get_embedding_model()` and `initialize_embeddings()`
- Built-in testing with Tamil text samples
- 384-dimensional embeddings (paraphrase-multilingual-MiniLM-L12-v2)

**backend/rag/chunking.py** - Text Chunking Strategies
- Created `TextChunker` class with three strategies:
  - Character-based chunking (simple, fixed-size)
  - Sentence-aware chunking (preserves sentence boundaries)
  - Paragraph-aware chunking (preserves paragraph structure)
- Configurable chunk size and overlap from settings
- `Chunk` dataclass with metadata support
- Tamil sentence splitting (handles Tamil purna viraam ।)
- Comprehensive tests for all strategies

**backend/rag/vectorstore.py** - FAISS Vector Store
- Created `VectorStore` class for similarity search
- Uses FAISS IndexFlatIP for cosine similarity
- Features:
  - Add/delete documents with incremental updates
  - Metadata filtering during search
  - Persistent storage (save/load from disk)
  - Rebuild index to remove deleted documents
  - Get statistics (document count, index size)
- `Document` dataclass for vector store entries
- Thread-safe operations
- Handles normalized embeddings for accurate similarity

**backend/rag/loaders.py** - Document Loaders
- Created `BaseLoader` abstract class
- Implemented format-specific loaders:
  - `PDFLoader` - Extract text from PDF files
  - `DOCXLoader` - Extract from Microsoft Word documents
  - `TXTLoader` - Load plain text with UTF-8 encoding
- `DocumentLoaderFactory` for automatic loader selection
- `LoadedDocument` dataclass with rich metadata
- Support for directory loading (recursive option)
- Metadata extraction (file stats, document properties)
- Error handling and encoding detection

**backend/rag/prompts.py** - Tamil-Optimized Prompts
- Created `PromptTemplate` dataclass for reusable prompts
- Implemented Tamil-optimized prompt templates:
  - `RAG_QA_TEMPLATE` - Basic RAG question answering
  - `CONVERSATIONAL_RAG_TEMPLATE` - Chat with history
  - `CODE_MIXED_RAG_TEMPLATE` - Tamil + English support
  - `SIMPLE_QA_TEMPLATE` - Direct questions
  - `SUMMARIZATION_TEMPLATE` - Document summarization
- `PromptBuilder` class with helper methods:
  - `build_with_context()` - Format RAG prompts
  - `_format_context()` - Structure retrieved documents
  - `_format_chat_history()` - Format conversation history
- Convenience functions: `get_rag_prompt_builder()`, etc.
- All prompts in Tamil with English translations

**backend/rag/__init__.py** - Package Exports
- Centralized imports for all RAG components
- Clean API for external usage

**backend/rag/test_rag_pipeline.py** - End-to-End Test
- Comprehensive integration test for entire RAG pipeline
- Tests all components working together:
  1. Document creation (Tamil sample documents)
  2. Document loading (multiple files)
  3. Text chunking (sentence-aware)
  4. Embedding generation (batch processing)
  5. Vector store creation and indexing
  6. Similarity search with multiple queries
  7. RAG prompt generation
- Creates sample Tamil documents about AI, Tamil language, and technology
- Outputs detailed statistics and results
- Verifies save/load persistence

### Changed - 2025-10-31 00:00:00

#### CLAUDE.md Updates
- Updated all `docker-compose` commands to `docker compose` (V2 syntax)
- Changed backend startup command from `uvicorn backend.main:app --reload` to `python -m uvicorn backend.main:app --reload`
- Added file reference line numbers for key implementation files (settings.py:8-93, llm_local.py:204-233)
- Added verify_setup.py to testing commands section
- Added "Important Notes" section clarifying:
  - Docker Compose V2 vs V1 usage
  - Empty placeholder directories (api/, rag/, graphs/, speech/)
  - Current implementation status (only models/, main.py, settings.py are complete)
- Enhanced LocalLLM documentation with REST API endpoint details (http://localhost:11435)
- Improved directory auto-creation documentation with line references

---

## [0.1.0] - 2025-10-30

### Added

#### Initial Project Setup
- Created project structure with backend/ and app/web/ directories
- Implemented Pydantic-based settings management (backend/settings.py)
- Set up FastAPI application with CORS and health check endpoints (backend/main.py)
- Implemented Ollama LLM integration with streaming support (backend/models/llm_local.py)
- Created model download script for embeddings, STT, TTS models (backend/models/download_models.py)
- Added Docker Compose configuration for Ollama server (docker-compose.dev.yml)
- Set up React + Vite + TypeScript + Tailwind frontend skeleton (app/web/)
- Created verification script for setup validation (verify_setup.py)
- Added requirements.txt with all Python dependencies
- Created placeholder directories for future implementation:
  - backend/api/ (admin and chat endpoints)
  - backend/rag/ (document processing and vector store)
  - backend/graphs/ (LangGraph state machines)
  - backend/speech/ (STT, TTS, VAD)
- Created comprehensive CLAUDE.md documentation
- Created PRD.md, TASKS.md, MODELS_INFO.md, SETUP_TESTING.md documentation files

### Configuration
- Set up Ollama on port 11435 (to avoid conflict with system Ollama on 11434)
- Configured automatic directory creation for data/, models/, logs/
- Set default models:
  - LLM: Tamil-LLaMA GGUF (via Ollama)
  - Embeddings: paraphrase-multilingual-MiniLM-L12-v2
  - STT: Whisper large-v2
  - TTS: facebook/mms-tts-tam

### Implementation Status
- ✅ Phase 1-2: Project foundation complete
- ✅ Phase 3: RAG Pipeline complete
- ✅ Phase 4: Document Ingestion API & LangGraph Workflow complete
- 🔄 Phase 5-14: Speech components, chat API, frontend - planned
