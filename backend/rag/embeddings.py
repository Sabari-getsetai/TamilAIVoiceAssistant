"""
Embedding Model Management for Tamil AI Voice Assistant

This module handles loading and managing the multilingual embedding model
for Tamil text. Uses SentenceTransformers with paraphrase-multilingual-MiniLM-L12-v2
which supports Tamil, English, and code-mixed text.
"""
import sys
from pathlib import Path
from typing import List, Union, Optional
import numpy as np


from backend.settings import settings

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "sentence-transformers not installed. "
        "Run: pip install sentence-transformers>=3.0.0"
    )


class EmbeddingModel:
    """
    Manages multilingual embedding model for Tamil text encoding

    Features:
    - Supports Tamil, English, and code-mixed text
    - 384-dimensional embeddings
    - Optimized for semantic similarity
    - Batch processing support
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding model

        Args:
            model_name: HuggingFace model name (default from settings)
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.model: Optional[SentenceTransformer] = None
        self.embedding_dimension: int = 0

    def load(self) -> bool:
        """
        Load the embedding model from cache or download if needed

        Returns:
            bool: True if loaded successfully
        """
        try:
            print(f"📥 Loading embedding model: {self.model_name}")

            # Load model (will use cache if available)
            self.model = SentenceTransformer(self.model_name)

            # Get embedding dimension
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()

            print(f"✅ Embedding model loaded successfully!")
            print(f"   Dimension: {self.embedding_dimension}")
            print(f"   Max sequence length: {self.model.max_seq_length}")

            return True

        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            return False

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Encode text(s) into embeddings

        Args:
            texts: Single text string or list of texts
            batch_size: Batch size for processing multiple texts
            show_progress: Show progress bar for batch processing
            normalize: Normalize embeddings to unit length (recommended for cosine similarity)

        Returns:
            numpy array of embeddings (shape: [num_texts, embedding_dim])

        Raises:
            RuntimeError: If model not loaded
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]

        try:
            # Encode texts
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=normalize,
                convert_to_numpy=True,
            )

            return embeddings

        except Exception as e:
            print(f"❌ Error encoding texts: {e}")
            raise

    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a single query text (optimized for retrieval)

        Args:
            query: Query text in Tamil or English

        Returns:
            numpy array of embedding (shape: [embedding_dim])
        """
        # For query, we always normalize for cosine similarity
        embeddings = self.encode(query, normalize=True)
        return embeddings[0]  # Return single embedding

    def encode_documents(
        self,
        documents: List[str],
        batch_size: int = 32,
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        Encode multiple documents for indexing

        Args:
            documents: List of document texts
            batch_size: Batch size for processing
            show_progress: Show progress bar

        Returns:
            numpy array of embeddings (shape: [num_docs, embedding_dim])
        """
        return self.encode(
            documents,
            batch_size=batch_size,
            show_progress=show_progress,
            normalize=True,
        )

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1, higher is more similar)
        """
        # Assuming normalized embeddings, cosine similarity is dot product
        return float(np.dot(embedding1, embedding2))

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dimension


# Global embedding model instance (singleton pattern)
_embedding_instance: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    """
    Get or create the global embedding model instance

    Returns:
        EmbeddingModel instance
    """
    global _embedding_instance

    if _embedding_instance is None:
        _embedding_instance = EmbeddingModel()

    return _embedding_instance


def initialize_embeddings() -> bool:
    """
    Initialize the global embedding model instance

    Returns:
        bool: True if initialized successfully
    """
    model = get_embedding_model()
    if not model.is_loaded():
        return model.load()
    return True


if __name__ == "__main__":
    # Test embedding model
    print("="*60)
    print("🧪 Testing Embedding Model")
    print("="*60)

    # Initialize model
    model = get_embedding_model()

    if model.load():
        print("\n" + "="*60)
        print("🧪 Test 1: Tamil Text Encoding")
        print("="*60)

        tamil_texts = [
            "வணக்கம், நான் ஒரு AI உதவியாளர்",  # Hello, I am an AI assistant
            "இன்று வானிலை எப்படி உள்ளது?",  # How is the weather today?
            "நன்றி, உங்கள் உதவிக்கு",  # Thank you for your help
        ]

        embeddings = model.encode_documents(tamil_texts)
        print(f"\n✅ Encoded {len(tamil_texts)} Tamil texts")
        print(f"   Embedding shape: {embeddings.shape}")

        # Test similarity
        sim = model.similarity(embeddings[0], embeddings[1])
        print(f"\n📊 Similarity between first two texts: {sim:.4f}")

        print("\n" + "="*60)
        print("🧪 Test 2: Mixed Language (Tamil + English)")
        print("="*60)

        mixed_text = "Hello வணக்கம், this is code-mixed text"
        embedding = model.encode_query(mixed_text)
        print(f"\n✅ Encoded mixed language text")
        print(f"   Embedding shape: {embedding.shape}")

        print("\n" + "="*60)
        print("🧪 Test 3: Query Encoding")
        print("="*60)

        query = "AI உதவியாளர் பற்றி சொல்லுங்கள்"  # Tell me about AI assistant
        query_embedding = model.encode_query(query)

        # Find most similar document
        similarities = [model.similarity(query_embedding, doc_emb) for doc_emb in embeddings]
        most_similar_idx = np.argmax(similarities)

        print(f"\nQuery: {query}")
        print(f"Most similar document: {tamil_texts[most_similar_idx]}")
        print(f"Similarity score: {similarities[most_similar_idx]:.4f}")

        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
    else:
        print("\n❌ Failed to load embedding model")
        print("\nTo download the model, run:")
        print("   python backend/models/download_models.py")
