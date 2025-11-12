"""
Prompt service for RAG pipeline.

Manages prompt templates and context formatting for LLM queries.
"""

import logging
from typing import List, Dict, Any

from app.core.config import settings
from app.services.base import Message

logger = logging.getLogger(__name__)


class PromptService:
    """Service for creating and formatting prompts."""

    def __init__(self):
        """Initialize prompt service."""
        self.system_prompt = self._get_system_prompt()
        logger.info("Initialized PromptService")

    def _get_system_prompt(self) -> str:
        """
        Get system prompt for financial RAG assistant.

        Returns:
            System prompt text
        """
        return """You are an AI assistant specialized in analyzing financial documents and reports. Your role is to:

1. Answer questions based ONLY on the provided context from financial documents
2. Provide accurate, detailed, and well-structured answers
3. Always cite your sources using the format: [Source: filename, Page X]
4. If the context doesn't contain enough information to answer the question, clearly state that
5. For numerical data, be precise and include units where applicable
6. When comparing data, clearly state the time periods or categories being compared
7. Maintain a professional, analytical tone

Important guidelines:
- Do NOT make up information or use knowledge outside the provided context
- Do NOT provide financial advice or recommendations
- If asked about future predictions or opinions, decline politely
- If the question is ambiguous, ask for clarification
- Always double-check numbers and calculations

Your answers should be:
- Accurate: Based strictly on the provided context
- Complete: Address all parts of the question
- Clear: Use simple language when possible
- Cited: Include source references for all claims
"""

    def create_rag_prompt(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> List[Message]:
        """
        Create prompt messages for RAG query.

        Args:
            question: User's question
            retrieved_chunks: Retrieved document chunks with metadata

        Returns:
            List of messages for LLM
        """
        # Format context from retrieved chunks
        context = self._format_context(retrieved_chunks)

        # Build user message
        user_message = f"""Context from financial documents:

{context}

---

Question: {question}

Please provide a detailed answer based on the context above. Include citations to specific documents and page numbers where applicable."""

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_message),
        ]

        logger.debug(f"Created RAG prompt with {len(retrieved_chunks)} context chunks")

        return messages

    def _format_context(
        self,
        chunks: List[Dict[str, Any]],
        max_length: Optional[int] = None,
    ) -> str:
        """
        Format retrieved chunks into context string.

        Args:
            chunks: Retrieved chunks
            max_length: Maximum context length in characters

        Returns:
            Formatted context string
        """
        max_length = max_length or settings.MAX_CONTEXT_LENGTH

        context_parts = []
        current_length = 0

        for i, chunk in enumerate(chunks, 1):
            # Extract metadata
            metadata = chunk.get('metadata', {})
            content = chunk.get('content', '')
            score = chunk.get('score', 0)

            # Format source citation
            filename = metadata.get('filename', 'Unknown')
            page_num = metadata.get('page_number', metadata.get('num_pages', 'N/A'))

            # Build context entry
            context_entry = f"""[Source {i}] {filename}, Page {page_num} (Relevance: {score:.2f})
{content}
"""

            # Check if adding this would exceed max length
            entry_length = len(context_entry)
            if max_length and (current_length + entry_length) > max_length:
                logger.warning(
                    f"Context truncated at {current_length} characters "
                    f"(max: {max_length})"
                )
                break

            context_parts.append(context_entry)
            current_length += entry_length

        context = "\n---\n".join(context_parts)

        logger.debug(
            f"Formatted context: {len(context_parts)} chunks, "
            f"{current_length} characters"
        )

        return context

    def create_summarization_prompt(
        self,
        text: str,
        max_length: Optional[int] = None,
    ) -> List[Message]:
        """
        Create prompt for text summarization.

        Args:
            text: Text to summarize
            max_length: Maximum summary length

        Returns:
            List of messages for LLM
        """
        max_length_instruction = f" Keep the summary under {max_length} words." if max_length else ""

        user_message = f"""Please provide a concise summary of the following financial document or section.{max_length_instruction}

Document text:
{text}

Summary:"""

        return [
            Message(
                role="system",
                content="You are an AI assistant that creates clear, concise summaries of financial documents."
            ),
            Message(role="user", content=user_message),
        ]

    def create_comparison_prompt(
        self,
        query: str,
        chunks_a: List[Dict[str, Any]],
        chunks_b: List[Dict[str, Any]],
        label_a: str = "Document A",
        label_b: str = "Document B",
    ) -> List[Message]:
        """
        Create prompt for comparing information from different documents.

        Args:
            query: Comparison question
            chunks_a: Chunks from first document/source
            chunks_b: Chunks from second document/source
            label_a: Label for first source
            label_b: Label for second source

        Returns:
            List of messages for LLM
        """
        context_a = self._format_context(chunks_a)
        context_b = self._format_context(chunks_b)

        user_message = f"""Compare the following information from two sources:

{label_a}:
{context_a}

---

{label_b}:
{context_b}

---

Question: {query}

Please provide a detailed comparison addressing the question above. Clearly indicate which information comes from which source."""

        return [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_message),
        ]

    def create_extraction_prompt(
        self,
        text: str,
        fields: List[str],
    ) -> List[Message]:
        """
        Create prompt for extracting structured information.

        Args:
            text: Text to extract from
            fields: List of fields to extract

        Returns:
            List of messages for LLM
        """
        fields_list = "\n".join(f"- {field}" for field in fields)

        user_message = f"""Extract the following information from the financial document:

{fields_list}

Document text:
{text}

Please provide the extracted information in a clear, structured format. If a field is not found in the document, indicate "Not found"."""

        return [
            Message(
                role="system",
                content="You are an AI assistant that extracts structured information from financial documents."
            ),
            Message(role="user", content=user_message),
        ]

    def format_sources(
        self,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """
        Format source citations from chunks.

        Args:
            chunks: Retrieved chunks

        Returns:
            List of source citations
        """
        sources = []

        for chunk in chunks:
            metadata = chunk.get('metadata', {})

            source = {
                'filename': metadata.get('filename', 'Unknown'),
                'page': str(metadata.get('page_number', metadata.get('num_pages', 'N/A'))),
                'score': f"{chunk.get('score', 0):.2f}",
                'preview': chunk.get('content', '')[:200] + '...',
            }

            sources.append(source)

        return sources

    def truncate_context_to_token_limit(
        self,
        context: str,
        max_tokens: int,
        chars_per_token: float = 4.0,
    ) -> str:
        """
        Truncate context to fit within token limit.

        Args:
            context: Context string
            max_tokens: Maximum tokens
            chars_per_token: Approximate characters per token

        Returns:
            Truncated context
        """
        max_chars = int(max_tokens * chars_per_token)

        if len(context) <= max_chars:
            return context

        logger.warning(
            f"Context truncated from {len(context)} to {max_chars} characters"
        )

        # Truncate and add indicator
        return context[:max_chars] + "\n\n[Context truncated...]"
