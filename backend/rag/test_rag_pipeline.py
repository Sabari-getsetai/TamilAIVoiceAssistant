#!/usr/bin/env python3
"""
End-to-End RAG Pipeline Test

This script tests the complete RAG pipeline:
1. Document loading
2. Text chunking
3. Embedding generation
4. Vector store operations
5. Retrieval
6. Prompt generation
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.rag.loaders import DocumentLoaderFactory
from backend.rag.chunking import TextChunker
from backend.rag.embeddings import get_embedding_model
from backend.rag.vectorstore import VectorStore, Document
from backend.rag.prompts import get_rag_prompt_builder
from backend.settings import settings


def test_rag_pipeline():
    """Run complete RAG pipeline test"""

    print("="*70)
    print("🧪 RAG Pipeline End-to-End Test")
    print("="*70)

    # Step 1: Create sample documents
    print("\n📝 Step 1: Creating sample Tamil documents...")
    print("-"*70)

    sample_docs_dir = Path("data/docs")
    sample_docs_dir.mkdir(parents=True, exist_ok=True)

    # Create sample Tamil documents
    documents_content = {
        "ai_basics.txt": """செயற்கை நுண்ணறிவு (Artificial Intelligence)

செயற்கை நுண்ணறிவு என்பது கணினிகள் மனித நுண்ணறிவை உருவகப்படுத்தும் தொழில்நுட்பம்.

முக்கிய பகுப்புகள்:
1. இயந்திரக் கற்றல் (Machine Learning) - தரவுகளிலிருந்து கற்றல்
2. ஆழ்ந்த கற்றல் (Deep Learning) - நரம்பியல் வலைகள்
3. இயற்கை மொழி செயலாக்கம் (NLP) - மொழி புரிதல்

பயன்பாடுகள்: மொழிபெயர்ப்பு, குரல் அடையாளம், படம் அடையாளம்.""",

        "tamil_language.txt": """தமிழ் மொழி

தமிழ் உலகின் பழமையான மொழிகளில் ஒன்று. திராவிட மொழிக் குடும்பத்தைச் சேர்ந்தது.

சிறப்பியல்புகள்:
- 2000 ஆண்டுகளுக்கு மேலான இலக்கிய வரலாறு
- செம்மையான இலக்கண அமைப்பு
- வளமான இலக்கியம்

தமிழ் இலக்கியம்: சங்க இலக்கியம், சிலப்பதிகாரம், கம்பராமாயணம், திருக்குறள்.""",

        "technology.txt": """தொழில்நுட்ப வளர்ச்சி

21ம் நூற்றாண்டில் தொழில்நுட்பம் வேகமாக வளர்ந்து வருகிறது.

முக்கிய தொழில்நுட்பங்கள்:
- செயற்கை நுண்ணறிவு
- பிளாக்செயின்
- இணைய பாதுகாப்பு
- குவாண்டம் கம்ப்யூட்டிங்

எதிர்காலம்: மேலும் மேம்பட்ட AI அமைப்புகள், தானியங்கி வாகனங்கள்.""",
    }

    # Write sample documents
    for filename, content in documents_content.items():
        filepath = sample_docs_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created: {filename}")

    # Step 2: Load documents
    print("\n📂 Step 2: Loading documents...")
    print("-"*70)

    loaded_docs = DocumentLoaderFactory.load_directory(
        sample_docs_dir,
        file_extensions=['.txt']
    )
    print(f"\n✅ Loaded {len(loaded_docs)} documents")

    # Step 3: Chunk documents
    print("\n✂️  Step 3: Chunking documents...")
    print("-"*70)

    chunker = TextChunker(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        strategy="sentence"
    )

    all_chunks = []
    for doc in loaded_docs:
        chunks = chunker.chunk_text(
            doc.content,
            metadata={**doc.metadata, "source_file": doc.metadata["filename"]}
        )
        all_chunks.extend(chunks)
        print(f"  {doc.metadata['filename']}: {len(chunks)} chunks")

    print(f"\n✅ Total chunks created: {len(all_chunks)}")

    # Step 4: Generate embeddings
    print("\n🧮 Step 4: Generating embeddings...")
    print("-"*70)

    embedding_model = get_embedding_model()
    if not embedding_model.load():
        print("❌ Failed to load embedding model")
        return False

    # Generate embeddings for all chunks
    chunk_texts = [chunk.text for chunk in all_chunks]
    embeddings = embedding_model.encode_documents(
        chunk_texts,
        show_progress=True
    )

    print(f"✅ Generated {len(embeddings)} embeddings")
    print(f"   Embedding dimension: {embeddings.shape[1]}")

    # Step 5: Create vector store and add documents
    print("\n🗄️  Step 5: Building vector store...")
    print("-"*70)

    vector_store = VectorStore(
        embedding_dimension=embedding_model.get_dimension(),
        store_name="test_rag"
    )

    # Convert chunks to Document objects
    documents = []
    for i, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
        doc = Document(
            id=f"chunk_{i}",
            text=chunk.text,
            embedding=embedding,
            metadata=chunk.metadata
        )
        documents.append(doc)

    # Add to vector store
    added_ids = vector_store.add_documents(documents, embeddings)
    print(f"✅ Added {len(added_ids)} documents to vector store")

    # Get stats
    stats = vector_store.get_stats()
    print(f"\nVector Store Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Save vector store
    print("\n💾 Saving vector store...")
    vector_store.save()

    # Step 6: Test retrieval
    print("\n🔍 Step 6: Testing retrieval...")
    print("-"*70)

    test_queries = [
        "செயற்கை நுண்ணறிவு என்றால் என்ன?",
        "தமிழ் மொழியின் சிறப்பு என்ன?",
        "எதிர்கால தொழில்நுட்பம் என்ன?",
    ]

    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-"*50)

        # Generate query embedding
        query_embedding = embedding_model.encode_query(query)

        # Search
        results = vector_store.search(
            query_embedding,
            k=settings.RETRIEVAL_K
        )

        print(f"Found {len(results)} relevant documents:")
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n  [{i}] Score: {score:.4f}")
            print(f"      Source: {doc.metadata.get('source_file', 'Unknown')}")
            print(f"      Text: {doc.text[:100]}...")

    # Step 7: Test RAG prompt generation
    print("\n📋 Step 7: Testing RAG prompt generation...")
    print("-"*70)

    query = "செயற்கை நுண்ணறிவு என்றால் என்ன?"
    print(f"\nQuery: {query}")

    # Get top K documents
    query_embedding = embedding_model.encode_query(query)
    results = vector_store.search(query_embedding, k=3)

    # Extract context
    context_docs = [doc.text for doc, score in results]

    # Build RAG prompt
    prompt_builder = get_rag_prompt_builder()
    rag_prompt = prompt_builder.build_with_context(
        question=query,
        context_documents=context_docs
    )

    print("\n" + "="*70)
    print("Generated RAG Prompt:")
    print("="*70)
    print(rag_prompt)

    # Summary
    print("\n" + "="*70)
    print("✅ RAG Pipeline Test Completed Successfully!")
    print("="*70)
    print(f"\nPipeline Summary:")
    print(f"  Documents loaded: {len(loaded_docs)}")
    print(f"  Chunks created: {len(all_chunks)}")
    print(f"  Embeddings generated: {len(embeddings)}")
    print(f"  Vector store size: {vector_store.index.ntotal}")
    print(f"  Embedding dimension: {embedding_model.get_dimension()}")
    print(f"\nVector store saved to: {settings.FAISS_DIR}/test_rag.*")

    return True


if __name__ == "__main__":
    try:
        success = test_rag_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
