"""Skills 系统基类和装饰器"""

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from jojo_code.skills.types import SkillCategory, SkillDefinition, SkillMetadata, SkillScope

P = ParamSpec("P")
R = TypeVar("R")


def skill(
    name: str,
    description: str,
    category: SkillCategory = SkillCategory.CUSTOM,
    tags: list[str] | None = None,
    version: str = "1.0.0",
    author: str = "",
    examples: list[str] | None = None,
    requires: list[str] | None = None,
    scope: SkillScope = SkillScope.GLOBAL,
):
    """Skill 装饰器

    用法:
        @skill(
            name="web_search",
            description="搜索网页",
            category=SkillCategory.WEB,
            tags=["search", "web"],
            examples=["搜索 Python 教程"]
        )
        def handle_web_search(query: str) -> str:
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # 创建元数据
        metadata = SkillMetadata(
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            version=version,
            author=author,
            examples=examples or [],
            requires=requires or [],
        )

        # 创建技能定义
        skill_def = SkillDefinition(
            id=f"skill_{uuid.uuid4().hex[:8]}",
            metadata=metadata,
            handler=func,
            scope=scope,
        )

        # 将技能定义附加到函数
        func._skill_def = skill_def  # type: ignore

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return wrapper

    return decorator


class BaseSkill:
    """技能基类

    提供技能的默认实现和生命周期管理。
    """

    def __init__(self, name: str, description: str, category: SkillCategory = SkillCategory.CUSTOM):
        self.name = name
        self.description = description
        self.category = category
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """是否启用"""
        return self._enabled

    def enable(self) -> None:
        """启用技能"""
        self._enabled = True

    def disable(self) -> None:
        """禁用技能"""
        self._enabled = False

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """执行技能

        子类需要重写此方法。
        """
        raise NotImplementedError("子类必须实现 execute 方法")

    def validate(self, *args: Any, **kwargs: Any) -> bool:
        """验证输入参数

        返回 True 表示验证通过。
        """
        return True

    def get_metadata(self) -> SkillMetadata:
        """获取元数据"""
        return SkillMetadata(
            name=self.name,
            description=self.description,
            category=self.category,
        )


class SkillTool(BaseSkill):
    """技能工具适配器

    将 Skill 适配为 LangChain Tool。
    """

    def __init__(self, skill: BaseSkill):
        super().__init__(skill.name, skill.description, skill.category)
        self._skill = skill

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """执行技能"""
        return self._skill.execute(*args, **kwargs)

    def validate(self, *args: Any, **kwargs: Any) -> bool:
        """验证输入"""
        return self._skill.validate(*args, **kwargs)

    def to_langchain_tool(self):
        """转换为 LangChain Tool"""
        from langchain_core.tools import tool

        @tool(name=self.name, description=self.description)
        def langchain_wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.execute(*args, **kwargs)

        return langchain_wrapper


def create_skill_tool(skill: BaseSkill) -> Any:
    """创建 Skill 工具（工厂函数）

    Args:
        skill: 技能实例

    Returns:
        LangChain Tool
    """
    adapter = SkillTool(skill)
    return adapter.to_langchain_tool()
