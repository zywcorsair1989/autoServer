"""Tests for Rerank Service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
# from app.ai.rerank_service import RerankService

from backend.app.ai.rerank_service import RerankService

@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client"""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        yield mock_client


@pytest.fixture
def rerank_service():
    """Create Rerank Service instance"""
    return RerankService()


class TestRerankService:
    """Test suite for Rerank Service"""

    def test_rerank_service_initialization(self):
        """Test Rerank Service initializes correctly"""
        service = RerankService()

        assert service.model == "gte-rerank-v2"
        assert service.api_key == ""
        assert service.base_url == "https://dashscope.aliyuncs.com/api/v1/services/rerank"

    @pytest.mark.asyncio
    async def test_rerank(self, rerank_service, mock_httpx_client):
        """Test reranking documents"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "output": {
                "results": [
                    {"index": 2, "relevance_score": 0.95},
                    {"index": 0, "relevance_score": 0.85},
                    {"index": 1, "relevance_score": 0.75},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        query = "What is machine learning?"
        documents = [
            "Machine learning is a subset of AI.",
            "Python is a programming language.",
            "Deep learning uses neural networks.",
        ]

        result = await rerank_service.rerank(query, documents, top_n=3)

        assert len(result) == 3
        assert result[0]["index"] == 2
        assert result[0]["relevance_score"] == 0.95
        assert result[0]["document"] == "Deep learning uses neural networks."
        assert result[1]["index"] == 0
        assert result[1]["relevance_score"] == 0.85
        assert result[2]["index"] == 1
        assert result[2]["relevance_score"] == 0.75

    @pytest.mark.asyncio
    async def test_rerank_with_top_n(self, rerank_service, mock_httpx_client):
        """Test reranking with top_n limit"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "output": {
                "results": [
                    {"index": 1, "relevance_score": 0.90},
                    {"index": 0, "relevance_score": 0.80},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        query = "Test query"
        documents = ["Doc 1", "Doc 2", "Doc 3"]

        result = await rerank_service.rerank(query, documents, top_n=2)

        assert len(result) == 2

        # Verify top_n was sent to API
        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["json"]["parameters"]["top_n"] == 2

    @pytest.mark.asyncio
    async def test_rerank_with_scores(self, rerank_service, mock_httpx_client):
        """Test reranking with scores as tuples"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "output": {
                "results": [
                    {"index": 1, "relevance_score": 0.95},
                    {"index": 0, "relevance_score": 0.85},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        query = "Test query"
        documents = ["Doc 1", "Doc 2"]

        result = await rerank_service.rerank_with_scores(query, documents, top_n=2)

        assert len(result) == 2
        assert result[0] == (1, 0.95, "Doc 2")
        assert result[1] == (0, 0.85, "Doc 1")

    @pytest.mark.asyncio
    async def test_rerank_http_error(self, rerank_service, mock_httpx_client):
        """Test HTTP error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = http_error
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        query = "Test query"
        documents = ["Doc 1"]

        with pytest.raises(Exception, match="Rerank API failed: 500"):
            await rerank_service.rerank(query, documents)

    @pytest.mark.asyncio
    async def test_rerank_network_error(self, rerank_service, mock_httpx_client):
        """Test network error handling"""
        mock_httpx_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Network error", request=MagicMock())
        )

        query = "Test query"
        documents = ["Doc 1"]

        with pytest.raises(Exception):
            await rerank_service.rerank(query, documents)

    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self, rerank_service, mock_httpx_client):
        """Test reranking with empty document list"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"output": {"results": []}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        query = "Test query"
        documents = []

        result = await rerank_service.rerank(query, documents, top_n=5)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_rerank_single_document(self, rerank_service, mock_httpx_client):
        """Test reranking with single document"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "output": {"results": [{"index": 0, "relevance_score": 1.0}]}
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        query = "Test query"
        documents = ["Single document"]

        result = await rerank_service.rerank(query, documents, top_n=1)

        assert len(result) == 1
        assert result[0]["index"] == 0
        assert result[0]["document"] == "Single document"