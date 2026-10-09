"""Tests for Embedding Service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.ai.embedding_service import EmbeddingService
from app.core.config import settings


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

        # 模型名与维度均取决于 .env / config，不写死具体值
        assert service.model == settings.BAILIAN_EMBEDDING_MODEL
        assert service.dimension == settings.EMBEDDING_DIMENSION
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
            model=settings.BAILIAN_EMBEDDING_MODEL, input=text
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
            model=settings.BAILIAN_EMBEDDING_MODEL, input=texts
        )

    @pytest.mark.asyncio
    async def test_embed_batch_order_preserved(
        self, embedding_service, mock_openai_client
    ):
        """批量返回应按返回顺序对齐，而非 item.index。

        百炼部分模型（如 qwen3.7-text-embedding-flash）批量返回的
        item.index 全为 0，按 index 回填会导致向量错位，此测试固化
        “按返回顺序对齐”的正确行为（OpenAI 兼容协议保证顺序与输入一致）。
        """
        mock_embedding1 = [0.1, 0.2, 0.3]
        mock_embedding2 = [0.4, 0.5, 0.6]

        # 模拟真实百炼行为：返回顺序与输入一致，但 index 不可靠（全为 0）
        mock_data1 = MagicMock()
        mock_data1.embedding = mock_embedding1
        mock_data1.index = 0

        mock_data2 = MagicMock()
        mock_data2.embedding = mock_embedding2
        mock_data2.index = 0

        mock_response = MagicMock()
        mock_response.data = [mock_data1, mock_data2]

        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        texts = ["Text 1", "Text 2"]
        result = await embedding_service.embed_batch(texts)

        # 按返回顺序对齐
        assert result[0] == mock_embedding1
        assert result[1] == mock_embedding2

    @pytest.mark.asyncio
    async def test_embed_batch_count_mismatch(
        self, embedding_service, mock_openai_client
    ):
        """返回数量与输入不一致时应报错，而非静默返回错位/缺失向量"""
        mock_embedding = [0.1, 0.2, 0.3]

        mock_data = MagicMock()
        mock_data.embedding = mock_embedding
        mock_data.index = 0

        mock_response = MagicMock()
        mock_response.data = [mock_data]  # 输入 2 条只返回 1 条

        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="数量不匹配"):
            await embedding_service.embed_batch(["Text 1", "Text 2"])

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