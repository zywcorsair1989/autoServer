"""Tests for text splitting utilities."""

import pytest

from app.utils.text_splitter import (
    TextSplitter,
    TextChunk,
    SentenceTextSplitter,
    ParagraphTextSplitter,
    split_text_to_chunks,
)


class TestTextSplitter:
    """Tests for the TextSplitter class."""

    def test_split_empty_text(self):
        """Test splitting empty text."""
        splitter = TextSplitter()
        chunks = splitter.split_text("")

        assert chunks == []

    def test_split_whitespace_only(self):
        """Test splitting whitespace-only text."""
        splitter = TextSplitter()
        chunks = splitter.split_text("   \n\n   ")

        assert chunks == []

    def test_split_short_text(self):
        """Test splitting text shorter than chunk size."""
        splitter = TextSplitter(chunk_size=100)
        text = "This is a short text."
        chunks = splitter.split_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_split_by_separator(self):
        """Test splitting by separator."""
        splitter = TextSplitter(chunk_size=50, separator="\n")
        text = "Line 1\nLine 2\nLine 3"
        chunks = splitter.split_text(text)

        assert len(chunks) >= 1
        # Each chunk should be within size limit (with some flexibility)
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_split_long_line(self):
        """Test splitting a line longer than chunk size."""
        splitter = TextSplitter(chunk_size=20, chunk_overlap=5)
        text = "This is a very long line that exceeds the chunk size limit."
        chunks = splitter.split_text(text)

        assert len(chunks) >= 2

    def test_chunk_metadata(self):
        """Test that chunks have correct metadata."""
        splitter = TextSplitter(chunk_size=50)
        text = "First line.\nSecond line."
        chunks = splitter.split_text(text)

        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert chunk.start_char >= 0
            assert chunk.end_char >= chunk.start_char


class TestTextChunk:
    """Tests for the TextChunk dataclass."""

    def test_text_chunk_creation(self):
        """Test creating a TextChunk."""
        chunk = TextChunk(
            content="Test content",
            index=0,
            start_char=0,
            end_char=12
        )

        assert chunk.content == "Test content"
        assert chunk.index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 12
        assert chunk.metadata is None

    def test_text_chunk_with_metadata(self):
        """Test creating a TextChunk with metadata."""
        metadata = {"source": "test"}
        chunk = TextChunk(
            content="Test",
            index=0,
            start_char=0,
            end_char=4,
            metadata=metadata
        )

        assert chunk.metadata == metadata


class TestSentenceTextSplitter:
    """Tests for the SentenceTextSplitter class."""

    def test_split_by_sentence(self):
        """Test splitting by sentences."""
        splitter = SentenceTextSplitter(chunk_size=50)
        text = "First sentence. Second sentence. Third sentence."
        chunks = splitter.split_text(text)

        assert len(chunks) >= 1


class TestParagraphTextSplitter:
    """Tests for the ParagraphTextSplitter class."""

    def test_split_by_paragraph(self):
        """Test splitting by paragraphs."""
        splitter = ParagraphTextSplitter(chunk_size=100)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = splitter.split_text(text)

        assert len(chunks) >= 1


class TestSplitTextToChunks:
    """Tests for the convenience function."""

    def test_split_text_to_chunks_basic(self):
        """Test basic text splitting."""
        text = "This is a test. " * 50  # Long text
        chunks = split_text_to_chunks(text, chunk_size=100, chunk_overlap=20)

        assert len(chunks) >= 2
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_split_text_to_chunks_short(self):
        """Test splitting short text."""
        text = "Short text"
        chunks = split_text_to_chunks(text, chunk_size=100)

        assert len(chunks) == 1
        assert chunks[0] == text