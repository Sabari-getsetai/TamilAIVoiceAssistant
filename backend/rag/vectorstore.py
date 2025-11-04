"""
FAISS Vector Store Management for Tamil AI Voice Assistant

This module provides FAISS-based vector store for efficient similarity search
and retrieval. Supports persistence, incremental updates, and batch operations.
"""
import sys
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.settings import settings

try:
    import faiss
except ImportError:
    raise ImportError(
        "faiss-cpu not installed. "
        "Run: pip install faiss-cpu>=1.8.0"
    )


@dataclass
class Document:
    """Represents a document in the vector store"""
    id: str
    text: str
    embedding: Optional[np.ndarray] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary (excluding embedding)"""
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata or {}
        }


class VectorStore:
    """
    FAISS-based vector store for similarity search

    Features:
    - Efficient similarity search with FAISS IndexFlatIP (inner product)
    - Persistent storage (index + metadata)
    - Incremental updates (add/delete documents)
    - Batch operations
    - Metadata filtering
    """

    def __init__(
        self,
        embedding_dimension: int = 384,
        store_name: str = "default",
        persist_directory: Optional[Path] = None,
    ):
        """
        Initialize vector store

        Args:
            embedding_dimension: Dimension of embeddings
            store_name: Name for this vector store
            persist_directory: Directory to save/load index (default from settings)
        """
        self.embedding_dimension = embedding_dimension
        self.store_name = store_name
        self.persist_directory = persist_directory or settings.FAISS_DIR

        # FAISS index (using IndexFlatIP for cosine similarity with normalized vectors)
        self.index: Optional[faiss.Index] = None

        # Document storage (id -> Document)
        self.documents: Dict[str, Document] = {}

        # ID to index mapping for FAISS
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}

        # Counter for next index
        self.next_index = 0

        # Initialize index
        self._create_index()

    def _create_index(self):
        """Create a new FAISS index"""
        # IndexFlatIP for inner product (works as cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dimension)

    def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[np.ndarray] = None,
    ) -> List[str]:
        """
        Add documents to the vector store

        Args:
            documents: List of Document objects
            embeddings: Optional pre-computed embeddings (if not in documents)

        Returns:
            List of document IDs added
        """
        if not documents:
            return []

        # Prepare embeddings
        if embeddings is not None:
            # Use provided embeddings
            embedding_matrix = embeddings
        else:
            # Extract from documents
            embedding_matrix = np.array([doc.embedding for doc in documents])

        # Validate embeddings
        if embedding_matrix.shape[0] != len(documents):
            raise ValueError("Number of embeddings must match number of documents")

        if embedding_matrix.shape[1] != self.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch. Expected {self.embedding_dimension}, "
                f"got {embedding_matrix.shape[1]}"
            )

        # Ensure embeddings are in correct format for FAISS (float32, C-contiguous)
        embedding_matrix = np.ascontiguousarray(embedding_matrix, dtype=np.float32)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embedding_matrix)

        # Add to FAISS index
        self.index.add(embedding_matrix)

        # Store documents and mappings
        added_ids = []
        for i, doc in enumerate(documents):
            current_index = self.next_index + i

            # Store document
            self.documents[doc.id] = doc
            self.id_to_index[doc.id] = current_index
            self.index_to_id[current_index] = doc.id
            added_ids.append(doc.id)

        # Update next index
        self.next_index += len(documents)

        return added_ids

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 4,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_metadata: Optional metadata filters (exact match)

        Returns:
            List of (Document, score) tuples, sorted by relevance
        """
        if self.index.ntotal == 0:
            return []

        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)

        # Search in FAISS
        # Get more results if we need to filter
        search_k = k * 10 if filter_metadata else k
        scores, indices = self.index.search(query_embedding, min(search_k, self.index.ntotal))

        # Convert to results
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            doc_id = self.index_to_id.get(idx)
            if doc_id is None:
                continue

            doc = self.documents.get(doc_id)
            if doc is None:
                continue

            # Apply metadata filter if provided
            if filter_metadata:
                if not self._matches_filter(doc, filter_metadata):
                    continue

            results.append((doc, float(score)))

            # Stop if we have enough results
            if len(results) >= k:
                break

        return results

    def _matches_filter(self, doc: Document, filter_metadata: Dict) -> bool:
        """
        Check if document matches metadata filter

        Args:
            doc: Document to check
            filter_metadata: Metadata filters (all must match)

        Returns:
            True if document matches all filters
        """
        if not doc.metadata:
            return False

        for key, value in filter_metadata.items():
            if doc.metadata.get(key) != value:
                return False

        return True

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        embedding_model=None,
        filter_metadata: Optional[Dict] = None
    ) -> List:
        """
        Search for similar documents using text query

        This is a LangChain-compatible interface that wraps the search() method.

        Args:
            query: Text query to search for
            k: Number of results to return
            embedding_model: Embedding model to encode the query (required)
            filter_metadata: Optional metadata filters

        Returns:
            List of Document objects (LangChain format with page_content and metadata)
        """
        if embedding_model is None:
            # Try to get from backend.rag
            try:
                from backend.rag.embeddings import get_embedding_model, initialize_embeddings
                # Initialize embeddings if not already loaded
                initialize_embeddings()
                embedding_model = get_embedding_model()
            except Exception as e:
                raise ValueError("embedding_model required for similarity_search") from e

        # Generate query embedding
        if hasattr(embedding_model, 'embed_query'):
            # SentenceTransformer-style embedding
            query_embedding = embedding_model.embed_query(query)
        elif hasattr(embedding_model, 'encode'):
            # Direct encode method
            # Ensure model is loaded
            if hasattr(embedding_model, 'model') and embedding_model.model is None:
                if hasattr(embedding_model, 'load'):
                    embedding_model.load()
            query_embedding = embedding_model.encode(query)
        else:
            raise ValueError("embedding_model must have embed_query() or encode() method")

        # Convert to numpy array
        query_embedding = np.array(query_embedding)

        # Search
        results = self.search(query_embedding, k=k, filter_metadata=filter_metadata)

        # Convert to LangChain Document format
        from langchain_core.documents import Document as LangChainDocument

        langchain_docs = []
        for doc, score in results:
            langchain_doc = LangChainDocument(
                page_content=doc.text,
                metadata={
                    **(doc.metadata or {}),
                    "id": doc.id,
                    "score": float(score)  # Store score in metadata
                }
            )
            langchain_docs.append(langchain_doc)

        return langchain_docs

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID"""
        return self.documents.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document from vector store

        Note: FAISS doesn't support efficient deletion, so we just mark as deleted
        and rebuild index periodically

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted, False if not found
        """
        if doc_id not in self.documents:
            return False

        # Remove from documents
        del self.documents[doc_id]

        # Remove from mappings
        if doc_id in self.id_to_index:
            index = self.id_to_index[doc_id]
            del self.id_to_index[doc_id]
            del self.index_to_id[index]

        return True

    def rebuild_index(self, embedding_model=None):
        """
        Rebuild FAISS index from scratch (removes deleted documents)

        Args:
            embedding_model: Optional embedding model to regenerate embeddings.
                           If not provided and documents don't have embeddings, will raise error.
        """
        if not self.documents:
            self._create_index()
            self.id_to_index.clear()
            self.index_to_id.clear()
            self.next_index = 0
            return

        # Collect all documents
        docs = list(self.documents.values())

        # Check if documents have embeddings
        if docs[0].embedding is None:
            # Need to regenerate embeddings
            if embedding_model is None:
                # Try to get embedding model
                try:
                    from backend.rag.embeddings import get_embedding_model, initialize_embeddings
                    initialize_embeddings()
                    embedding_model = get_embedding_model()
                except Exception as e:
                    raise ValueError("Documents don't have embeddings and no embedding_model provided") from e

            # Generate embeddings
            texts = [doc.text for doc in docs]
            if hasattr(embedding_model, 'embed_documents'):
                embeddings = embedding_model.embed_documents(texts)
            elif hasattr(embedding_model, 'encode'):
                embeddings = embedding_model.encode(texts)
            else:
                raise ValueError("embedding_model must have embed_documents() or encode() method")

            embeddings = np.array(embeddings, dtype=np.float32)
        else:
            # Use existing embeddings
            embeddings = np.array([doc.embedding for doc in docs], dtype=np.float32)

        # Reset index
        self._create_index()
        self.id_to_index.clear()
        self.index_to_id.clear()
        self.next_index = 0

        # Re-add all documents
        self.add_documents(docs, embeddings)

    def save(self) -> bool:
        """
        Save vector store to disk

        Returns:
            True if saved successfully
        """
        try:
            # Ensure directory exists
            self.persist_directory.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            index_path = self.persist_directory / f"{self.store_name}.index"
            faiss.write_index(self.index, str(index_path))

            # Save metadata (documents, mappings)
            metadata_path = self.persist_directory / f"{self.store_name}.metadata"
            metadata = {
                "documents": {doc_id: doc.to_dict() for doc_id, doc in self.documents.items()},
                "id_to_index": self.id_to_index,
                "index_to_id": {int(k): v for k, v in self.index_to_id.items()},  # Convert keys to int
                "next_index": self.next_index,
                "embedding_dimension": self.embedding_dimension,
            }

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            print(f"✅ Vector store saved to {self.persist_directory}/{self.store_name}.*")
            return True

        except Exception as e:
            print(f"❌ Error saving vector store: {e}")
            return False

    def load(self) -> bool:
        """
        Load vector store from disk

        Returns:
            True if loaded successfully
        """
        try:
            # Load FAISS index
            index_path = self.persist_directory / f"{self.store_name}.index"
            if not index_path.exists():
                print(f"⚠️  No saved index found at {index_path}")
                return False

            self.index = faiss.read_index(str(index_path))

            # Load metadata
            metadata_path = self.persist_directory / f"{self.store_name}.metadata"
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Restore documents (without embeddings)
            self.documents = {
                doc_id: Document(**doc_data)
                for doc_id, doc_data in metadata["documents"].items()
            }

            # Restore mappings
            self.id_to_index = metadata["id_to_index"]
            self.index_to_id = {int(k): v for k, v in metadata["index_to_id"].items()}
            self.next_index = metadata["next_index"]
            self.embedding_dimension = metadata["embedding_dimension"]

            print(f"✅ Vector store loaded from {self.persist_directory}/{self.store_name}.*")
            print(f"   Documents: {len(self.documents)}")
            print(f"   Index size: {self.index.ntotal}")

            return True

        except Exception as e:
            print(f"❌ Error loading vector store: {e}")
            return False

    def index_exists(self) -> bool:
        """
        Check if a saved index exists on disk

        Returns:
            True if index file exists
        """
        index_path = self.persist_directory / f"{self.store_name}.index"
        return index_path.exists()

    def load_index(self) -> bool:
        """
        Alias for load() method for compatibility

        Returns:
            True if loaded successfully
        """
        return self.load()

    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.embedding_dimension,
            "store_name": self.store_name,
        }


if __name__ == "__main__":
    # Test vector store
    print("="*60)
    print("🧪 Testing FAISS Vector Store")
    print("="*60)

    # Create sample documents with embeddings
    np.random.seed(42)
    docs = [
        Document(
            id="doc1",
            text="வணக்கம், நான் ஒரு AI உதவியாளர்",
            embedding=np.random.rand(384),
            metadata={"source": "tamil", "type": "greeting"}
        ),
        Document(
            id="doc2",
            text="இன்று வானிலை எப்படி உள்ளது?",
            embedding=np.random.rand(384),
            metadata={"source": "tamil", "type": "question"}
        ),
        Document(
            id="doc3",
            text="AI assistant for Tamil language",
            embedding=np.random.rand(384),
            metadata={"source": "english", "type": "description"}
        ),
    ]

    # Normalize embeddings
    for doc in docs:
        doc.embedding = doc.embedding / np.linalg.norm(doc.embedding)

    # Create vector store
    print("\n🔧 Creating vector store...")
    store = VectorStore(embedding_dimension=384, store_name="test")

    # Add documents
    print("\n📥 Adding documents...")
    added_ids = store.add_documents(docs)
    print(f"✅ Added {len(added_ids)} documents: {added_ids}")

    # Get stats
    print("\n📊 Vector store stats:")
    stats = store.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Search
    print("\n🔍 Searching for similar documents...")
    query_embedding = docs[0].embedding  # Use first doc as query
    results = store.search(query_embedding, k=2)

    print(f"\nTop {len(results)} results:")
    for i, (doc, score) in enumerate(results):
        print(f"\n{i+1}. Document ID: {doc.id}")
        print(f"   Text: {doc.text}")
        print(f"   Score: {score:.4f}")
        print(f"   Metadata: {doc.metadata}")

    # Test metadata filtering
    print("\n🔍 Searching with metadata filter (type='question')...")
    results = store.search(query_embedding, k=5, filter_metadata={"type": "question"})

    print(f"\nFiltered results: {len(results)}")
    for i, (doc, score) in enumerate(results):
        print(f"\n{i+1}. {doc.text} (score: {score:.4f})")

    # Test save/load
    print("\n💾 Testing save/load...")
    store.save()

    print("\n📂 Loading vector store...")
    new_store = VectorStore(embedding_dimension=384, store_name="test")
    if new_store.load():
        print("✅ Load successful!")
        print(f"   Documents in loaded store: {len(new_store.documents)}")

        # Verify search works on loaded store
        results = new_store.search(query_embedding, k=2)
        print(f"   Search results: {len(results)}")

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
