"""Skills 管理器"""

import uuid
from pathlib import Path
from typing import Any

from jojo_code.skills.types import (
    SkillCategory,
    SkillDefinition,
    SkillMetadata,
    SkillResult,
    SkillScope,
)


class SkillManager:
    """技能管理器

    负责技能的注册、加载、卸载和执行。
    支持:
    - 手动注册
    - 动态加载(从目录/文件)
    - 内置技能
    - 技能搜索和过滤
    """

    def __init__(self, skills_dir: Path | str | None = None):
        """初始化技能管理器

        Args:
            skills_dir: 技能目录(默认 ~/.jojo-code/skills)
        """
        if skills_dir is None:
            skills_dir = Path.home() / ".jojo-code" / "skills"

        self.skills_dir = Path(skills_dir)
        self._skills: dict[str, SkillDefinition] = {}
        self._enabled = True

        # 确保目录存在
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def register(self, skill_def: SkillDefinition) -> None:
        """注册技能

        Args:
            skill_def: 技能定义
        """
        self._skills[skill_def.id] = skill_def

    def register_function(
        self,
        func: Any,
        name: str | None = None,
        description: str = "",
        category: SkillCategory = SkillCategory.CUSTOM,
        tags: list[str] | None = None,
    ) -> str:
        """注册函数为技能

        Args:
            func: 函数对象
            name: 技能名称(默认使用函数名)
            description: 描述
            category: 分类
            tags: 标签

        Returns:
            技能 ID
        """
        skill_id = f"skill_{uuid.uuid4().hex[:8]}"

        metadata = SkillMetadata(
            name=name or func.__name__,
            description=description or func.__doc__ or "",
            category=category,
            tags=tags or [],
        )

        skill_def = SkillDefinition(
            id=skill_id,
            metadata=metadata,
            handler=func,
        )

        self.register(skill_def)
        return skill_id

    def unregister(self, skill_id: str) -> bool:
        """注销技能

        Args:
            skill_id: 技能 ID

        Returns:
            是否成功
        """
        if skill_id in self._skills:
            del self._skills[skill_id]
            return True
        return False

    def get(self, skill_id: str) -> SkillDefinition | None:
        """获取技能

        Args:
            skill_id: 技能 ID

        Returns:
            技能定义,不存在返回 None
        """
        return self._skills.get(skill_id)

    def get_by_name(self, name: str) -> SkillDefinition | None:
        """通过名称获取技能

        Args:
            name: 技能名称

        Returns:
            技能定义,不存在返回 None
        """
        for skill_def in self._skills.values():
            if skill_def.metadata.name == name:
                return skill_def
        return None

    def list_skills(
        self,
        category: SkillCategory | None = None,
        scope: SkillScope | None = None,
        enabled_only: bool = True,
    ) -> list[SkillDefinition]:
        """列出技能

        Args:
            category: 按分类过滤
            scope: 按作用域过滤
            enabled_only: 只返回启用的

        Returns:
            技能列表
        """
        result = list(self._skills.values())

        if category:
            result = [s for s in result if s.metadata.category == category]

        if scope:
            result = [s for s in result if s.scope == scope]

        if enabled_only:
            result = [s for s in result if s.enabled]

        return result

    def enable(self, skill_id: str) -> bool:
        """启用技能"""
        if skill_id in self._skills:
            self._skills[skill_id].enabled = True
            return True
        return False

    def disable(self, skill_id: str) -> bool:
        """禁用技能"""
        if skill_id in self._skills:
            self._skills[skill_id].enabled = False
            return True
        return False

    def execute(self, skill_id: str, *args: Any, **kwargs: Any) -> SkillResult:
        """执行技能

        Args:
            skill_id: 技能 ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        import time

        start = time.time()

        skill_def = self.get(skill_id)
        if not skill_def:
            return SkillResult(
                success=False,
                error=f"Skill {skill_id} not found",
                duration_ms=(time.time() - start) * 1000,
            )

        if not skill_def.enabled:
            return SkillResult(
                success=False,
                error=f"Skill {skill_id} is disabled",
                duration_ms=(time.time() - start) * 1000,
            )

        try:
            output = skill_def.handler(*args, **kwargs)
            return SkillResult(
                success=True,
                output=output,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def execute_by_name(self, name: str, *args: Any, **kwargs: Any) -> SkillResult:
        """通过名称执行技能

        Args:
            name: 技能名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        skill_def = self.get_by_name(name)
        if not skill_def:
            return SkillResult(
                success=False,
                error=f"Skill '{name}' not found",
            )

        return self.execute(skill_def.id, *args, **kwargs)

    def search(self, keyword: str) -> list[SkillDefinition]:
        """搜索技能

        Args:
            keyword: 关键词

        Returns:
            匹配的技能列表
        """
        keyword_lower = keyword.lower()
        results = []

        for skill_def in self._skills.values():
            # 搜索名称、描述、标签
            if (
                keyword_lower in skill_def.metadata.name.lower()
                or keyword_lower in skill_def.metadata.description.lower()
                or any(keyword_lower in tag.lower() for tag in skill_def.metadata.tags)
            ):
                results.append(skill_def)

        return results

    def load_from_directory(self, directory: Path | str) -> int:
        """从目录动态加载技能

        Args:
            directory: 目录路径

        Returns:
            加载的技能数量
        """
        import importlib.util
        import sys

        dir_path = Path(directory)
        if not dir_path.exists():
            return 0

        loaded = 0
        for py_file in dir_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            # 动态导入模块
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[py_file.stem] = module
                spec.loader.exec_module(module)

                # 查找被装饰的函数
                for name in dir(module):
                    obj = getattr(module, name)
                    if hasattr(obj, "_skill_def"):
                        self.register(obj._skill_def)
                        loaded += 1

        return loaded

    def load_builtin_skills(self) -> int:
        """加载内置技能

        Returns:
            加载的技能数量
        """
        import importlib

        # 从内置模块加载
        builtin_modules = [
            "jojo_code.skills.builtins",
        ]

        loaded = 0
        for module_name in builtin_modules:
            try:
                module = importlib.import_module(module_name)

                # 查找被装饰的函数
                for name in dir(module):
                    obj = getattr(module, name)
                    if hasattr(obj, "_skill_def"):
                        self.register(obj._skill_def)
                        loaded += 1
            except ImportError:
                pass

        return loaded

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息
        """
        categories: dict[str, int] = {}
        total = len(self._skills)
        enabled = sum(1 for s in self._skills.values() if s.enabled)

        for skill_def in self._skills.values():
            cat = skill_def.metadata.category.value
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "categories": categories,
        }


# 全局技能管理器
_default_manager: SkillManager | None = None


def get_skill_manager() -> SkillManager:
    """获取全局技能管理器"""
    global _default_manager
    if _default_manager is None:
        _default_manager = SkillManager()
        # 加载内置技能
        _default_manager.load_builtin_skills()
    return _default_manager


def set_skill_manager(manager: SkillManager) -> None:
    """设置全局技能管理器"""
    global _default_manager
    _default_manager = manager
