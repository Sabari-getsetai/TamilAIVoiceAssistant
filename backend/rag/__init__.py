"""
RAG (Retrieval-Augmented Generation) Pipeline

This package provides all components for the RAG pipeline:
- Document loaders (PDF, DOCX, TXT)
- Text chunking strategies
- Embedding model management
- FAISS vector store
- Tamil-optimized prompts
"""

from backend.rag.loaders import (
    DocumentLoaderFactory,
    LoadedDocument,
    PDFLoader,
    DOCXLoader,
    TXTLoader,
)

from backend.rag.chunking import (
    TextChunker,
    Chunk,
)

from backend.rag.embeddings import (
    EmbeddingModel,
    get_embedding_model,
    initialize_embeddings,
)

from backend.rag.vectorstore import (
    VectorStore,
    Document,
)

from backend.rag.prompts import (
    PromptTemplate,
    PromptBuilder,
    RAG_QA_TEMPLATE,
    CONVERSATIONAL_RAG_TEMPLATE,
    CODE_MIXED_RAG_TEMPLATE,
    get_rag_prompt_builder,
    get_conversational_rag_builder,
    get_code_mixed_builder,
)


__all__ = [
    # Loaders
    "DocumentLoaderFactory",
    "LoadedDocument",
    "PDFLoader",
    "DOCXLoader",
    "TXTLoader",

    # Chunking
    "TextChunker",
    "Chunk",

    # Embeddings
    "EmbeddingModel",
    "get_embedding_model",
    "initialize_embeddings",

    # Vector Store
    "VectorStore",
    "Document",

    # Prompts
    "PromptTemplate",
    "PromptBuilder",
    "RAG_QA_TEMPLATE",
    "CONVERSATIONAL_RAG_TEMPLATE",
    "CODE_MIXED_RAG_TEMPLATE",
    "get_rag_prompt_builder",
    "get_conversational_rag_builder",
    "get_code_mixed_builder",
]
