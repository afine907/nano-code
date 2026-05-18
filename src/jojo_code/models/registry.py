"""模型注册表"""

from typing import Any

from jojo_code.models.types import (
    PRESET_MODELS,
    ModelCapability,
    ModelInfo,
    ModelProvider,
)


class ModelRegistry:
    """模型注册表

    管理可用模型列表，支持自定义模型。
    """

    def __init__(self):
        self._models: dict[str, ModelInfo] = PRESET_MODELS.copy()
        self._custom_providers: dict[ModelProvider, Any] = {}

    def register(self, model_info: ModelInfo) -> None:
        """注册模型

        Args:
            model_info: 模型信息
        """
        self._models[model_info.name] = model_info

    def unregister(self, name: str) -> bool:
        """注销模型

        Args:
            name: 模型名称

        Returns:
            是否成功
        """
        if name in PRESET_MODELS:
            # 不能注销预置模型
            return False
        if name in self._models:
            del self._models[name]
            return True
        return False

    def get(self, name: str) -> ModelInfo | None:
        """获取模型信息

        Args:
            name: 模型名称

        Returns:
            模型信息，不存在返回 None
        """
        return self._models.get(name)

    def list_models(
        self,
        provider: ModelProvider | None = None,
        capability: ModelCapability | None = None,
        tags: list[str] | None = None,
    ) -> list[ModelInfo]:
        """列出模型

        Args:
            provider: 按提供商过滤
            capability: 按能力过滤
            tags: 按标签过滤（任一匹配）

        Returns:
            模型列表
        """
        result = list(self._models.values())

        if provider:
            result = [m for m in result if m.provider == provider]

        if capability:
            result = [m for m in result if capability in m.capabilities]

        if tags:
            result = [m for m in result if any(tag in m.tags for tag in tags)]

        return result

    def list_by_provider(self, provider: ModelProvider) -> list[ModelInfo]:
        """按提供商列出模型

        Args:
            provider: 提供商

        Returns:
            模型列表
        """
        return self.list_models(provider=provider)

    def list_fast(self) -> list[ModelInfo]:
        """列出快速模型

        Returns:
            模型列表
        """
        return self.list_models(tags=["fast"])

    def list_cheap(self) -> list[ModelInfo]:
        """列出便宜模型

        Returns:
            模型列表
        """
        return self.list_models(tags=["cheap"])

    def list_smart(self) -> list[ModelInfo]:
        """列出智能模型

        Returns:
            模型列表
        """
        return self.list_models(tags=["smart", "reasoning"])

    def register_custom_provider(
        self,
        provider: ModelProvider,
        factory: Any,
    ) -> None:
        """注册自定义提供商

        Args:
            provider: 提供商类型
            factory: 工厂函数
        """
        self._custom_providers[provider] = factory

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息
        """
        by_provider: dict[str, int] = {}
        total = len(self._models)

        for model in self._models.values():
            provider = model.provider.value
            by_provider[provider] = by_provider.get(provider, 0) + 1

        return {
            "total": total,
            "by_provider": by_provider,
        }


# 全局注册表
_default_registry: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    """获取全局模型注册表"""
    global _default_registry
    if _default_registry is None:
        _default_registry = ModelRegistry()
    return _default_registry


def set_model_registry(registry: ModelRegistry) -> None:
    """设置全局模型注册表"""
    global _default_registry
    _default_registry = registry
