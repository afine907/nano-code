"""Skills 系统类型定义"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SkillCategory(Enum):
    """技能分类"""

    WEB = "web"  # 网页相关
    DATA = "data"  # 数据处理
    CODE = "code"  # 代码相关
    FILE = "file"  # 文件操作
    SYSTEM = "system"  # 系统操作
    SEARCH = "search"  # 搜索相关
    CUSTOM = "custom"  # 自定义


class SkillScope(Enum):
    """技能作用域"""

    GLOBAL = "global"  # 全局可用
    SESSION = "session"  # 当前会话
    PROJECT = "project"  # 当前项目


@dataclass
class SkillMetadata:
    """技能元数据"""

    name: str  # 技能名称
    description: str  # 技能描述
    category: SkillCategory  # 分类
    tags: list[str] = field(default_factory=list)  # 标签
    version: str = "1.0.0"  # 版本
    author: str = ""  # 作者
    examples: list[str] = field(default_factory=list)  # 使用示例
    requires: list[str] = field(default_factory=list)  # 依赖


@dataclass
class SkillDefinition:
    """技能定义"""

    id: str
    metadata: SkillMetadata
    handler: Callable[..., Any]  # 处理函数
    schema: dict[str, Any] = field(default_factory=dict)  # 输入 schema
    scope: SkillScope = SkillScope.GLOBAL  # 作用域
    enabled: bool = True  # 是否启用
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.id,
            "metadata": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "category": self.metadata.category.value,
                "tags": self.metadata.tags,
                "version": self.metadata.version,
                "author": self.metadata.author,
                "examples": self.metadata.examples,
                "requires": self.metadata.requires,
            },
            "schema": self.schema,
            "scope": self.scope.value,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SkillResult:
    """技能执行结果"""

    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
        }
