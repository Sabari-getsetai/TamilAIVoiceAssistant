"""
Text Chunking Strategies for Tamil AI Voice Assistant

This module provides text chunking strategies optimized for Tamil and
multilingual documents. Chunks are created with configurable size and
overlap for optimal RAG retrieval.
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.settings import settings


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    text: str
    start_index: int
    end_index: int
    chunk_id: int
    metadata: Dict[str, any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TextChunker:
    """
    Handles text chunking with configurable strategies

    Supports:
    - Character-based chunking
    - Sentence-aware chunking
    - Paragraph-aware chunking
    - Tamil and English text
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy: str = "sentence",
    ):
        """
        Initialize the text chunker

        Args:
            chunk_size: Target size for each chunk (default from settings)
            chunk_overlap: Number of characters to overlap between chunks (default from settings)
            strategy: Chunking strategy - "character", "sentence", or "paragraph"
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.strategy = strategy

        # Validate overlap
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Chunk text using the configured strategy

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to all chunks

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        if self.strategy == "character":
            return self._chunk_by_characters(text, metadata)
        elif self.strategy == "sentence":
            return self._chunk_by_sentences(text, metadata)
        elif self.strategy == "paragraph":
            return self._chunk_by_paragraphs(text, metadata)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")

    def _chunk_by_characters(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Simple character-based chunking with overlap

        Args:
            text: Text to chunk
            metadata: Optional metadata

        Returns:
            List of Chunk objects
        """
        chunks = []
        text_length = len(text)
        start = 0
        chunk_id = 0

        while start < text_length:
            # Calculate end position
            end = min(start + self.chunk_size, text_length)

            # Extract chunk
            chunk_text = text[start:end].strip()

            if chunk_text:  # Only add non-empty chunks
                chunks.append(Chunk(
                    text=chunk_text,
                    start_index=start,
                    end_index=end,
                    chunk_id=chunk_id,
                    metadata=metadata.copy() if metadata else {}
                ))
                chunk_id += 1

            # Move start position (accounting for overlap)
            start = end - self.chunk_overlap

            # Prevent infinite loop if overlap >= chunk_size
            if start <= chunks[-1].start_index if chunks else -1:
                start = end

        return chunks

    def _chunk_by_sentences(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Sentence-aware chunking that tries to keep sentences intact

        Args:
            text: Text to chunk
            metadata: Optional metadata

        Returns:
            List of Chunk objects
        """
        # Split into sentences (works for both Tamil and English)
        sentences = self._split_sentences(text)

        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        start_index = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If adding this sentence exceeds chunk_size and we have content
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_chunk).strip()
                end_index = start_index + len(chunk_text)

                chunks.append(Chunk(
                    text=chunk_text,
                    start_index=start_index,
                    end_index=end_index,
                    chunk_id=chunk_id,
                    metadata=metadata.copy() if metadata else {}
                ))
                chunk_id += 1

                # Handle overlap - keep last few sentences for context
                if self.chunk_overlap > 0:
                    overlap_text = []
                    overlap_length = 0
                    for s in reversed(current_chunk):
                        if overlap_length + len(s) <= self.chunk_overlap:
                            overlap_text.insert(0, s)
                            overlap_length += len(s)
                        else:
                            break
                    current_chunk = overlap_text
                    current_length = overlap_length
                    start_index = end_index - current_length
                else:
                    current_chunk = []
                    current_length = 0
                    start_index = end_index

            # Add current sentence
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space

        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk).strip()
            end_index = start_index + len(chunk_text)

            chunks.append(Chunk(
                text=chunk_text,
                start_index=start_index,
                end_index=end_index,
                chunk_id=chunk_id,
                metadata=metadata.copy() if metadata else {}
            ))

        return chunks

    def _chunk_by_paragraphs(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Paragraph-aware chunking that tries to keep paragraphs intact

        Args:
            text: Text to chunk
            metadata: Optional metadata

        Returns:
            List of Chunk objects
        """
        # Split into paragraphs (double newline or more)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        start_index = 0

        for paragraph in paragraphs:
            paragraph_length = len(paragraph)

            # If paragraph alone exceeds chunk_size, split it by sentences
            if paragraph_length > self.chunk_size:
                # First, add accumulated paragraphs if any
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk).strip()
                    end_index = start_index + len(chunk_text)

                    chunks.append(Chunk(
                        text=chunk_text,
                        start_index=start_index,
                        end_index=end_index,
                        chunk_id=chunk_id,
                        metadata=metadata.copy() if metadata else {}
                    ))
                    chunk_id += 1
                    current_chunk = []
                    current_length = 0
                    start_index = end_index

                # Split large paragraph by sentences
                para_chunks = self._chunk_by_sentences(paragraph, metadata)
                for pc in para_chunks:
                    pc.chunk_id = chunk_id
                    chunks.append(pc)
                    chunk_id += 1

                start_index = chunks[-1].end_index if chunks else 0

            # If adding this paragraph exceeds chunk_size
            elif current_length + paragraph_length > self.chunk_size and current_chunk:
                # Create chunk from accumulated paragraphs
                chunk_text = "\n\n".join(current_chunk).strip()
                end_index = start_index + len(chunk_text)

                chunks.append(Chunk(
                    text=chunk_text,
                    start_index=start_index,
                    end_index=end_index,
                    chunk_id=chunk_id,
                    metadata=metadata.copy() if metadata else {}
                ))
                chunk_id += 1

                # Handle overlap
                if self.chunk_overlap > 0 and current_chunk:
                    # Keep last paragraph for overlap
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[0])
                    start_index = end_index - current_length
                else:
                    current_chunk = []
                    current_length = 0
                    start_index = end_index

                # Add current paragraph
                current_chunk.append(paragraph)
                current_length += paragraph_length + 2  # +2 for \n\n
            else:
                # Add paragraph to current chunk
                current_chunk.append(paragraph)
                current_length += paragraph_length + 2

        # Add remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk).strip()
            end_index = start_index + len(chunk_text)

            chunks.append(Chunk(
                text=chunk_text,
                start_index=start_index,
                end_index=end_index,
                chunk_id=chunk_id,
                metadata=metadata.copy() if metadata else {}
            ))

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences (works for Tamil and English)

        Tamil sentence endings: । (purna viraam), . (period)
        English sentence endings: . ! ?

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Pattern for sentence boundaries (Tamil and English)
        # Matches: period, exclamation, question mark, Tamil purna viraam
        # Followed by space and capital letter or Tamil letter
        pattern = r'(?<=[.!?।])\s+(?=[A-ZА-Я\u0B80-\u0BFF])'

        sentences = re.split(pattern, text)

        # If no clear sentences found, try splitting by just periods
        if len(sentences) == 1:
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            sentences = [s + '.' if not s.endswith(('.', '!', '?', '।')) else s for s in sentences]

        return [s.strip() for s in sentences if s.strip()]

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks (compatibility method for document service)
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks as strings
        """
        chunks = self.chunk_text(text)
        return [chunk.text for chunk in chunks]


def get_text_chunker(chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None, strategy: str = "sentence"):
    """
    Factory function to get text chunker instance
    
    Args:
        chunk_size: Target size for each chunk (default from settings)
        chunk_overlap: Number of characters to overlap between chunks (default from settings)
        strategy: Chunking strategy - "character", "sentence", or "paragraph"
        
    Returns:
        Configured TextChunker instance
    """
    return TextChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=strategy
    )


if __name__ == "__main__":
    # Test chunking strategies
    print("="*60)
    print("🧪 Testing Text Chunking")
    print("="*60)

    # Sample Tamil text
    tamil_text = """
வணக்கம். நான் ஒரு செயற்கை நுண்ணறிவு உதவியாளர். இது முதல் பத்தி.

தமிழ் மொழி உலகின் பழமையான மொழிகளில் ஒன்று. இது திராவிட மொழிக் குடும்பத்தைச் சேர்ந்தது. தமிழ் இலக்கியம் மிகவும் வளமானது.

செயற்கை நுண்ணறிவு தொழில்நுட்பம் வேகமாக வளர்ந்து வருகிறது. இது பல துறைகளில் புரட்சியை ஏற்படுத்தி வருகிறது. எதிர்காலத்தில் மேலும் பல மாற்றங்களை நாம் காணலாம்.
    """.strip()

    # Test 1: Character-based chunking
    print("\n" + "="*60)
    print("🧪 Test 1: Character-based Chunking")
    print("="*60)

    chunker = TextChunker(chunk_size=100, chunk_overlap=20, strategy="character")
    chunks = chunker.chunk_text(tamil_text, metadata={"source": "test.txt"})

    print(f"\nCreated {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        print(f"\nChunk {i}:")
        print(f"  Text: {chunk.text[:50]}...")
        print(f"  Length: {len(chunk.text)}")
        print(f"  Position: {chunk.start_index}-{chunk.end_index}")

    # Test 2: Sentence-based chunking
    print("\n" + "="*60)
    print("🧪 Test 2: Sentence-based Chunking")
    print("="*60)

    chunker = TextChunker(chunk_size=150, chunk_overlap=30, strategy="sentence")
    chunks = chunker.chunk_text(tamil_text, metadata={"source": "test.txt"})

    print(f"\nCreated {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"  Text: {chunk.text}")
        print(f"  Length: {len(chunk.text)}")

    # Test 3: Paragraph-based chunking
    print("\n" + "="*60)
    print("🧪 Test 3: Paragraph-based Chunking")
    print("="*60)

    chunker = TextChunker(chunk_size=200, chunk_overlap=50, strategy="paragraph")
    chunks = chunker.chunk_text(tamil_text, metadata={"source": "test.txt"})

    print(f"\nCreated {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"  Paragraphs: {chunk.text.count(chr(10) + chr(10)) + 1}")
        print(f"  Length: {len(chunk.text)}")
        print(f"  Preview: {chunk.text[:80]}...")

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
