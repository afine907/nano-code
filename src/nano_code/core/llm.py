"""LLM 客户端配置"""

import os

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

# 模型配置
DEFAULT_MODEL = "gpt-4o-mini"


def get_llm(model: str | None = None, temperature: float = 0.7) -> BaseChatModel:
    """获取 LLM 实例

    根据 API Key 自动选择使用 OpenAI 或 Anthropic。

    Args:
        model: 模型名称，默认使用配置的模型
        temperature: 温度参数

    Returns:
        LLM 实例
    """
    model_name = model or os.getenv("NANO_CODE_MODEL", DEFAULT_MODEL)
    # 确保 model_name 不为 None
    if model_name is None:
        model_name = DEFAULT_MODEL

    # 检查 Anthropic API Key
    if os.getenv("ANTHROPIC_API_KEY"):
        # 如果是 Claude 模型则使用指定模型，否则使用默认 Claude 模型
        claude_model = model_name if model_name.startswith("claude") else "claude-sonnet-4-20250514"
        # mypy 对 ChatAnthropic 的参数检查有误，使用 type: ignore
        return ChatAnthropic(  # type: ignore[call-arg]
            model=claude_model,
            temperature=temperature,
        )

    # 默认使用 OpenAI
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
    )
