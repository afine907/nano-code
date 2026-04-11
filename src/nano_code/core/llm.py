"""LLM 客户端配置"""

import os

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from nano_code.core.config import get_settings

# 模型配置
DEFAULT_MODEL = "gpt-4o-mini"


def get_llm(model: str | None = None, temperature: float = 0.7) -> BaseChatModel:
    """获取 LLM 实例

    支持三种配置方式（优先级从高到低）：

    1. 自定义 OpenAI 兼容 API（设置 OPENAI_BASE_URL）:
       - OPENAI_API_KEY: API Key
       - OPENAI_BASE_URL: API 端点（如 https://api.longcat.chat/openai/v1）
       - NANO_CODE_MODEL: 模型名称

    2. Anthropic Claude（设置 ANTHROPIC_API_KEY）:
       - ANTHROPIC_API_KEY: API Key
       - NANO_CODE_MODEL: 模型名称（默认 claude-sonnet-4-20250514）

    3. OpenAI（默认）:
       - OPENAI_API_KEY: API Key
       - NANO_CODE_MODEL: 模型名称（默认 gpt-4o-mini）

    Args:
        model: 模型名称，默认使用配置的模型
        temperature: 温度参数

    Returns:
        LLM 实例
    """
    settings = get_settings()
    model_name = model or settings.model or DEFAULT_MODEL

    # 1. 自定义 OpenAI 兼容 API（如 LongCat）
    base_url = settings.openai_base_url or os.getenv("OPENAI_BASE_URL")
    if base_url:
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("设置了 OPENAI_BASE_URL 但未设置 OPENAI_API_KEY")
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=SecretStr(api_key),
            base_url=base_url,
        )

    # 2. Anthropic Claude
    if settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"):
        claude_model = model_name if model_name.startswith("claude") else "claude-sonnet-4-20250514"
        return ChatAnthropic(  # type: ignore[call-arg]
            model=claude_model,
            temperature=temperature,
        )

    # 3. OpenAI 默认
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=SecretStr(api_key),
    )
