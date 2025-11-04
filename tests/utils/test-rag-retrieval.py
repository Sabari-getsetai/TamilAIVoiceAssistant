#!/usr/bin/env python3
"""
Quick test script to verify RAG retrieval is working correctly
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.rag.vectorstore import VectorStore
from backend.rag.embeddings import get_embedding_model

def test_rag_retrieval():
    print("="*70)
    print("🧪 Testing RAG Retrieval Integration")
    print("="*70)

    # Initialize components
    print("\n1️⃣ Initializing embedding model...")
    embeddings = get_embedding_model()
    print(f"   ✅ Embedding model loaded: {type(embeddings).__name__}")

    # Initialize vector store
    print("\n2️⃣ Initializing vector store...")
    vectorstore = VectorStore(
        embedding_dimension=384,
        store_name="default"
    )
    print(f"   ✅ VectorStore created")

    # Check if index exists
    print("\n3️⃣ Checking if FAISS index exists...")
    if not vectorstore.index_exists():
        print("   ❌ FAISS index not found!")
        print("   💡 Please upload and ingest documents via admin dashboard first")
        return False
    print(f"   ✅ FAISS index exists")

    # Load the index
    print("\n4️⃣ Loading FAISS index...")
    if not vectorstore.load_index():
        print("   ❌ Failed to load FAISS index!")
        return False
    print(f"   ✅ Index loaded successfully")
    print(f"   📊 Total documents: {len(vectorstore.documents)}")
    print(f"   📊 Index size: {vectorstore.index.ntotal}")

    # Test similarity search with a query
    test_queries = [
        "what is artificial intelligence",
        "செயற்கை நுண்ணறிவு என்றால் என்ன",
        "machine learning",
    ]

    print(f"\n5️⃣ Testing similarity_search() method...")
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        try:
            docs = vectorstore.similarity_search(
                query,
                k=3,
                embedding_model=embeddings
            )

            if docs:
                print(f"   ✅ Retrieved {len(docs)} documents")
                for i, doc in enumerate(docs):
                    score = doc.metadata.get('score', 0.0)
                    preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                    print(f"\n   {i+1}. Score: {score:.4f}")
                    print(f"      Preview: {preview}")
                    print(f"      Metadata: {doc.metadata}")
            else:
                print(f"   ⚠️  No documents retrieved (query may not match indexed content)")

        except Exception as e:
            print(f"   ❌ Error during search: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n" + "="*70)
    print("✅ RAG Retrieval Test Complete!")
    print("="*70)
    return True

if __name__ == "__main__":
    success = test_rag_retrieval()
    sys.exit(0 if success else 1)
