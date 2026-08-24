"""Tests for LLM Service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.ai.llm_service import LLMService


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    with patch("app.ai.llm_service.AsyncOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def llm_service(mock_openai_client):
    """Create LLM Service instance with mocked client"""
    return LLMService()


class TestLLMService:
    """Test suite for LLM Service"""

    def test_llm_service_initialization(self, mock_openai_client):
        """Test LLM Service initializes correctly"""
        service = LLMService()

        assert service.model == "qwen3.7-max-2026-06-08"
        assert service.client is not None

    @pytest.mark.asyncio
    async def test_generate_non_stream(self, llm_service, mock_openai_client):
        """Test non-streaming generation"""
        # Mock response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is a test response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hello, how are you?"}]
        result = await llm_service.generate(messages, stream=False)

        assert result == "This is a test response"
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_temperature(self, llm_service, mock_openai_client):
        """Test generation with custom temperature"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Response with temperature"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hello"}]
        result = await llm_service.generate(messages, stream=False, temperature=0.5)

        assert result == "Response with temperature"
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_generate_empty_response_raises_error(
        self, llm_service, mock_openai_client
    ):
        """Test that empty response raises ValueError"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(ValueError, match="Received empty response from LLM"):
            await llm_service.generate(messages, stream=False)

    @pytest.mark.asyncio
    async def test_stream_generate(self, llm_service, mock_openai_client):
        """Test streaming generation"""
        # Mock streaming response
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock(delta=MagicMock(content="Hello"))]

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock(delta=MagicMock(content=" world"))]

        mock_chunk3 = MagicMock()
        mock_chunk3.choices = [MagicMock(delta=MagicMock(content="!"))]

        # Create async generator
        async def mock_stream():
            for chunk in [mock_chunk1, mock_chunk2, mock_chunk3]:
                yield chunk

        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )

        messages = [{"role": "user", "content": "Say hello"}]
        chunks = []
        async for chunk in llm_service.stream_generate(messages):
            chunks.append(chunk)

        assert chunks == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_generate_api_error(self, llm_service, mock_openai_client):
        """Test API error handling"""
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(Exception, match="API Error"):
            await llm_service.generate(messages, stream=False)

    @pytest.mark.asyncio
    async def test_generate_with_multiple_messages(self, llm_service, mock_openai_client):
        """Test generation with conversation history"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "AI response to conversation"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        result = await llm_service.generate(messages, stream=False)

        assert result == "AI response to conversation"
        call_args = mock_openai_client.chat.completions.create.call_args
        assert len(call_args.kwargs["messages"]) == 4