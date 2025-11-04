"""
Document Ingestion LangGraph Workflow

This module implements a LangGraph state machine for processing documents:
1. Load documents from uploaded files
2. Chunk text into appropriate segments
3. Generate embeddings for each chunk
4. Store in FAISS vector store
5. Persist to disk

State Flow: Upload → Load → Chunk → Embed → Index → Complete
"""
import sys
from pathlib import Path
from typing import List, Dict, TypedDict, Optional, Annotated
from datetime import datetime
import uuid

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.settings import settings
from backend.rag import (
    DocumentLoaderFactory,
    TextChunker,
    get_embedding_model,
    VectorStore,
    Document,
)

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    raise ImportError(
        "langgraph not installed. "
        "Run: pip install langgraph>=0.2.0"
    )


# State Schema
class IngestState(TypedDict):
    """
    State for document ingestion workflow

    Attributes:
        file_paths: List of file paths to ingest
        loaded_documents: Loaded document objects with metadata
        chunks: Text chunks with metadata
        embeddings: Generated embeddings for chunks
        indexed_count: Number of chunks indexed
        status: Current status of ingestion
        error: Error message if any
        session_id: Unique session identifier
        vector_store_name: Name of vector store to use
        started_at: Timestamp when ingestion started
        completed_at: Timestamp when ingestion completed
    """
    file_paths: List[str]
    loaded_documents: Optional[List[Dict]]
    chunks: Optional[List[Dict]]
    embeddings: Optional[List]
    indexed_count: int
    status: str  # "pending", "loading", "chunking", "embedding", "indexing", "completed", "failed"
    error: Optional[str]
    session_id: str
    vector_store_name: str
    started_at: Optional[str]
    completed_at: Optional[str]


# Graph Nodes
def load_documents_node(state: IngestState) -> IngestState:
    """
    Load documents from file paths

    Args:
        state: Current workflow state

    Returns:
        Updated state with loaded documents
    """
    print(f"\n📂 Loading {len(state['file_paths'])} documents...")

    try:
        loaded_docs = []

        for file_path in state['file_paths']:
            # Load document
            doc = DocumentLoaderFactory.load_document(Path(file_path))

            # Convert to dict for state storage
            loaded_docs.append({
                "content": doc.content,
                "metadata": doc.metadata,
                "source": doc.source,
                "doc_type": doc.doc_type,
            })

            print(f"  ✅ Loaded: {doc.metadata.get('filename', 'unknown')}")

        state["loaded_documents"] = loaded_docs
        state["status"] = "loading_complete"

        print(f"✅ Successfully loaded {len(loaded_docs)} documents")

        return state

    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        state["status"] = "failed"
        state["error"] = str(e)
        return state


def chunk_documents_node(state: IngestState) -> IngestState:
    """
    Chunk documents into smaller segments

    Args:
        state: Current workflow state

    Returns:
        Updated state with text chunks
    """
    print(f"\n✂️  Chunking documents...")

    try:
        chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            strategy="sentence"  # Use sentence-aware chunking
        )

        all_chunks = []

        for doc in state["loaded_documents"]:
            # Create chunks
            chunks = chunker.chunk_text(
                doc["content"],
                metadata=doc["metadata"]
            )

            # Convert to dict for state storage
            for chunk in chunks:
                all_chunks.append({
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                    "chunk_id": chunk.chunk_id,
                    "source": doc["source"],
                })

            filename = doc["metadata"].get("filename", "unknown")
            print(f"  ✅ Chunked {filename}: {len(chunks)} chunks")

        state["chunks"] = all_chunks
        state["status"] = "chunking_complete"

        print(f"✅ Total chunks created: {len(all_chunks)}")

        return state

    except Exception as e:
        print(f"❌ Error chunking documents: {e}")
        state["status"] = "failed"
        state["error"] = str(e)
        return state


def generate_embeddings_node(state: IngestState) -> IngestState:
    """
    Generate embeddings for text chunks

    Args:
        state: Current workflow state

    Returns:
        Updated state with embeddings
    """
    print(f"\n🧮 Generating embeddings for {len(state['chunks'])} chunks...")

    try:
        # Get embedding model
        embedding_model = get_embedding_model()

        # Load model if not already loaded
        if not embedding_model.is_loaded():
            if not embedding_model.load():
                raise RuntimeError("Failed to load embedding model")

        # Extract chunk texts
        chunk_texts = [chunk["text"] for chunk in state["chunks"]]

        # Generate embeddings
        embeddings = embedding_model.encode_documents(
            chunk_texts,
            show_progress=True
        )

        # Store embeddings (convert to list for JSON serialization)
        state["embeddings"] = embeddings.tolist()
        state["status"] = "embedding_complete"

        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"   Dimension: {embeddings.shape[1]}")

        return state

    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        state["status"] = "failed"
        state["error"] = str(e)
        return state


def index_documents_node(state: IngestState) -> IngestState:
    """
    Index documents in FAISS vector store

    Args:
        state: Current workflow state

    Returns:
        Updated state with indexing status
    """
    print(f"\n🗄️  Indexing {len(state['chunks'])} chunks in vector store...")

    try:
        import numpy as np

        # Get or create vector store
        embedding_model = get_embedding_model()
        vector_store = VectorStore(
            embedding_dimension=embedding_model.get_dimension(),
            store_name=state["vector_store_name"]
        )

        # Try to load existing store
        try:
            vector_store.load()
            print(f"  ℹ️  Loaded existing vector store with {vector_store.index.ntotal} documents")
        except Exception:
            print(f"  ℹ️  Creating new vector store")

        # Prepare documents for indexing
        documents = []
        # Convert embeddings to proper numpy array format for FAISS
        # Must be float32 and C-contiguous
        embeddings_array = np.array(state["embeddings"], dtype=np.float32)
        if not embeddings_array.flags['C_CONTIGUOUS']:
            embeddings_array = np.ascontiguousarray(embeddings_array, dtype=np.float32)

        for i, (chunk, embedding) in enumerate(zip(state["chunks"], embeddings_array)):
            doc_id = f"{state['session_id']}_chunk_{i}"

            doc = Document(
                id=doc_id,
                text=chunk["text"],
                embedding=embedding,
                metadata={
                    **chunk["metadata"],
                    "source": chunk["source"],
                    "session_id": state["session_id"],
                    "indexed_at": datetime.now().isoformat(),
                }
            )
            documents.append(doc)

        # Add to vector store
        added_ids = vector_store.add_documents(documents, embeddings_array)

        # Save vector store
        if vector_store.save():
            print(f"✅ Indexed and saved {len(added_ids)} documents")
        else:
            raise RuntimeError("Failed to save vector store")

        state["indexed_count"] = len(added_ids)
        state["status"] = "completed"
        state["completed_at"] = datetime.now().isoformat()

        # Get final stats
        stats = vector_store.get_stats()
        print(f"\nVector Store Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        return state

    except Exception as e:
        print(f"❌ Error indexing documents: {e}")
        state["status"] = "failed"
        state["error"] = str(e)
        return state


# Build the Graph
def create_ingest_graph() -> StateGraph:
    """
    Create the document ingestion workflow graph

    Returns:
        Compiled StateGraph for document ingestion
    """
    # Create graph
    workflow = StateGraph(IngestState)

    # Add nodes
    workflow.add_node("load_documents", load_documents_node)
    workflow.add_node("chunk_documents", chunk_documents_node)
    workflow.add_node("generate_embeddings", generate_embeddings_node)
    workflow.add_node("index_documents", index_documents_node)

    # Define edges (workflow sequence)
    workflow.set_entry_point("load_documents")
    workflow.add_edge("load_documents", "chunk_documents")
    workflow.add_edge("chunk_documents", "generate_embeddings")
    workflow.add_edge("generate_embeddings", "index_documents")
    workflow.add_edge("index_documents", END)

    # Compile graph
    return workflow.compile()


# Convenience function
def run_ingestion_workflow(
    file_paths: List[str],
    vector_store_name: str = "default",
    session_id: Optional[str] = None
) -> IngestState:
    """
    Run the document ingestion workflow

    Args:
        file_paths: List of file paths to ingest
        vector_store_name: Name of vector store to use
        session_id: Optional explicit session ID (for re-indexing)

    Returns:
        Final workflow state
    """
    # Create initial state
    initial_state: IngestState = {
        "file_paths": file_paths,
        "loaded_documents": None,
        "chunks": None,
        "embeddings": None,
        "indexed_count": 0,
        "status": "pending",
        "error": None,
        "session_id": session_id or str(uuid.uuid4()),  # Use provided or generate new
        "vector_store_name": vector_store_name,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
    }

    # Create and run graph
    graph = create_ingest_graph()

    print("="*70)
    print("🚀 Starting Document Ingestion Workflow")
    print("="*70)
    print(f"Session ID: {initial_state['session_id']}")
    print(f"Files: {len(file_paths)}")
    print(f"Vector Store: {vector_store_name}")
    print("="*70)

    # Run workflow
    final_state = graph.invoke(initial_state)

    # Print summary
    print("\n" + "="*70)
    if final_state["status"] == "completed":
        print("✅ Document Ingestion Completed Successfully!")
        print(f"   Indexed: {final_state['indexed_count']} chunks")
        print(f"   Duration: {final_state['started_at']} → {final_state['completed_at']}")
    else:
        print("❌ Document Ingestion Failed!")
        print(f"   Status: {final_state['status']}")
        print(f"   Error: {final_state['error']}")
    print("="*70)

    return final_state


if __name__ == "__main__":
    # Test the ingestion workflow
    import sys

    # Create sample documents if they don't exist
    sample_dir = Path("data/docs")
    sample_dir.mkdir(parents=True, exist_ok=True)

    test_file = sample_dir / "test_ingestion.txt"
    if not test_file.exists():
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""செயற்கை நுண்ணறிவு பற்றிய ஆவணம்

செயற்கை நுண்ணறிவு (AI) என்பது கணினிகள் மனித நுண்ணறிவை உருவகப்படுத்தும் தொழில்நுட்பம்.

முக்கிய பகுதிகள்:
- இயந்திரக் கற்றல் (Machine Learning)
- ஆழ்ந்த கற்றல் (Deep Learning)
- இயற்கை மொழி செயலாக்கம் (NLP)

பயன்பாடுகள்: மொழிபெயர்ப்பு, குரல் அடையாளம், படம் அடையாளம்.
""")
        print(f"Created test file: {test_file}")

    # Run ingestion
    result = run_ingestion_workflow(
        file_paths=[str(test_file)],
        vector_store_name="test_ingest"
    )

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "completed" else 1)
