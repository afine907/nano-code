"""模型类型定义"""

from dataclasses import dataclass, field
from enum import Enum


class ModelProvider(Enum):
    """模型提供商"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"  # 自定义 OpenAI 兼容 API
    LOCAL = "local"  # 本地模型


class ModelCapability(Enum):
    """模型能力"""

    CHAT = "chat"  # 对话
    FUNCTION_CALLING = "function_calling"  # 函数调用
    VISION = "vision"  # 视觉理解
    STREAMING = "streaming"  # 流式输出
    JSON_MODE = "json_mode"  # JSON 输出
    REASONING = "reasoning"  # 推理模型


# 能力简写
C = ModelCapability


@dataclass
class ModelInfo:
    """模型信息"""

    name: str  # 模型名称
    provider: ModelProvider  # 提供商
    display_name: str  # 显示名称
    description: str  # 描述
    context_length: int = 128000  # 上下文长度
    capabilities: list[ModelCapability] = field(default_factory=list)
    cost_per_1k_input: float = 0.0  # $ / 1K tokens
    cost_per_1k_output: float = 0.0  # $ / 1K tokens
    default_temperature: float = 0.7
    max_output_tokens: int = 16384
    tags: list[str] = field(default_factory=list)  # 标签: fast, cheap, smart 等


# 预置模型列表
PRESET_MODELS: dict[str, ModelInfo] = {
    # OpenAI
    "gpt-4o": ModelInfo(
        name="gpt-4o",
        provider=ModelProvider.OPENAI,
        display_name="GPT-4o",
        description="OpenAI 最新的旗舰模型，支持视觉和函数调用",
        context_length=128000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.VISION, C.STREAMING, C.JSON_MODE],
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
    ),
    "gpt-4o-mini": ModelInfo(
        name="gpt-4o-mini",
        provider=ModelProvider.OPENAI,
        display_name="GPT-4o Mini",
        description="小型快速模型，适合简单任务",
        context_length=128000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.STREAMING],
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        tags=["fast", "cheap"],
    ),
    "gpt-4-turbo": ModelInfo(
        name="gpt-4-turbo",
        provider=ModelProvider.OPENAI,
        display_name="GPT-4 Turbo",
        description="GPT-4 的快速版本",
        context_length=128000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.VISION, C.STREAMING],
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
    ),
    # Anthropic
    "claude-sonnet-4-20250514": ModelInfo(
        name="claude-sonnet-4-20250514",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude 4 Sonnet",
        description="Anthropic Claude 4 Sonnet 模型，平衡性能和成本",
        context_length=200000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.VISION, C.STREAMING],
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    ),
    "claude-opus-4-20250514": ModelInfo(
        name="claude-opus-4-20250514",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude 4 Opus",
        description="Anthropic 最强模型，适合复杂推理",
        context_length=200000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.VISION, C.STREAMING, C.REASONING],
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        tags=["smart", "reasoning"],
    ),
    "claude-3-5-sonnet-20240620": ModelInfo(
        name="claude-3-5-sonnet-20240620",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude 3.5 Sonnet",
        description="性价比高的 Claude 模型",
        context_length=200000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.VISION, C.STREAMING],
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    ),
    "claude-3-haiku-20240307": ModelInfo(
        name="claude-3-haiku-20240307",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude 3 Haiku",
        description="快速小型模型",
        context_length=200000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.VISION, C.STREAMING],
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        tags=["fast", "cheap"],
    ),
    # LongCat (自定义兼容)
    "LongCat-Flash-Chat": ModelInfo(
        name="LongCat-Flash-Chat",
        provider=ModelProvider.CUSTOM,
        display_name="LongCat Flash Chat",
        description="LongCat 快速对话模型",
        context_length=128000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.STREAMING],
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0003,
        tags=["fast", "cheap", "chinese"],
    ),
    "LongCat-Flash-Thinking-2601": ModelInfo(
        name="LongCat-Flash-Thinking-2601",
        provider=ModelProvider.CUSTOM,
        display_name="LongCat Flash Thinking",
        description="LongCat 推理模型，支持思考过程",
        context_length=128000,
        capabilities=[C.CHAT, C.FUNCTION_CALLING, C.STREAMING, C.REASONING],
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0006,
        tags=["reasoning", "chinese"],
    ),
}
