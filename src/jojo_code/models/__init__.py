"""模型系统

支持多模型管理和切换：
- 预置模型列表 (OpenAI, Anthropic, LongCat 等)
- 模型注册表 (ModelRegistry)
- 工厂函数创建模型实例
- 快速/智能/便宜模型选择
"""

from jojo_code.models.factory import (
    create_cheap_model,
    create_fast_model,
    create_model,
    create_smart_model,
)
from jojo_code.models.registry import (
    ModelRegistry,
    get_model_registry,
    set_model_registry,
)
from jojo_code.models.types import (
    PRESET_MODELS,
    ModelCapability,
    ModelInfo,
    ModelProvider,
)

__all__ = [
    # Types
    "ModelCapability",
    "ModelInfo",
    "ModelProvider",
    "PRESET_MODELS",
    # Registry
    "ModelRegistry",
    "get_model_registry",
    "set_model_registry",
    # Factory
    "create_model",
    "create_fast_model",
    "create_smart_model",
    "create_cheap_model",
]
