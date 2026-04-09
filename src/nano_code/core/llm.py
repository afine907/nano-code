"""LLM 客户端配置"""
import os

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# 模型配置
DEFAULT_MODEL = "gpt-4o-mini"


def get_llm(model: str | None = None, temperature: float = 0.7):
    """获取 LLM 实例

    根据 API Key 自动选择使用 OpenAI 或 Anthropic。

    Args:
        model: 模型名称，默认使用配置的模型
        temperature: 温度参数

    Returns:
        LLM 实例
    """
    model = model or os.getenv("NANO_CODE_MODEL", DEFAULT_MODEL)

    # 检查 Anthropic API Key
    if os.getenv("ANTHROPIC_API_KEY"):
        return ChatAnthropic(
            model=model if model.startswith("claude") else "claude-sonnet-4-20250514",
            temperature=temperature,
        )

    # 默认使用 OpenAI
    return ChatOpenAI(
        model=model,
        temperature=temperature,
    )
