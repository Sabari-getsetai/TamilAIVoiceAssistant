"""
Tamil-Optimized Prompts for RAG-based Question Answering

This module provides prompt templates optimized for Tamil-LLaMA models
in a RAG (Retrieval-Augmented Generation) context.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Represents a prompt template"""
    template: str
    input_variables: List[str]

    def format(self, **kwargs) -> str:
        """
        Format the template with provided variables

        Args:
            **kwargs: Variable values to substitute

        Returns:
            Formatted prompt string
        """
        # Check for missing variables
        missing = set(self.input_variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        return self.template.format(**kwargs)


# RAG Question Answering Prompt (Tamil + English)
RAG_QA_TEMPLATE = PromptTemplate(
    template="""நீங்கள் ஒரு உதவிகரமான AI உதவியாளர். கொடுக்கப்பட்ட சூழல் தகவலைப் பயன்படுத்தி பயனரின் கேள்விக்கு பதிலளிக்கவும்.

சூழல் தகவல் (Context):
{context}

பயனர் கேள்வி (Question):
{question}

வழிகாட்டுதல்கள் (Instructions):
1. சூழல் தகவலை அடிப்படையாகக் கொண்டு துல்லியமான பதில் அளிக்கவும்
2. நீங்கள் உறுதியாக தெரியாத விஷயங்களை எழுதாதீர்கள்
3. சூழலில் பதில் இல்லை என்றால், "மன்னிக்கவும், வழங்கப்பட்ட தகவலில் இதற்கான பதில் இல்லை" என்று சொல்லவும்
4. பதில் தெளிவாகவும் சுருக்கமாகவும் இருக்க வேண்டும்

பதில் (Answer):""",
    input_variables=["context", "question"]
)


# Conversational RAG Prompt (with chat history)
CONVERSATIONAL_RAG_TEMPLATE = PromptTemplate(
    template="""நீங்கள் ஒரு உதவிகரமான தமிழ் AI உதவியாளர். முந்தைய உரையாடலையும் சூழல் தகவலையும் கருத்தில் கொண்டு பதிலளிக்கவும்.

உரையாடல் வரலாறு (Chat History):
{chat_history}

சூழல் தகவல் (Context):
{context}

தற்போதைய கேள்வி (Current Question):
{question}

வழிகாட்டுதல்கள்:
1. முந்தைய உரையாடலின் சூழலை கருத்தில் கொள்ளுங்கள்
2. வழங்கப்பட்ட சூழல் தகவலை பயன்படுத்துங்கள்
3. இயற்கையான, நட்பான முறையில் பதிலளிக்கவும்
4. தெரியாத விஷயங்களை ஒப்புக்கொள்ளவும்

பதில்:""",
    input_variables=["chat_history", "context", "question"]
)


# Simple Question Answering (without RAG context)
SIMPLE_QA_TEMPLATE = PromptTemplate(
    template="""நீங்கள் ஒரு உதவிகரமான தமிழ் AI உதவியாளர். பின்வரும் கேள்விக்கு துல்லியமாக பதிலளிக்கவும்.

கேள்வி: {question}

பதில்:""",
    input_variables=["question"]
)


# Document Summarization Prompt
SUMMARIZATION_TEMPLATE = PromptTemplate(
    template="""பின்வரும் உள்ளடக்கத்தை தமிழில் சுருக்கமாக விவரிக்கவும்.

உள்ளடக்கம்:
{content}

வழிகாட்டுதல்கள்:
1. முக்கிய புள்ளிகளை எடுத்துக்காட்டவும்
2. 2-3 பத்திகளில் சுருக்கவும்
3. எளிய தமிழில் எழுதவும்

சுருக்கம்:""",
    input_variables=["content"]
)


# Tamil Language Instruction Prompt
TAMIL_INSTRUCTION_TEMPLATE = PromptTemplate(
    template="""நீங்கள் ஒரு தமிழ் மொழி நிபுணர். பின்வரும் பணியை முடிக்கவும்.

பணி: {instruction}

{additional_context}

பதில்:""",
    input_variables=["instruction", "additional_context"]
)


# English to Tamil Response Prompt
EN_TO_TA_RESPONSE_TEMPLATE = PromptTemplate(
    template="""You are a helpful AI assistant that can understand both English and Tamil.
Please respond to the following question in Tamil.

Context Information:
{context}

Question: {question}

Please provide your answer in Tamil language.

Answer:""",
    input_variables=["context", "question"]
)


# Code-Mixed (Tamil + English) RAG Prompt
CODE_MIXED_RAG_TEMPLATE = PromptTemplate(
    template="""நீங்கள் ஒரு multilingual AI assistant. You can understand both Tamil and English.

Context:
{context}

Question: {question}

Instructions:
- Respond in the same language as the question
- தமிழ் கேள்வி என்றால் தமிழில் பதில்
- English question means English answer
- Mixed language is also fine
- Use the context to provide accurate answer

Answer:""",
    input_variables=["context", "question"]
)


class PromptBuilder:
    """
    Helper class to build and manage prompts
    """

    def __init__(self, template: PromptTemplate):
        """
        Initialize prompt builder

        Args:
            template: PromptTemplate to use
        """
        self.template = template

    def build(self, **kwargs) -> str:
        """
        Build prompt from template

        Args:
            **kwargs: Variable values

        Returns:
            Formatted prompt string
        """
        return self.template.format(**kwargs)

    def build_with_context(
        self,
        question: str,
        context_documents: List[str],
        chat_history: Optional[List[Dict]] = None,
    ) -> str:
        """
        Build RAG prompt with retrieved context

        Args:
            question: User's question
            context_documents: List of retrieved document texts
            chat_history: Optional chat history for conversational RAG

        Returns:
            Formatted prompt string
        """
        # Format context
        context = self._format_context(context_documents)

        # Choose template based on whether we have chat history
        if chat_history:
            formatted_history = self._format_chat_history(chat_history)
            return self.template.format(
                question=question,
                context=context,
                chat_history=formatted_history
            )
        else:
            return self.template.format(
                question=question,
                context=context
            )

    def _format_context(self, documents: List[str]) -> str:
        """
        Format retrieved documents into context string

        Args:
            documents: List of document texts

        Returns:
            Formatted context string
        """
        if not documents:
            return "தகவல் இல்லை (No information available)"

        # Number and format each document
        formatted_docs = []
        for i, doc in enumerate(documents, 1):
            formatted_docs.append(f"[{i}] {doc}")

        return "\n\n".join(formatted_docs)

    def _format_chat_history(self, history: List[Dict]) -> str:
        """
        Format chat history for prompt

        Args:
            history: List of chat messages [{"role": "user/assistant", "content": "..."}]

        Returns:
            Formatted history string
        """
        if not history:
            return "இல்லை (None)"

        formatted = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                formatted.append(f"பயனர்: {content}")
            else:
                formatted.append(f"உதவியாளர்: {content}")

        return "\n".join(formatted)


# Convenience functions
def get_rag_prompt_builder() -> PromptBuilder:
    """Get RAG QA prompt builder"""
    return PromptBuilder(RAG_QA_TEMPLATE)


def get_conversational_rag_builder() -> PromptBuilder:
    """Get conversational RAG prompt builder"""
    return PromptBuilder(CONVERSATIONAL_RAG_TEMPLATE)


def get_code_mixed_builder() -> PromptBuilder:
    """Get code-mixed (Tamil + English) prompt builder"""
    return PromptBuilder(CODE_MIXED_RAG_TEMPLATE)


if __name__ == "__main__":
    # Test prompts
    print("="*60)
    print("🧪 Testing Tamil Prompts")
    print("="*60)

    # Test 1: Simple RAG prompt
    print("\n" + "="*60)
    print("🧪 Test 1: RAG QA Prompt")
    print("="*60)

    builder = get_rag_prompt_builder()
    context_docs = [
        "செயற்கை நுண்ணறிவு என்பது கணினிகள் மூலம் மனித நுண்ணறிவை உருவகப்படுத்துவது.",
        "இயந்திரக் கற்றல் என்பது AI-ன் ஒரு பிரிவு.",
    ]

    prompt = builder.build_with_context(
        question="செயற்கை நுண்ணறிவு என்றால் என்ன?",
        context_documents=context_docs
    )

    print(prompt)

    # Test 2: Conversational RAG prompt
    print("\n" + "="*60)
    print("🧪 Test 2: Conversational RAG Prompt")
    print("="*60)

    conv_builder = get_conversational_rag_builder()
    chat_history = [
        {"role": "user", "content": "AI பற்றி சொல்லுங்கள்"},
        {"role": "assistant", "content": "AI என்பது செயற்கை நுண்ணறிவு."},
    ]

    prompt = conv_builder.build_with_context(
        question="இது எப்படி வேலை செய்கிறது?",
        context_documents=context_docs,
        chat_history=chat_history
    )

    print(prompt)

    # Test 3: Code-mixed prompt
    print("\n" + "="*60)
    print("🧪 Test 3: Code-Mixed Prompt")
    print("="*60)

    mixed_builder = get_code_mixed_builder()
    prompt = mixed_builder.build_with_context(
        question="What is AI in Tamil context?",
        context_documents=[
            "AI applications in Tamil: மொழி மொழிபெயர்ப்பு, speech recognition, etc."
        ]
    )

    print(prompt)

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
