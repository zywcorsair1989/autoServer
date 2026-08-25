"""文档分块的文本分割工具。

此模块提供文本分割功能，用于将文档分割成较小的块以便进行嵌入和检索。
"""

import re
from typing import List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """表示带有元数据的文本块。"""

    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Optional[dict] = None


class TextSplitter:
    """Text splitter for breaking text into chunks.

    Supports multiple splitting strategies:
    - Character-based splitting
    - Sentence-based splitting
    - Paragraph-based splitting
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n"
    ):
        """Initialize the text splitter.

        Args:
            chunk_size: Target size for each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
            separator: Primary separator for splitting text.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split_text(self, text: str) -> List[TextChunk]:
        """Split text into chunks.

        Args:
            text: Text to split.

        Returns:
            List of TextChunk objects.
        """
        if not text or not text.strip():
            return []

        # Split by separator
        splits = self._split_by_separator(text)

        # Merge splits into chunks
        chunks = self._merge_splits_to_chunks(splits)

        logger.debug(
            f"Split text into {len(chunks)} chunks "
            f"(chunk_size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return chunks

    def _split_by_separator(self, text: str) -> List[str]:
        """Split text by separator, preserving separator.

        Args:
            text: Text to split.

        Returns:
            List of text segments.
        """
        if self.separator not in text:
            # Try splitting by sentence if separator not found
            return self._split_by_sentence(text)

        splits = text.split(self.separator)
        # Re-add separator to maintain context
        result = []
        for i, split in enumerate(splits):
            if split.strip():
                if i < len(splits) - 1:
                    result.append(split + self.separator)
                else:
                    result.append(split)

        return result

    def _split_by_sentence(self, text: str) -> List[str]:
        """Split text by sentences.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        # Simple sentence splitting pattern
        sentence_pattern = r'(?<=[.!?。！？])\s+'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _merge_splits_to_chunks(self, splits: List[str]) -> List[TextChunk]:
        """Merge splits into chunks of target size.

        Args:
            splits: List of text segments.

        Returns:
            List of TextChunk objects.
        """
        chunks = []
        current_chunk = []
        current_length = 0
        current_start = 0
        char_position = 0

        for split in splits:
            split_length = len(split)

            # If single split is larger than chunk_size, need to split further
            if split_length > self.chunk_size:
                # First, add current chunk if not empty
                if current_chunk:
                    chunk_text = "".join(current_chunk)
                    chunks.append(TextChunk(
                        content=chunk_text,
                        index=len(chunks),
                        start_char=current_start,
                        end_char=char_position
                    ))
                    current_chunk = []
                    current_length = 0
                    current_start = char_position

                # Split the large segment
                sub_chunks = self._split_large_text(split, char_position)
                chunks.extend(sub_chunks)
                char_position += split_length
                current_start = char_position
                continue

            # Check if adding this split would exceed chunk size
            if current_length + split_length > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_text = "".join(current_chunk)
                    chunks.append(TextChunk(
                        content=chunk_text,
                        index=len(chunks),
                        start_char=current_start,
                        end_char=char_position
                    ))

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    # Get overlap from end of current chunk
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = [overlap_text, split] if overlap_text else [split]
                    current_length = len(overlap_text) + split_length if overlap_text else split_length
                else:
                    current_chunk = [split]
                    current_length = split_length

                current_start = char_position
            else:
                current_chunk.append(split)
                current_length += split_length

            char_position += split_length

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = "".join(current_chunk)
            chunks.append(TextChunk(
                content=chunk_text,
                index=len(chunks),
                start_char=current_start,
                end_char=char_position
            ))

        # Update indices after all chunks are created
        for i, chunk in enumerate(chunks):
            chunk.index = i

        return chunks

    def _split_large_text(self, text: str, start_position: int) -> List[TextChunk]:
        """Split a large text segment into smaller chunks.

        Args:
            text: Text to split.
            start_position: Starting character position.

        Returns:
            List of TextChunk objects.
        """
        chunks = []
        position = 0

        while position < len(text):
            end_position = min(position + self.chunk_size, len(text))
            chunk_content = text[position:end_position]

            # Try to break at word boundary
            if end_position < len(text):
                last_space = chunk_content.rfind(' ')
                if last_space > self.chunk_size // 2:
                    end_position = position + last_space + 1
                    chunk_content = text[position:end_position]

            chunks.append(TextChunk(
                content=chunk_content,
                index=len(chunks),
                start_char=start_position + position,
                end_char=start_position + end_position
            ))
            position = end_position

        return chunks

    def _get_overlap_text(self, current_chunk: List[str]) -> Optional[str]:
        """Get overlap text from the end of current chunk.

        Args:
            current_chunk: List of text segments in current chunk.

        Returns:
            Overlap text string or None if no overlap.
        """
        chunk_text = "".join(current_chunk)
        if len(chunk_text) < self.chunk_overlap:
            return chunk_text

        # Get last chunk_overlap characters
        overlap = chunk_text[-self.chunk_overlap:]

        # Try to start at word boundary
        first_space = overlap.find(' ')
        if first_space != -1 and first_space < len(overlap) // 2:
            overlap = overlap[first_space + 1:]

        return overlap


class SentenceTextSplitter(TextSplitter):
    """Text splitter that splits by sentences."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """Initialize sentence text splitter.

        Args:
            chunk_size: Target size for each chunk.
            chunk_overlap: Overlap between chunks.
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.separator = "."  # Override separator to period


class ParagraphTextSplitter(TextSplitter):
    """Text splitter that splits by paragraphs."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """Initialize paragraph text splitter.

        Args:
            chunk_size: Target size for each chunk.
            chunk_overlap: Overlap between chunks.
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.separator = "\n\n"  # Override separator to double newline


def split_text_to_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """Convenience function to split text into chunk strings.

    Args:
        text: Text to split.
        chunk_size: Target size for each chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        List of chunk strings.
    """
    splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text)
    return [chunk.content for chunk in chunks]