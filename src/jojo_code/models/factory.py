"""模型工厂 - 创建模型实例"""

import os
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from jojo_code.models.registry import get_model_registry
from jojo_code.models.types import ModelProvider


def create_model(
    model_name: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> BaseChatModel:
    """创建模型实例

    根据模型名称自动选择合适的 provider。
    支持以下配置方式（优先级从高到低）：

    1. 自定义 OpenAI 兼容 API:
       - OPENAI_BASE_URL: API 端点
       - OPENAI_API_KEY: API Key

    2. 环境变量指定:
       - ANTHROPIC_API_KEY: 使用 Anthropic
       - OPENAI_API_KEY: 使用 OpenAI

    3. 模型名称自动推断:
       - claude-* → Anthropic
       - gpt-* → OpenAI
       - 其他 → 自定义 API（需要配置 OPENAI_BASE_URL）

    Args:
        model_name: 模型名称，默认从配置读取
        temperature: 温度参数
        **kwargs: 额外参数

    Returns:
        模型实例
    """
    from jojo_code.core.config import get_settings

    settings = get_settings()
    model_name = model_name or settings.model or "gpt-4o-mini"

    # 获取模型信息
    registry = get_model_registry()
    model_info = registry.get(model_name)

    # 确定 provider
    provider = _determine_provider(model_name, model_info, settings)

    # 创建模型实例
    if provider == ModelProvider.ANTHROPIC:
        return _create_anthropic(model_name, temperature, settings, **kwargs)

    # OpenAI 或自定义兼容 API
    base_url = settings.openai_base_url or os.getenv("OPENAI_BASE_URL")
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=SecretStr(api_key) if api_key else None,
        base_url=base_url,
        **kwargs,
    )


def _determine_provider(
    model_name: str,
    model_info: Any,
    settings: Any,
) -> ModelProvider:
    """确定模型提供商"""

    # 1. 如果模型信息存在，使用预置信息
    if model_info:
        return model_info.provider

    # 2. 根据模型名称推断
    if model_name.startswith("claude"):
        return ModelProvider.ANTHROPIC
    if model_name.startswith("gpt"):
        return ModelProvider.OPENAI

    # 3. 检查环境变量
    if os.getenv("ANTHROPIC_API_KEY"):
        return ModelProvider.ANTHROPIC

    # 4. 检查是否配置了自定义 API
    if settings.openai_base_url or os.getenv("OPENAI_BASE_URL"):
        return ModelProvider.CUSTOM

    # 5. 默认 OpenAI
    return ModelProvider.OPENAI


def _create_anthropic(
    model_name: str,
    temperature: float,
    settings: Any,
    **kwargs: Any,
) -> ChatAnthropic:
    """创建 Anthropic 模型"""
    api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

    # 如果没有明确指定模型，使用默认
    if not model_name.startswith("claude"):
        model_name = "claude-sonnet-4-20250514"

    return ChatAnthropic(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        **kwargs,
    )


def create_fast_model(temperature: float = 0.3) -> BaseChatModel:
    """创建快速模型

    Args:
        temperature: 温度参数

    Returns:
        模型实例
    """
    registry = get_model_registry()
    fast_models = registry.list_fast()

    if fast_models:
        # 选择最便宜的
        fast_models.sort(key=lambda m: m.cost_per_1k_input)
        return create_model(fast_models[0].name, temperature)

    # 默认使用 mini
    return create_model("gpt-4o-mini", temperature)


def create_smart_model(temperature: float = 0.7) -> BaseChatModel:
    """创建智能模型

    Args:
        temperature: 温度参数

    Returns:
        模型实例
    """
    registry = get_model_registry()
    smart_models = registry.list_smart()

    if smart_models:
        # 选择最智能的
        return create_model(smart_models[0].name, temperature)

    # 默认使用 gpt-4o
    return create_model("gpt-4o", temperature)


def create_cheap_model(temperature: float = 0.5) -> BaseChatModel:
    """创建便宜模型

    Args:
        temperature: 温度参数

    Returns:
        模型实例
    """
    registry = get_model_registry()
    cheap_models = registry.list_cheap()

    if cheap_models:
        cheap_models.sort(key=lambda m: m.cost_per_1k_input)
        return create_model(cheap_models[0].name, temperature)

    return create_model("gpt-4o-mini", temperature)
