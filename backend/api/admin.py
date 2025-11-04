"""
Admin API Endpoints for Tamil AI Voice Assistant

Provides endpoints for:
- Document upload
- Document ingestion (triggering LangGraph workflow)
- Ingestion status monitoring
- Document management (list, delete)
"""
import sys
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.settings import settings
from backend.graphs import run_ingestion_workflow
from backend.rag import VectorStore, get_embedding_model


# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# In-memory storage for ingestion sessions
# In production, use Redis or database
ingestion_sessions: Dict[str, Dict] = {}

# Thread pool for background ingestion
executor = ThreadPoolExecutor(max_workers=2)


# Request/Response Models
class UploadResponse(BaseModel):
    """Response for file upload"""
    success: bool
    message: str
    files: List[Dict[str, str]]
    upload_dir: str


class IngestRequest(BaseModel):
    """Request to trigger document ingestion"""
    file_paths: List[str]
    vector_store_name: str = "default"


class IngestResponse(BaseModel):
    """Response for ingestion request"""
    success: bool
    session_id: str
    message: str
    status: str


class StatusResponse(BaseModel):
    """Response for status check"""
    session_id: str
    status: str
    progress: Dict
    error: Optional[str] = None


class DocumentInfo(BaseModel):
    """Document information"""
    id: str
    filename: str
    file_size: int
    chunk_count: int
    upload_date: str
    status: str  # 'indexed', 'processing', 'failed'
    text_preview: str
    metadata: Dict
    indexed_at: Optional[str] = None


class DocumentsResponse(BaseModel):
    """Response for documents list"""
    total: int
    documents: List[DocumentInfo]
    vector_store_name: str


# Utility Functions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_file(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file

    Args:
        filename: Name of the file
        file_size: Size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    # Check size
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"

    return True, None


async def save_uploaded_file(file: UploadFile, upload_dir: Path) -> Path:
    """
    Save uploaded file to disk

    Args:
        file: Uploaded file
        upload_dir: Directory to save to

    Returns:
        Path to saved file
    """
    # Create unique filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{timestamp}_{unique_id}_{file.filename}"

    file_path = upload_dir / filename

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def run_ingestion_in_background(session_id: str, file_paths: List[str], vector_store_name: str):
    """
    Run ingestion workflow in background thread

    Args:
        session_id: Session identifier
        file_paths: Files to ingest
        vector_store_name: Vector store name
    """
    try:
        # Update session status
        ingestion_sessions[session_id]["status"] = "running"

        # Run workflow
        result = run_ingestion_workflow(file_paths, vector_store_name)

        # Update session with result
        ingestion_sessions[session_id].update({
            "status": result["status"],
            "indexed_count": result.get("indexed_count", 0),
            "completed_at": result.get("completed_at"),
            "error": result.get("error"),
            "final_state": result,
        })

    except Exception as e:
        # Update session with error
        ingestion_sessions[session_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
        })


# API Endpoints

@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
) -> UploadResponse:
    """
    Upload documents for ingestion

    Args:
        files: List of files to upload

    Returns:
        Upload confirmation with file paths
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Ensure upload directory exists
    settings.DOCS_DIR.mkdir(parents=True, exist_ok=True)

    uploaded_files = []
    errors = []

    for file in files:
        try:
            # Read file to get size
            content = await file.read()
            file_size = len(content)
            await file.seek(0)  # Reset file pointer

            # Validate file
            is_valid, error_msg = validate_file(file.filename, file_size)
            if not is_valid:
                errors.append({"filename": file.filename, "error": error_msg})
                continue

            # Save file
            file_path = await save_uploaded_file(file, settings.DOCS_DIR)

            uploaded_files.append({
                "filename": file.filename,
                "path": str(file_path),
                "size": str(file_size),
            })

        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    # Check results
    if not uploaded_files:
        raise HTTPException(
            status_code=400,
            detail=f"No files uploaded successfully. Errors: {errors}"
        )

    return UploadResponse(
        success=True,
        message=f"Uploaded {len(uploaded_files)} files" + (
            f" ({len(errors)} failed)" if errors else ""
        ),
        files=uploaded_files,
        upload_dir=str(settings.DOCS_DIR),
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
) -> IngestResponse:
    """
    Trigger document ingestion workflow

    Args:
        request: Ingestion request with file paths
        background_tasks: FastAPI background tasks

    Returns:
        Ingestion session information
    """
    if not request.file_paths:
        raise HTTPException(status_code=400, detail="No file paths provided")

    # Validate file paths exist
    for file_path in request.file_paths:
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    # Create session
    session_id = str(uuid.uuid4())

    ingestion_sessions[session_id] = {
        "session_id": session_id,
        "file_paths": request.file_paths,
        "vector_store_name": request.vector_store_name,
        "status": "queued",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "indexed_count": 0,
        "error": None,
    }

    # Run ingestion in background
    background_tasks.add_task(
        run_ingestion_in_background,
        session_id,
        request.file_paths,
        request.vector_store_name
    )

    return IngestResponse(
        success=True,
        session_id=session_id,
        message=f"Ingestion started for {len(request.file_paths)} files",
        status="queued",
    )


@router.get("/status/{session_id}", response_model=StatusResponse)
async def get_ingestion_status(session_id: str) -> StatusResponse:
    """
    Get status of an ingestion session

    Args:
        session_id: Session identifier

    Returns:
        Current status of the session
    """
    if session_id not in ingestion_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = ingestion_sessions[session_id]

    return StatusResponse(
        session_id=session_id,
        status=session["status"],
        progress={
            "started_at": session.get("started_at"),
            "completed_at": session.get("completed_at"),
            "indexed_count": session.get("indexed_count", 0),
            "file_count": len(session.get("file_paths", [])),
        },
        error=session.get("error"),
    )


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents(
    vector_store_name: str = "default",
    limit: int = 100,
) -> DocumentsResponse:
    """
    List indexed documents in vector store

    Args:
        vector_store_name: Vector store to query
        limit: Maximum number of documents to return

    Returns:
        List of indexed documents
    """
    try:
        # Load vector store
        embedding_model = get_embedding_model()
        if not embedding_model.is_loaded():
            embedding_model.load()

        vector_store = VectorStore(
            embedding_dimension=embedding_model.get_dimension(),
            store_name=vector_store_name
        )

        if not vector_store.load():
            return DocumentsResponse(
                total=0,
                documents=[],
                vector_store_name=vector_store_name,
            )

        # Helper function to extract session_id consistently
        def get_session_id(doc) -> str:
            """Extract session_id from document, trying metadata first, then ID parsing"""
            if doc.metadata and "session_id" in doc.metadata:
                return doc.metadata["session_id"]
            # Fallback: parse from document ID (format: session_id_chunk_N)
            if "_chunk_" in doc.id:
                return doc.id.rsplit("_chunk_", 1)[0]
            # Last resort: use the full ID
            return doc.id

        # Group ALL documents by session_id to count chunks
        doc_groups = {}
        for doc in vector_store.documents.values():
            session_id = get_session_id(doc)
            if session_id not in doc_groups:
                doc_groups[session_id] = []
            doc_groups[session_id].append(doc)

        # Format response - iterate through unique session_ids, not individual chunks
        documents = []
        
        # Process each unique session (document), limit to requested number
        for session_id, chunks in list(doc_groups.items())[:limit]:
            # Use first chunk as representative for metadata
            first_chunk = chunks[0]
            meta = first_chunk.metadata or {}

            # Get filename (from metadata or default)
            filename = meta.get("filename", meta.get("file_path", "unknown.txt").split("/")[-1])

            # Get file size (from metadata or estimate from text)
            file_size = meta.get("file_size", len(first_chunk.text))

            # Count chunks for this document
            chunk_count = len(chunks)

            # Get upload/indexed date
            upload_date = meta.get("loaded_at", meta.get("indexed_at", datetime.now().isoformat()))
            indexed_at = meta.get("indexed_at", upload_date)

            # Create text preview from first chunk
            text_preview = first_chunk.text[:200] + "..." if len(first_chunk.text) > 200 else first_chunk.text

            documents.append(DocumentInfo(
                id=session_id,  # Use session_id as document ID (groups chunks together)
                filename=filename,
                file_size=int(file_size) if isinstance(file_size, (int, float, str)) else 0,
                chunk_count=chunk_count,
                upload_date=upload_date,
                status="indexed",  # All documents in vector store are indexed
                text_preview=text_preview,
                metadata=meta,
                indexed_at=indexed_at,
            ))

        return DocumentsResponse(
            total=len(documents),  # Total unique documents (not chunks)
            documents=documents,
            vector_store_name=vector_store_name,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {e}")


@router.get("/documents/{doc_id}", response_model=DocumentInfo)
async def get_document(
    doc_id: str,
    vector_store_name: str = "default",
) -> DocumentInfo:
    """
    Get a specific document by ID

    Args:
        doc_id: Document/session ID
        vector_store_name: Vector store name

    Returns:
        Document information with all chunks
    """
    try:
        # Load vector store
        embedding_model = get_embedding_model()
        if not embedding_model.is_loaded():
            embedding_model.load()

        vector_store = VectorStore(
            embedding_dimension=embedding_model.get_dimension(),
            store_name=vector_store_name
        )

        if not vector_store.load():
            raise HTTPException(status_code=404, detail="Vector store not found")

        # Find all chunks for this document
        chunks = [doc for doc in vector_store.documents.values()
                  if doc.metadata and doc.metadata.get("session_id") == doc_id]

        if not chunks:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get first chunk for metadata
        first_chunk = chunks[0]
        meta = first_chunk.metadata or {}

        # Combine all chunk text for preview
        full_text = "\n".join([chunk.text for chunk in chunks])
        text_preview = full_text[:500] + "..." if len(full_text) > 500 else full_text

        return DocumentInfo(
            id=doc_id,
            filename=meta.get("filename", "unknown.txt"),
            file_size=meta.get("file_size", 0),
            chunk_count=len(chunks),
            upload_date=meta.get("loaded_at", datetime.now().isoformat()),
            status="indexed",
            text_preview=text_preview,
            metadata=meta,
            indexed_at=meta.get("indexed_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document: {e}")


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    vector_store_name: str = "default",
) -> JSONResponse:
    """
    Delete a document (all chunks) from vector store

    Args:
        doc_id: Document/session ID to delete (deletes all chunks)
        vector_store_name: Vector store name

    Returns:
        Deletion confirmation
    """
    try:
        # Load vector store
        embedding_model = get_embedding_model()
        if not embedding_model.is_loaded():
            embedding_model.load()

        vector_store = VectorStore(
            embedding_dimension=embedding_model.get_dimension(),
            store_name=vector_store_name
        )

        if not vector_store.load():
            raise HTTPException(status_code=404, detail="Vector store not found")

        # Find all chunks for this document
        chunks_to_delete = [doc.id for doc in vector_store.documents.values()
                            if doc.metadata and doc.metadata.get("session_id") == doc_id]

        if not chunks_to_delete:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete all chunks
        deleted_count = 0
        for chunk_id in chunks_to_delete:
            if vector_store.delete_document(chunk_id):
                deleted_count += 1

        # Rebuild index to clean up deleted entries
        vector_store.rebuild_index()

        # Save updated store
        vector_store.save()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Document {doc_id} deleted successfully ({deleted_count} chunks removed)",
                "deleted_chunks": deleted_count,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {e}")


@router.get("/stats")
async def get_vector_store_stats(vector_store_name: str = "default") -> JSONResponse:
    """
    Get statistics about the vector store

    Args:
        vector_store_name: Vector store name

    Returns:
        Vector store statistics with correct document count (grouped by session_id)
    """
    try:
        # Load vector store
        embedding_model = get_embedding_model()
        if not embedding_model.is_loaded():
            embedding_model.load()

        vector_store = VectorStore(
            embedding_dimension=embedding_model.get_dimension(),
            store_name=vector_store_name
        )

        if not vector_store.load():
            return JSONResponse(
                status_code=200,
                content={
                    "exists": False,
                    "message": "Vector store not found",
                }
            )

        # Helper function to extract session_id consistently (same as list_documents)
        def get_session_id(doc) -> str:
            """Extract session_id from document, trying metadata first, then ID parsing"""
            if doc.metadata and "session_id" in doc.metadata:
                return doc.metadata["session_id"]
            # Fallback: parse from document ID (format: session_id_chunk_N)
            if "_chunk_" in doc.id:
                return doc.id.rsplit("_chunk_", 1)[0]
            # Last resort: use the full ID
            return doc.id

        # Group documents by session_id to count unique documents
        doc_groups = {}
        total_chunks = len(vector_store.documents)
        
        for doc in vector_store.documents.values():
            session_id = get_session_id(doc)
            if session_id not in doc_groups:
                doc_groups[session_id] = []
            doc_groups[session_id].append(doc)

        # Calculate statistics
        total_documents = len(doc_groups)  # Count unique session_ids (actual documents)
        avg_chunks_per_doc = total_chunks / total_documents if total_documents > 0 else 0

        return JSONResponse(
            status_code=200,
            content={
                "exists": True,
                "total_documents": total_documents,  # Unique documents (grouped by session_id)
                "total_chunks": total_chunks,        # Total chunks in vector store
                "index_size": vector_store.index.ntotal if vector_store.index else 0,  # FAISS index size
                "embedding_dimension": vector_store.embedding_dimension,
                "store_name": vector_store.store_name,
                "avg_chunks_per_document": round(avg_chunks_per_doc, 2),
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {e}")


@router.post("/clear")
async def clear_all_documents(vector_store_name: str = "default") -> JSONResponse:
    """
    Clear all documents from vector store and delete uploaded files

    Args:
        vector_store_name: Vector store name

    Returns:
        Confirmation of cleared data
    """
    try:
        # Load vector store
        embedding_model = get_embedding_model()
        if not embedding_model.is_loaded():
            embedding_model.load()

        vector_store = VectorStore(
            embedding_dimension=embedding_model.get_dimension(),
            store_name=vector_store_name
        )

        # Track counts before clearing
        docs_count = 0
        if vector_store.load():
            docs_count = len(vector_store.documents)

        # Clear all documents from vector store
        vector_store.documents.clear()
        vector_store.id_to_index.clear()
        vector_store.index_to_id.clear()
        vector_store.next_index = 0
        vector_store._create_index()  # Reset FAISS index

        # Save empty store
        vector_store.save()

        # Delete all uploaded files
        files_deleted = 0
        if settings.DOCS_DIR.exists():
            for file_path in settings.DOCS_DIR.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    files_deleted += 1

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "All documents cleared successfully",
                "documents_removed": docs_count,
                "files_deleted": files_deleted,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {e}")


@router.post("/reindex")
async def reindex_all_documents(
    vector_store_name: str = "default",
    background_tasks: BackgroundTasks = None,
) -> JSONResponse:
    """
    Re-index all documents in the vector store
    Rebuilds FAISS index from existing documents

    Args:
        vector_store_name: Vector store name

    Returns:
        Confirmation of reindex operation
    """
    try:
        # Load vector store
        embedding_model = get_embedding_model()
        if not embedding_model.is_loaded():
            embedding_model.load()

        vector_store = VectorStore(
            embedding_dimension=embedding_model.get_dimension(),
            store_name=vector_store_name
        )

        if not vector_store.load():
            raise HTTPException(status_code=404, detail="Vector store not found")

        # Rebuild index
        docs_count = len(vector_store.documents)
        vector_store.rebuild_index()

        # Save rebuilt store
        vector_store.save()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Successfully re-indexed {docs_count} documents",
                "documents_reindexed": docs_count,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing documents: {e}")


@router.delete("/index")
async def delete_index(vector_store_name: str = "default") -> JSONResponse:
    """
    Delete the entire vector store index (keeps uploaded files)

    Args:
        vector_store_name: Vector store name

    Returns:
        Confirmation of index deletion
    """
    try:
        # Delete index files
        index_path = settings.FAISS_DIR / f"{vector_store_name}.index"
        metadata_path = settings.FAISS_DIR / f"{vector_store_name}.metadata"

        deleted_files = []
        if index_path.exists():
            index_path.unlink()
            deleted_files.append(str(index_path))

        if metadata_path.exists():
            metadata_path.unlink()
            deleted_files.append(str(metadata_path))

        if not deleted_files:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "Index not found",
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Index deleted successfully (uploaded files preserved)",
                "deleted_files": deleted_files,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting index: {e}")


@router.post("/documents/{doc_id}/reindex")
async def reindex_single_document(
    doc_id: str,
    vector_store_name: str = "default",
    background_tasks: BackgroundTasks = None,
) -> JSONResponse:
    """
    Re-index a specific document
    Re-computes embeddings and updates index

    Args:
        doc_id: Document/session ID to re-index
        vector_store_name: Vector store name

    Returns:
        Confirmation of reindex operation
    """
    try:
        # Load vector store
        embedding_model = get_embedding_model()
        if not embedding_model.is_loaded():
            embedding_model.load()

        vector_store = VectorStore(
            embedding_dimension=embedding_model.get_dimension(),
            store_name=vector_store_name
        )

        if not vector_store.load():
            raise HTTPException(status_code=404, detail="Vector store not found")

        # Find all chunks for this document
        chunks = [doc for doc in vector_store.documents.values()
                  if doc.metadata and doc.metadata.get("session_id") == doc_id]

        if not chunks:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get file path from metadata
        file_path = chunks[0].metadata.get("file_path")
        if not file_path or not Path(file_path).exists():
            raise HTTPException(
                status_code=404,
                detail="Original file not found, cannot re-index"
            )

        logger.info(f"🗑️  Deleting {len(chunks)} chunks for document {doc_id}")

        # Delete existing chunks
        deleted_count = 0
        for chunk in chunks:
            if vector_store.delete_document(chunk.id):
                deleted_count += 1

        logger.info(f"✅ Deleted {deleted_count} chunks from metadata")

        # CRITICAL: Rebuild the FAISS index to physically remove deleted vectors
        logger.info(f"🔄 Rebuilding FAISS index to remove deleted vectors...")
        vector_store.rebuild_index(embedding_model)

        # Save the vector store after deletion and rebuild
        if not vector_store.save():
            raise HTTPException(
                status_code=500,
                detail="Failed to save vector store after deletion"
            )

        logger.info(f"💾 Saved vector store after deletion")

        # Re-ingest the file with the SAME session_id to maintain consistency
        logger.info(f"📂 Re-ingesting file with original session_id: {doc_id}")
        result = run_ingestion_workflow([file_path], vector_store_name, session_id=doc_id)

        if result["status"] != "completed":
            raise HTTPException(
                status_code=500,
                detail=f"Re-indexing failed: {result.get('error', 'Unknown error')}"
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Document {doc_id} re-indexed successfully",
                "chunks_deleted": deleted_count,
                "chunks_reindexed": result.get("indexed_count", 0),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error re-indexing document: {e}")


@router.post("/reset-tts")
async def reset_tts():
    """
    Reset the TTS engine to pick up new configuration

    Useful when TTS settings are changed in .env file
    without restarting the server.
    Also updates TTS in all active websocket sessions.
    """
    try:
        from backend.speech.tts import reset_tts_engine, get_tts_engine
        from backend.settings import settings
        from backend.api.websocket import manager

        # Reset the cached instance
        reset_tts_engine()

        # Get fresh instance to verify new configuration
        tts = get_tts_engine()

        # Update all active websocket sessions
        updated_sessions = manager.update_all_tts_instances()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "TTS engine reset successfully",
                "current_voice": settings.TTS_MODEL_NAME,
                "speaking_rate": settings.TTS_SPEAKING_RATE,
                "voice_type": tts.voice_type if hasattr(tts, 'voice_type') else "gTTS",
                "engine": type(tts).__name__,
                "updated_websocket_sessions": updated_sessions
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting TTS: {e}")
