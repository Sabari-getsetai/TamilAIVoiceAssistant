"""LLM (Large Language Model) Pipeline Stage

This module handles AI response generation using the configured LLM,
with support for conversation history and RAG context integration.
"""

from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage

from backend.orchestration.pipelines.base_pipeline import (
    BasePipelineStage, PipelineStageType, ConversationState, PipelineStageError
)
from backend.models import get_llm, initialize_llm


class LLMStage(BasePipelineStage):
    """LLM (Large Language Model) pipeline stage"""

    def __init__(self):
        super().__init__(
            stage_type=PipelineStageType.LLM,
            stage_name="llm"
        )

        # Configure stage requirements
        self.required_inputs = ["user_text"]
        self.provided_outputs = ["assistant_text"]

        # LLM configuration
        self.max_tokens = 500
        self.temperature = 0.7
        self.max_history_turns = 10
        self.include_system_prompt = True

        # Initialize components
        self.llm = None
        self.llm_initialized = False

    async def process(self, state: ConversationState) -> ConversationState:
        """
        Process user input through LLM to generate assistant response

        Args:
            state: Current conversation state

        Returns:
            Updated state with assistant_text populated

        Raises:
            PipelineStageError: If LLM processing fails
        """
        try:
            # Initialize LLM if needed
            if not self.llm_initialized:
                await self._initialize_llm()

            # Get user input
            user_text = state["user_text"]
            if not user_text or not user_text.strip():
                raise PipelineStageError(
                    self.stage_name,
                    "Empty user text provided"
                )

            # Build conversation context
            messages = await self._build_conversation_messages(state)

            # Generate LLM response
            assistant_text = await self._generate_response(messages, state)

            # Update state with LLM response
            state["assistant_text"] = assistant_text

            # Add LLM metadata to custom context
            if "custom_context" not in state:
                state["custom_context"] = {}

            state["custom_context"]["llm_metadata"] = {
                "model_name": self._get_model_name(),
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "message_count": len(messages),
                "response_length": len(assistant_text),
                "context_used": bool(state.get("context_used")),
                "history_turns_included": len(state.get("conversation_history", []))
            }

            self.logger.info(
                f"LLM completed: Generated {len(assistant_text)} characters "
                f"from {len(messages)} messages"
            )

            return state

        except Exception as e:
            self.logger.error(f"LLM processing failed: {str(e)}")
            raise PipelineStageError(
                self.stage_name,
                f"LLM response generation failed: {str(e)}",
                cause=e
            )

    async def _initialize_llm(self) -> None:
        """Initialize LLM if needed"""
        try:
            if not self.llm_initialized:
                self.logger.info("Initializing LLM")
                if not initialize_llm():
                    raise ValueError("Failed to initialize LLM")

                self.llm = get_llm()
                if not self.llm:
                    raise ValueError("LLM not available after initialization")

                self.llm_initialized = True
                self.logger.info(f"LLM initialized: {self._get_model_name()}")

        except Exception as e:
            raise PipelineStageError(
                self.stage_name,
                f"Failed to initialize LLM: {str(e)}",
                cause=e
            )

    async def _build_conversation_messages(self, state: ConversationState) -> List:
        """Build conversation messages for LLM input"""
        try:
            messages = []

            # Add system prompt if enabled
            if self.include_system_prompt:
                system_prompt = self._build_system_prompt(state)
                if system_prompt:
                    # System message format depends on LLM implementation
                    # This is a simplified approach
                    messages.append({"role": "system", "content": system_prompt})

            # Add conversation history
            history = state.get("conversation_history", [])
            recent_history = history[-self.max_history_turns:] if history else []

            for turn in recent_history:
                if turn.get("user_text"):
                    messages.append(HumanMessage(content=turn["user_text"]))
                if turn.get("assistant_text"):
                    messages.append(AIMessage(content=turn["assistant_text"]))

            # Add current user message with RAG context if available
            current_message = self._build_current_user_message(state)
            messages.append(HumanMessage(content=current_message))

            return messages

        except Exception as e:
            raise PipelineStageError(
                self.stage_name,
                f"Failed to build conversation messages: {str(e)}",
                cause=e
            )

    def _build_system_prompt(self, state: ConversationState) -> str:
        """Build system prompt for the LLM"""
        language = state.get("language", "ta")

        # Base system prompt - could be made configurable
        base_prompt = """You are a helpful Tamil AI voice assistant. You provide accurate, helpful responses in a conversational manner."""

        # Language-specific instructions
        language_instructions = {
            "ta": "தமிழில் பதிலளித்து உதவுங்கள். தெளிவான மற்றும் உதவிகரமான பதில்களை வழங்குங்கள்.",
            "en": "Respond in English with clear and helpful answers.",
            "hi": "हिंदी में स्पष्ट और सहायक उत्तर दें।"
        }

        language_instruction = language_instructions.get(language, language_instructions["en"])

        # RAG context instruction if available
        context_instruction = ""
        if state.get("context_used"):
            context_instruction = "\n\nUse the following context from relevant documents to inform your response:\n"

        return f"{base_prompt}\n\n{language_instruction}{context_instruction}"

    def _build_current_user_message(self, state: ConversationState) -> str:
        """Build the current user message with optional RAG context"""
        user_text = state["user_text"]
        context = state.get("context_used", "")

        if context and context.strip():
            # Include RAG context in the user message
            message = f"Context from documents:\n{context}\n\nUser question: {user_text}"
        else:
            message = user_text

        return message

    async def _generate_response(self, messages: List, state: ConversationState) -> str:
        """Generate response using LLM"""
        try:
            if not self.llm:
                raise ValueError("LLM not initialized")

            # Configure generation parameters
            generation_config = {
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            # Generate response using LLM
            # The exact method depends on the LLM implementation
            if hasattr(self.llm, 'ainvoke'):
                # Async invocation
                response = await self.llm.ainvoke(messages, **generation_config)
            else:
                # Sync invocation (should be avoided in async pipeline)
                response = self.llm.invoke(messages, **generation_config)

            # Extract text content from response
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            # Validate and clean response
            if not response_text or not response_text.strip():
                return "I'm sorry, I couldn't generate a response. Please try asking again."

            return response_text.strip()

        except Exception as e:
            self.logger.error(f"LLM generation failed: {str(e)}")
            # Return fallback response instead of failing
            return "I apologize, but I'm having trouble generating a response right now. Please try again."

    def _get_model_name(self) -> str:
        """Get the name/identifier of the current LLM"""
        try:
            if self.llm and hasattr(self.llm, 'model_name'):
                return self.llm.model_name
            elif self.llm and hasattr(self.llm, '__class__'):
                return self.llm.__class__.__name__
            else:
                return "Unknown"
        except Exception:
            return "Unknown"

    def configure_llm(
        self,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        max_history_turns: Optional[int] = None,
        include_system_prompt: Optional[bool] = None
    ) -> None:
        """
        Configure LLM generation parameters

        Args:
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            max_history_turns: Maximum conversation history to include
            include_system_prompt: Whether to include system prompt
        """
        if max_tokens is not None:
            self.max_tokens = max(50, min(2000, max_tokens))

        if temperature is not None:
            self.temperature = max(0.0, min(1.0, temperature))

        if max_history_turns is not None:
            self.max_history_turns = max(0, min(50, max_history_turns))

        if include_system_prompt is not None:
            self.include_system_prompt = include_system_prompt

        self.logger.info(
            f"LLM configuration updated: "
            f"max_tokens={self.max_tokens}, "
            f"temperature={self.temperature}, "
            f"max_history={self.max_history_turns}, "
            f"system_prompt={self.include_system_prompt}"
        )

    def health_check(self) -> bool:
        """Check if LLM is healthy and available"""
        try:
            if not self.llm_initialized:
                return False

            if not self.llm:
                return False

            # Simple test generation
            test_messages = [HumanMessage(content="Hello")]

            # Try a simple synchronous call for health check
            if hasattr(self.llm, 'invoke'):
                test_response = self.llm.invoke(test_messages, max_tokens=10)
                return test_response is not None

            return True

        except Exception as e:
            self.logger.error(f"LLM health check failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current LLM"""
        try:
            return {
                "model_name": self._get_model_name(),
                "initialized": self.llm_initialized,
                "available": self.llm is not None,
                "health": self.health_check(),
                "configuration": {
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "max_history_turns": self.max_history_turns,
                    "include_system_prompt": self.include_system_prompt
                }
            }
        except Exception as e:
            return {
                "model_name": "Unknown",
                "initialized": False,
                "available": False,
                "health": False,
                "error": str(e)
            }

    async def estimate_token_usage(self, state: ConversationState) -> Dict[str, int]:
        """Estimate token usage for the current request"""
        try:
            # Build messages to estimate tokens
            messages = await self._build_conversation_messages(state)

            # Simple estimation (4 characters ≈ 1 token for English/Tamil)
            input_text = ""
            for message in messages:
                if hasattr(message, 'content'):
                    input_text += message.content + " "
                elif isinstance(message, dict) and 'content' in message:
                    input_text += message['content'] + " "

            estimated_input_tokens = len(input_text) // 4
            estimated_output_tokens = self.max_tokens

            return {
                "estimated_input_tokens": estimated_input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens
            }

        except Exception as e:
            self.logger.error(f"Token estimation failed: {str(e)}")
            return {
                "estimated_input_tokens": 0,
                "estimated_output_tokens": self.max_tokens,
                "estimated_total_tokens": self.max_tokens
            }