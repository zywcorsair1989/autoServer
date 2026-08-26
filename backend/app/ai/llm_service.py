"""LLM 服务 - 百炼 API 集成"""

import logging
from typing import List, Union, AsyncIterator, Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """使用百炼 API (OpenAI兼容) 的 LLM 服务"""

    def __init__(self):
        """使用百炼 API 配置初始化 LLM 服务"""
        self.client = AsyncOpenAI(
            api_key=settings.BAILIAN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = settings.BAILIAN_LLM_MODEL
        logger.info(f"LLM 服务使用模型 {self.model} 初始化")

    async def generate(
        self, messages: List[dict], stream: bool = False, temperature: float = 0.7
    ) -> Union[str, AsyncIterator[str]]:
        """
        从 LLM 生成响应

        Args:
            messages: 带 'role' 和 'content' 的消息字典列表
            stream: 是否流式传输响应
            temperature: 采样温度 (0.0 到 2.0)

        Returns:
            生成的文本字符串或流式传输的 AsyncIterator

        Raises:
            Exception: 如果 API 调用失败
        """
        try:
            formatted_messages: List[ChatCompletionMessageParam] = [
                {"role": msg["role"], "content": msg["content"]} for msg in messages
            ]

            if stream:
                return self._stream_generate(formatted_messages, temperature)
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    temperature=temperature,
                    # 显式关闭百炼联网搜索：知识库问答场景答案必须来自文档，
                    # 且联网搜索会显著拉长响应时间
                    extra_body={"enable_search": False},
                )
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("收到来自 LLM 的空响应")
                logger.debug(f"生成的响应: {content[:100]}...")
                return content

        except Exception as e:
            logger.error(f"LLM 生成失败: {str(e)}")
            raise

    async def _stream_generate(
        self, messages: List[ChatCompletionMessageParam], temperature: float
    ) -> AsyncIterator[str]:
        """
        从 LLM 流式生成响应

        Args:
            messages: 格式化的消息列表
            temperature: 采样温度

        Yields:
            来自流的文本块
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
                extra_body={"enable_search": False},
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"LLM 流式传输失败: {str(e)}")
            raise

    async def stream_generate(
        self, messages: List[dict], temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        流式传输生成的公共方法

        Args:
            messages: 消息字典列表
            temperature: 采样温度

        Yields:
            来自流的文本块
        """
        formatted_messages: List[ChatCompletionMessageParam] = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]
        async for chunk in self._stream_generate(formatted_messages, temperature):
            yield chunk