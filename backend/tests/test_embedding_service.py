"""Tests for Embedding Service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.ai.embedding_service import EmbeddingService


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    with patch("app.ai.embedding_service.AsyncOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def embedding_service(mock_openai_client):
    """Create Embedding Service instance with mocked client"""
    return EmbeddingService()


class TestEmbeddingService:
    """Test suite for Embedding Service"""

    def test_embedding_service_initialization(self, mock_openai_client):
        """Test Embedding Service initializes correctly"""
        service = EmbeddingService()

        assert service.model == "text-embedding-v2"
        assert service.dimension == 1536
        assert service.client is not None

    @pytest.mark.asyncio
    async def test_embed_text(self, embedding_service, mock_openai_client):
        """Test single text embedding"""
        # Mock response
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_data = MagicMock()
        mock_data.embedding = mock_embedding
        mock_data.index = 0

        mock_response = MagicMock()
        mock_response.data = [mock_data]

        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        text = "Hello, world!"
        result = await embedding_service.embed_text(text)

        assert result == mock_embedding
        mock_openai_client.embeddings.create.assert_called_once_with(
            model="text-embedding-v2", input=text
        )

    @pytest.mark.asyncio
    async def test_embed_batch(self, embedding_service, mock_openai_client):
        """Test batch embedding"""
        # Mock response
        mock_embedding1 = [0.1, 0.2, 0.3]
        mock_embedding2 = [0.4, 0.5, 0.6]
        mock_embedding3 = [0.7, 0.8, 0.9]

        mock_data1 = MagicMock()
        mock_data1.embedding = mock_embedding1
        mock_data1.index = 0

        mock_data2 = MagicMock()
        mock_data2.embedding = mock_embedding2
        mock_data2.index = 1

        mock_data3 = MagicMock()
        mock_data3.embedding = mock_embedding3
        mock_data3.index = 2

        mock_response = MagicMock()
        mock_response.data = [mock_data1, mock_data2, mock_data3]

        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        texts = ["Text 1", "Text 2", "Text 3"]
        result = await embedding_service.embed_batch(texts)

        assert len(result) == 3
        assert result[0] == mock_embedding1
        assert result[1] == mock_embedding2
        assert result[2] == mock_embedding3

        mock_openai_client.embeddings.create.assert_called_once_with(
            model="text-embedding-v2", input=texts
        )

    @pytest.mark.asyncio
    async def test_embed_batch_order_preserved(
        self, embedding_service, mock_openai_client
    ):
        """Test that batch embedding preserves order even if API returns out of order"""
        # Mock response with out-of-order indices
        mock_embedding1 = [0.1, 0.2, 0.3]
        mock_embedding2 = [0.4, 0.5, 0.6]

        mock_data2 = MagicMock()
        mock_data2.embedding = mock_embedding2
        mock_data2.index = 1

        mock_data1 = MagicMock()
        mock_data1.embedding = mock_embedding1
        mock_data1.index = 0

        mock_response = MagicMock()
        mock_response.data = [mock_data2, mock_data1]  # Out of order

        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        texts = ["Text 1", "Text 2"]
        result = await embedding_service.embed_batch(texts)

        # Order should be preserved
        assert result[0] == mock_embedding1
        assert result[1] == mock_embedding2

    @pytest.mark.asyncio
    async def test_embed_text_api_error(self, embedding_service, mock_openai_client):
        """Test API error handling for single text"""
        mock_openai_client.embeddings.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        text = "Hello"

        with pytest.raises(Exception, match="API Error"):
            await embedding_service.embed_text(text)

    @pytest.mark.asyncio
    async def test_embed_batch_api_error(self, embedding_service, mock_openai_client):
        """Test API error handling for batch embedding"""
        mock_openai_client.embeddings.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        texts = ["Text 1", "Text 2"]

        with pytest.raises(Exception, match="API Error"):
            await embedding_service.embed_batch(texts)

    @pytest.mark.asyncio
    async def test_embed_single_text_with_special_characters(
        self, embedding_service, mock_openai_client
    ):
        """Test embedding text with special characters"""
        mock_embedding = [0.1, 0.2, 0.3]
        mock_data = MagicMock()
        mock_data.embedding = mock_embedding
        mock_data.index = 0

        mock_response = MagicMock()
        mock_response.data = [mock_data]

        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        text = "Hello! How are you? I'm fine, thanks. 😊"
        result = await embedding_service.embed_text(text)

        assert result == mock_embedding
        mock_openai_client.embeddings.create.assert_called_once()