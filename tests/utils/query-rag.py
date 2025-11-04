#!/usr/bin/env python3
"""
Simple RAG Query Interface

Quick script to query an existing vector store without re-ingesting documents.

Usage:
    python query_rag.py "Your question here"
    python query_rag.py "செயற்கை நுண்ணறிவு என்றால் என்ன?"

Prerequisites:
    - Documents already ingested (run demo_rag_qa.py first)
    - Ollama running with a model
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.settings import settings
from backend.rag import get_embedding_model, VectorStore, get_rag_prompt_builder
from backend.models.llm_huggingface import get_hf_llm


def query(question: str, vector_store_name: str = "demo", show_context: bool = True):
    """
    Query the RAG system

    Args:
        question: Question to ask
        vector_store_name: Vector store to query
        show_context: Whether to show retrieved context
    """
    print("="*80)
    print("🔍 Tamil AI Voice Assistant - RAG Query")
    print("="*80)
    print(f"\n📝 Question: {question}")
    print("-"*80)

    # Load embedding model
    print("\n🧮 Loading embedding model...")
    embedding_model = get_embedding_model()
    if not embedding_model.is_loaded():
        embedding_model.load()

    # Load vector store
    print(f"🗄️  Loading vector store: {vector_store_name}")
    vector_store = VectorStore(
        embedding_dimension=embedding_model.get_dimension(),
        store_name=vector_store_name
    )

    if not vector_store.load():
        print(f"\n❌ Vector store '{vector_store_name}' not found!")
        print("\nPlease run one of the following first:")
        print("  1. python demo_rag_qa.py  (creates 'demo' vector store)")
        print("  2. python backend/rag/test_rag_pipeline.py  (creates 'test_rag' vector store)")
        print("  3. Use the Admin API to ingest documents")
        return

    print(f"  ✅ Loaded vector store with {vector_store.index.ntotal} documents")

    # Generate query embedding
    print(f"\n🔍 Searching for relevant documents...")
    query_embedding = embedding_model.encode_query(question)

    # Search
    results = vector_store.search(
        query_embedding,
        k=settings.RETRIEVAL_K
    )

    if not results:
        print("\n⚠️  No relevant documents found!")
        return

    # Extract context
    context_docs = [doc.text for doc, score in results]

    # Show context if requested
    if show_context:
        print(f"\n📚 Retrieved Context ({len(results)} documents):")
        print("-"*80)
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n[{i}] Score: {score:.4f}")
            print(f"Source: {doc.metadata.get('filename', 'Unknown')}")
            preview = doc.text[:200] + "..." if len(doc.text) > 200 else doc.text
            print(f"Text: {preview}\n")

    # Build RAG prompt
    prompt_builder = get_rag_prompt_builder()
    rag_prompt = prompt_builder.build_with_context(
        question=question,
        context_documents=context_docs
    )

    # Load LLM (HuggingFace Inference API)
    print("🤖 Loading HuggingFace model...")
    llm = get_hf_llm()
    if not llm.is_loaded():
        if not llm.load_model():
            print("\n⚠️  HuggingFace API not available. Showing context only.")
            print("   Setup: Get free token at https://huggingface.co/settings/tokens")
            print("   Set: export HF_API_TOKEN='your_token'")
            return

    # Generate answer
    print("💭 Generating answer...\n")
    print("="*80)
    print("💡 Answer:")
    print("="*80)

    answer = llm.generate(
        prompt=rag_prompt,
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
        stream=False
    )

    print(answer)
    print("\n" + "="*80)


def interactive_mode():
    """Run in interactive mode"""
    print("="*80)
    print("🔍 Tamil AI Voice Assistant - Interactive RAG Query")
    print("="*80)
    print("\nEnter your questions (or 'quit' to exit)")
    print("You can ask in Tamil or English!")
    print("-"*80)

    while True:
        try:
            question = input("\n❓ Your question: ").strip()

            if not question:
                continue

            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            query(question, show_context=False)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Command line mode
        question = " ".join(sys.argv[1:])
        query(question)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
