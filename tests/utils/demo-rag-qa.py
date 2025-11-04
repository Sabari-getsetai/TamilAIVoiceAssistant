#!/usr/bin/env python3
"""
Tamil AI Voice Assistant - Complete RAG Q&A Demo

This demo showcases the complete pipeline:
1. Create sample Tamil documents
2. Ingest documents using LangGraph workflow
3. Perform RAG-based question answering with LLM
4. Display results with retrieved context

Prerequisites:
- Embedding model downloaded (run: python backend/models/download_models.py)
- HuggingFace API token (get free at: https://huggingface.co/settings/tokens)
- Set token: export HF_API_TOKEN='your_token' or add to .env file
"""
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.settings import settings
from backend.graphs import run_ingestion_workflow
from backend.rag import (
    get_embedding_model,
    VectorStore,
    get_rag_prompt_builder,
)
from backend.models import get_llm, initialize_llm


def create_sample_documents() -> List[Path]:
    """
    Create sample Tamil documents for demonstration

    Returns:
        List of created file paths
    """
    print("="*80)
    print("📝 Step 1: Creating Sample Tamil Documents")
    print("="*80)

    sample_dir = Path("data/docs/demo")
    sample_dir.mkdir(parents=True, exist_ok=True)

    documents = {
        "ai_basics.txt": """செயற்கை நுண்ணறிவு - அறிமுகம்

செயற்கை நுண்ணறிவு (Artificial Intelligence - AI) என்பது கணினிகள் மூலம் மனித நுண்ணறிவை உருவகப்படுத்தும் தொழில்நுட்பமாகும்.

முக்கிய கூறுகள்:

1. இயந்திரக் கற்றல் (Machine Learning)
   - தரவுகளிலிருந்து கற்றல்
   - முன்னறிவிப்பு மாதிரிகள்
   - வடிவங்களை அடையாளம் காணுதல்

2. ஆழ்ந்த கற்றல் (Deep Learning)
   - செயற்கை நரம்பியல் வலைகள்
   - படம் மற்றும் குரல் அடையாளம்
   - இயற்கை மொழி செயலாக்கம்

3. இயற்கை மொழி செயலாக்கம் (Natural Language Processing)
   - மொழி புரிதல்
   - மொழிபெயர்ப்பு
   - உரையாடல் அமைப்புகள்

பயன்பாடுகள்:
- மருத்துவ நோய் கண்டறிதல்
- தானியங்கி வாகனங்கள்
- குரல் உதவியாளர்கள்
- மொழிபெயர்ப்பு சேவைகள்
- பரிந்துரை அமைப்புகள்

எதிர்காலம்:
AI தொழில்நுட்பம் மனித வாழ்க்கையின் அனைத்து பகுதிகளிலும் பெரும் தாக்கத்தை ஏற்படுத்தும்.
""",

        "tamil_language.txt": """தமிழ் மொழி - ஒரு பார்வை

தமிழ் மொழி உலகின் மிகப் பழமையான மொழிகளில் ஒன்றாகும். இது திராவிட மொழிக் குடும்பத்தின் முக்கிய மொழியாகும்.

வரலாறு:
- 2000 ஆண்டுகளுக்கும் மேலான எழுத்து வடிவ வரலாறு
- சங்க இலக்கிய காலம் (கி.மு. 300 - கி.பி. 300)
- செம்மொழி அந்தஸ்து பெற்ற மொழி

இலக்கணம்:
- தொல்காப்பியம் - முதல் இலக்கண நூல்
- எழுத்து, சொல், பொருள் என்ற மூன்று பகுப்புகள்
- 247 எழுத்துக்கள் (உயிர், மெய், உயிர்மெய்)

சிறப்பியல்புகள்:
1. தனித்துவமான எழுத்து முறை
2. வளமான இலக்கியம்
3. தொடர்ச்சியான பயன்பாடு
4. உலகளாவிய அங்கீகாரம்

பிரபல இலக்கியங்கள்:
- திருக்குறள் - வாழ்க்கை தத்துவம்
- சிலப்பதிகாரம் - காவியம்
- கம்பராமாயணம் - இதிகாசம்
- சங்க இலக்கியம் - கவிதைகள்

நவீன தமிழ்:
இன்று 8 கோடி மக்களால் பேசப்படும் தமிழ், தொழில்நுட்ப துறையிலும் முன்னேறி வருகிறது.
""",

        "technology_trends.txt": """தொழில்நுட்ப போக்குகள் - 2025

21ம் நூற்றாண்டில் தொழில்நுட்பம் வேகமாக முன்னேறி வருகிறது.

முக்கிய தொழில்நுட்பங்கள்:

1. செயற்கை நுண்ணறிவு (AI)
   - Generative AI மாதிரிகள்
   - ChatGPT, GPT-4 போன்ற மொழி மாதிரிகள்
   - தானியங்கு குறியீடு உருவாக்கம்

2. குவாண்டம் கம்ப்யூட்டிங்
   - அதிவேக கணினி செயலாக்கம்
   - சிக்கலான சிக்கல்களை தீர்த்தல்
   - குறியாக்கவியல் புதிய சகாப்தம்

3. பிளாக்செயின் மற்றும் Web3
   - பரவலாக்கப்பட்ட அமைப்புகள்
   - நிதி தொழில்நுட்பம் (DeFi)
   - NFT மற்றும் டிஜிட்டல் சொத்துக்கள்

4. இணைய பாதுகாப்பு
   - Zero Trust Architecture
   - AI-சார்ந்த பாதுகாப்பு
   - தரவு தனியுரிமை

5. Edge Computing மற்றும் IoT
   - நுண்ணறிவு சாதனங்கள்
   - 5G இணைப்பு
   - நகர்ப்புற தானியங்கி அமைப்புகள்

எதிர்காலம்:
இந்த தொழில்நுட்பங்கள் ஒன்றிணைந்து புதிய சாத்தியங்களை உருவாக்கும்.
""",

        "healthcare_ai.txt": """மருத்துவத்தில் செயற்கை நுண்ணறிவு

AI மருத்துவ துறையில் புரட்சிகரமான மாற்றங்களை ஏற்படுத்தி வருகிறது.

பயன்பாடுகள்:

1. நோய் கண்டறிதல்
   - மருத்துவ படங்களை பகுப்பாய்வு செய்தல்
   - புற்றுநோய் கண்டறிதல்
   - தோல் நோய்கள் அடையாளம்

2. மருந்து கண்டுபிடிப்பு
   - புதிய மருந்துகள் வடிவமைப்பு
   - மருந்து பரிசோதனை துரிதப்படுத்தல்
   - தனிப்பயன் மருத்துவம்

3. நோயாளி கண்காணிப்பு
   - தொடர்ச்சியான உயிரியல் அளவீடுகள்
   - முன்கூட்டிய எச்சரிக்கை அமைப்புகள்
   - தொலை மருத்துவம்

4. அறுவை சிகிச்சை உதவி
   - ரோபோடிக் அறுவை சிகிச்சை
   - துல்லியமான செயல்பாடுகள்
   - குறைந்த மீட்பு நேரம்

நன்மைகள்:
- விரைவான மற்றும் துல்லியமான கண்டறிதல்
- செலவு குறைப்பு
- சிறந்த நோயாளி பராமரிப்பு
- மருத்துவர்களுக்கு அதிக நேரம்

சவால்கள்:
- தரவு தனியுரிமை
- நெறிமுறை கேள்விகள்
- பயிற்சி தேவை
- ஒழுங்குமுறை அங்கீகாரம்
""",
    }

    created_files = []
    for filename, content in documents.items():
        filepath = sample_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        created_files.append(filepath)
        print(f"  ✅ Created: {filename} ({len(content)} chars)")

    print(f"\n✅ Created {len(created_files)} sample documents")
    return created_files


def ingest_documents(file_paths: List[Path]) -> bool:
    """
    Ingest documents using LangGraph workflow

    Args:
        file_paths: List of document paths

    Returns:
        True if successful
    """
    print("\n" + "="*80)
    print("🔄 Step 2: Ingesting Documents with LangGraph Workflow")
    print("="*80)

    result = run_ingestion_workflow(
        file_paths=[str(p) for p in file_paths],
        vector_store_name="demo"
    )

    return result["status"] == "completed"


def query_rag_system(question: str, vector_store_name: str = "demo") -> Tuple[str, List[str]]:
    """
    Query the RAG system with a question

    Args:
        question: Question to ask
        vector_store_name: Vector store to query

    Returns:
        Tuple of (answer, context_documents)
    """
    # Load embedding model
    embedding_model = get_embedding_model()
    if not embedding_model.is_loaded():
        embedding_model.load()

    # Load vector store
    vector_store = VectorStore(
        embedding_dimension=embedding_model.get_dimension(),
        store_name=vector_store_name
    )

    if not vector_store.load():
        raise RuntimeError("Vector store not found. Run ingestion first.")

    # Generate query embedding
    query_embedding = embedding_model.encode_query(question)

    # Search for relevant documents
    results = vector_store.search(
        query_embedding,
        k=settings.RETRIEVAL_K
    )

    # Extract context documents
    context_docs = [doc.text for doc, score in results]

    # Build RAG prompt
    prompt_builder = get_rag_prompt_builder()
    rag_prompt = prompt_builder.build_with_context(
        question=question,
        context_documents=context_docs
    )

    # Initialize Unified LLM (Local or Cloud based on settings)
    print("\n🤖 Initializing LLM...")
    llm = get_llm()
    
    # Show current backend configuration
    backend = llm.get_current_backend()
    model_info = llm.get_model_info()
    print(f"   Backend: {backend}")
    print(f"   Model: {model_info['model_name']}")
    
    if not llm.is_loaded():
        print(f"   Connecting to {backend} backend...")
        if not initialize_llm():
            print(f"⚠️  {backend} backend not available. Showing retrieved context only.")
            if backend == "local":
                print("\n   Local setup instructions:")
                print("   1. Start Ollama: docker compose -f docker-compose.dev.yml up -d ollama")
                print("   2. Load model: docker exec tamil-assistant-ollama ollama pull tinyllama")
            else:
                print("\n   Cloud setup instructions:")
                print("   1. Get HuggingFace token: https://huggingface.co/settings/tokens")
                print("   2. Set in .env: HF_API_TOKEN=your_token")
                print("   3. Or try local mode: set USE_LOCAL_LLM=true in .env")
            
            answer = f"⚠️ {backend} backend not available.\n\n"
            answer += "**Retrieved Context:**\n\n"
            for i, doc in enumerate(context_docs, 1):
                answer += f"[{i}] {doc[:300]}...\n\n"
            return answer, context_docs

    print(f"✅ Using {backend} backend with model: {model_info['model_name']}")

    # Generate answer with unified LLM
    answer = llm.generate(
        prompt=rag_prompt,
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )

    return answer, context_docs


def run_demo():
    """Run the complete RAG Q&A demo"""
    print("\n" + "="*80)
    print("🚀 Tamil AI Voice Assistant - RAG Q&A Demo")
    print("="*80)
    print("\nThis demo demonstrates:")
    print("1. Document ingestion with LangGraph workflow")
    print("2. RAG-based question answering with LLM")
    print("3. Tamil and English language support")
    print("="*80)

    try:
        # Step 1: Create sample documents
        file_paths = create_sample_documents()

        # Step 2: Ingest documents
        if not ingest_documents(file_paths):
            print("\n❌ Document ingestion failed!")
            return False

        # Step 3: Query the RAG system
        print("\n" + "="*80)
        print("💬 Step 3: Querying the RAG System")
        print("="*80)

        test_questions = [
            "செயற்கை நுண்ணறிவு என்றால் என்ன?",
            "What are the main components of AI?",
            "தமிழ் மொழியின் சிறப்பு என்ன?",
            "மருத்துவத்தில் AI எப்படி பயன்படுகிறது?",
            "What are the technology trends in 2025?",
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n{'-'*80}")
            print(f"Question {i}: {question}")
            print(f"{'-'*80}")

            try:
                answer, context_docs = query_rag_system(question)

                # Display retrieved context
                print(f"\n📚 Retrieved Context ({len(context_docs)} documents):")
                for j, doc in enumerate(context_docs, 1):
                    preview = doc[:150] + "..." if len(doc) > 150 else doc
                    print(f"\n  [{j}] {preview}")

                # Display answer
                print(f"\n💡 Answer:")
                print(f"{answer}")

            except Exception as e:
                print(f"❌ Error: {e}")
                continue

        # Summary
        print("\n" + "="*80)
        print("✅ Demo Completed Successfully!")
        print("="*80)
        print("\nWhat was demonstrated:")
        print("  ✅ Document creation and loading")
        print("  ✅ LangGraph ingestion workflow")
        print("  ✅ Text chunking and embedding generation")
        print("  ✅ FAISS vector store indexing")
        print("  ✅ Similarity search and retrieval")
        print("  ✅ RAG prompt generation")
        print("  ✅ LLM-based answer generation")
        print("  ✅ Tamil and English query support")
        print("\n" + "="*80)

        return True

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)
