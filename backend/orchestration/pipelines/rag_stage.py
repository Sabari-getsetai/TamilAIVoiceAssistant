"""RAG (Retrieval-Augmented Generation) Pipeline Stage

This module handles document retrieval and context building for the conversation,
providing relevant information to enhance the LLM response.
"""

from typing import List, Dict, Any, Optional

from backend.orchestration.pipelines.base_pipeline import (
    BasePipelineStage, PipelineStageType, ConversationState, PipelineStageError
)
from backend.repositories.document_repository import DocumentRepository
from backend.rag import get_embedding_model, VectorStore, get_rag_prompt_builder


class RAGStage(BasePipelineStage):
    """RAG (Retrieval-Augmented Generation) pipeline stage"""

    def __init__(self):
        super().__init__(
            stage_type=PipelineStageType.RAG,
            stage_name="rag"
        )

        # Configure stage requirements
        self.required_inputs = ["user_text", "session_id"]
        self.provided_outputs = ["retrieved_documents", "context_used"]

        # RAG configuration
        self.similarity_threshold = 0.7
        self.max_documents = 5
        self.max_context_length = 2000

        # Initialize components
        self.document_repo = DocumentRepository()
        self.vector_store = None
        self.embedding_model = None
        self.rag_prompt_builder = None

    async def process(self, state: ConversationState) -> ConversationState:
        """
        Process user query through RAG to retrieve relevant context

        Args:
            state: Current conversation state

        Returns:
            Updated state with retrieved_documents and context_used

        Raises:
            PipelineStageError: If RAG processing fails
        """
        try:
            # Check if RAG is enabled for this session
            if not state.get("rag_enabled", True):
                self.logger.info("RAG disabled for this session, skipping retrieval")
                state["retrieved_documents"] = []
                state["context_used"] = ""
                return state

            # Get user query
            user_text = state["user_text"]
            if not user_text or not user_text.strip():
                self.logger.info("Empty user text, skipping RAG retrieval")
                state["retrieved_documents"] = []
                state["context_used"] = ""
                return state

            # Initialize RAG components if needed
            await self._initialize_rag_components()

            # Get organization context for document filtering
            organization_id = state.get("organization_id")
            user_id = state.get("user_id")

            # Generate query embedding
            query_embedding = await self._get_query_embedding(user_text)

            # Retrieve relevant documents
            retrieved_docs = await self._retrieve_documents(
                query_embedding=query_embedding,
                organization_id=organization_id,
                user_id=user_id
            )

            # Build context from retrieved documents
            context_text = await self._build_context_from_documents(retrieved_docs)

            # Update state with retrieval results
            state["retrieved_documents"] = retrieved_docs
            state["context_used"] = context_text

            # Add RAG metadata to custom context
            if "custom_context" not in state:
                state["custom_context"] = {}

            state["custom_context"]["rag_metadata"] = {
                "query": user_text,
                "num_documents_retrieved": len(retrieved_docs),
                "context_length": len(context_text),
                "similarity_threshold": self.similarity_threshold,
                "organization_id": organization_id
            }

            self.logger.info(
                f"RAG completed: Retrieved {len(retrieved_docs)} documents, "
                f"built context of {len(context_text)} characters"
            )

            return state

        except Exception as e:
            self.logger.error(f"RAG processing failed: {str(e)}")
            raise PipelineStageError(
                self.stage_name,
                f"RAG retrieval failed: {str(e)}",
                cause=e
            )

    async def _initialize_rag_components(self) -> None:
        """Initialize RAG components (embedding model, vector store, etc.)"""
        try:
            if not self.embedding_model:
                self.logger.info("Initializing embedding model")
                self.embedding_model = get_embedding_model()

            if not self.vector_store:
                self.logger.info("Initializing vector store")
                self.vector_store = VectorStore()

            if not self.rag_prompt_builder:
                self.logger.info("Initializing RAG prompt builder")
                self.rag_prompt_builder = get_rag_prompt_builder()

        except Exception as e:
            raise PipelineStageError(
                self.stage_name,
                f"Failed to initialize RAG components: {str(e)}",
                cause=e
            )

    async def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for the user query"""
        try:
            if not self.embedding_model:
                raise ValueError("Embedding model not initialized")

            # Generate embedding
            embedding = self.embedding_model.embed_query(query)

            # Validate embedding
            if not embedding or len(embedding) == 0:
                raise ValueError("Empty embedding generated")

            return embedding

        except Exception as e:
            raise PipelineStageError(
                self.stage_name,
                f"Failed to generate query embedding: {str(e)}",
                cause=e
            )

    async def _retrieve_documents(
        self,
        query_embedding: List[float],
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using similarity search"""
        try:
            # Use repository for database session management
            from backend.database.connection import get_db

            # This is a simplified approach - in a full implementation,
            # we'd inject the database session through the pipeline
            async for db in get_db():
                try:
                    # Perform similarity search
                    similar_chunks = await self.document_repo.similarity_search(
                        db=db,
                        query_embedding=query_embedding,
                        similarity_threshold=self.similarity_threshold,
                        limit=self.max_documents
                    )

                    # Filter by organization if specified
                    filtered_chunks = []
                    for chunk, similarity in similar_chunks:
                        # Add organization filtering logic here
                        # For now, we'll include all chunks
                        filtered_chunks.append({
                            "chunk_id": chunk.id,
                            "document_id": chunk.document_id,
                            "content": chunk.content,
                            "similarity_score": similarity,
                            "metadata": chunk.metadata or {}
                        })

                    # Sort by similarity score (highest first)
                    filtered_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)

                    return filtered_chunks[:self.max_documents]

                finally:
                    await db.close()

        except Exception as e:
            self.logger.error(f"Document retrieval failed: {str(e)}")
            # Return empty results rather than failing the entire pipeline
            return []

    async def _build_context_from_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        try:
            if not documents:
                return ""

            # Use RAG prompt builder if available
            if self.rag_prompt_builder:
                try:
                    context = self.rag_prompt_builder.build_context(documents)
                    if context and len(context) <= self.max_context_length:
                        return context
                except Exception as e:
                    self.logger.warning(f"RAG prompt builder failed, using fallback: {e}")

            # Fallback: simple concatenation with document boundaries
            context_parts = []
            current_length = 0

            for i, doc in enumerate(documents):
                doc_content = doc.get("content", "")
                similarity = doc.get("similarity_score", 0.0)

                # Format document with metadata
                doc_text = f"[Document {i+1}] (Relevance: {similarity:.2f})\n{doc_content}\n"

                # Check if adding this document would exceed the limit
                if current_length + len(doc_text) > self.max_context_length:
                    if i == 0:
                        # If even the first document is too long, truncate it
                        remaining_length = self.max_context_length - current_length
                        doc_text = doc_text[:remaining_length] + "...\n"
                        context_parts.append(doc_text)
                    break

                context_parts.append(doc_text)
                current_length += len(doc_text)

            return "\n".join(context_parts).strip()

        except Exception as e:
            self.logger.error(f"Context building failed: {str(e)}")
            return ""

    async def validate_retrieval_setup(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate that RAG retrieval is properly set up for an organization"""
        validation_result = {
            "is_valid": False,
            "components_status": {},
            "document_count": 0,
            "indexed_document_count": 0,
            "issues": []
        }

        try:
            # Check embedding model
            try:
                await self._initialize_rag_components()
                validation_result["components_status"]["embedding_model"] = "available"
            except Exception as e:
                validation_result["components_status"]["embedding_model"] = "failed"
                validation_result["issues"].append(f"Embedding model: {str(e)}")

            # Check vector store
            try:
                if self.vector_store:
                    validation_result["components_status"]["vector_store"] = "available"
                else:
                    validation_result["components_status"]["vector_store"] = "not_initialized"
            except Exception as e:
                validation_result["components_status"]["vector_store"] = "failed"
                validation_result["issues"].append(f"Vector store: {str(e)}")

            # Check document availability
            try:
                async for db in get_db():
                    try:
                        # Get document count for organization
                        if organization_id:
                            org_docs = await self.document_repo.get_by_organization(db, organization_id)
                            validation_result["document_count"] = len(org_docs)

                            # Count indexed documents
                            indexed_count = sum(
                                1 for doc in org_docs
                                if hasattr(doc, 'status') and doc.status.value == "indexed"
                            )
                            validation_result["indexed_document_count"] = indexed_count
                    finally:
                        await db.close()

            except Exception as e:
                validation_result["issues"].append(f"Document check: {str(e)}")

            # Determine overall validity
            has_embedding = validation_result["components_status"].get("embedding_model") == "available"
            has_vectors = validation_result["components_status"].get("vector_store") == "available"
            has_documents = validation_result["indexed_document_count"] > 0

            validation_result["is_valid"] = has_embedding and has_vectors and has_documents

            if not has_documents:
                validation_result["issues"].append(
                    f"No indexed documents available for organization {organization_id or 'default'}"
                )

            return validation_result

        except Exception as e:
            validation_result["issues"].append(f"Validation error: {str(e)}")
            return validation_result

    def configure_rag(
        self,
        similarity_threshold: Optional[float] = None,
        max_documents: Optional[int] = None,
        max_context_length: Optional[int] = None
    ) -> None:
        """
        Configure RAG retrieval parameters

        Args:
            similarity_threshold: Minimum similarity score for document inclusion
            max_documents: Maximum number of documents to retrieve
            max_context_length: Maximum length of context to build
        """
        if similarity_threshold is not None:
            self.similarity_threshold = max(0.0, min(1.0, similarity_threshold))

        if max_documents is not None:
            self.max_documents = max(1, min(20, max_documents))

        if max_context_length is not None:
            self.max_context_length = max(100, min(10000, max_context_length))

        self.logger.info(
            f"RAG configuration updated: "
            f"threshold={self.similarity_threshold}, "
            f"max_docs={self.max_documents}, "
            f"max_context={self.max_context_length}"
        )

    def get_rag_status(self) -> Dict[str, Any]:
        """Get current RAG configuration and status"""
        return {
            "similarity_threshold": self.similarity_threshold,
            "max_documents": self.max_documents,
            "max_context_length": self.max_context_length,
            "embedding_model_loaded": self.embedding_model is not None,
            "vector_store_loaded": self.vector_store is not None,
            "rag_prompt_builder_loaded": self.rag_prompt_builder is not None
        }