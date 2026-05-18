"""Skills 系统

提供 Agent 技能扩展能力：
- Skill 定义和装饰器
- 技能管理器（注册、加载、执行）
- 内置 Skills
- 动态加载支持
"""

from jojo_code.skills.base import BaseSkill, SkillTool, create_skill_tool, skill
from jojo_code.skills.builtins import (
    analyze_code,
    calculate,
    format_json,
    read_file,
    run_command,
    translate,
    validate_json,
    web_fetch,
    web_search,
    write_file,
)
from jojo_code.skills.manager import SkillManager, get_skill_manager, set_skill_manager
from jojo_code.skills.types import (
    SkillCategory,
    SkillDefinition,
    SkillMetadata,
    SkillResult,
    SkillScope,
)

__all__ = [
    # Base
    "BaseSkill",
    "SkillTool",
    "skill",
    "create_skill_tool",
    # Manager
    "SkillManager",
    "get_skill_manager",
    "set_skill_manager",
    # Types
    "SkillCategory",
    "SkillDefinition",
    "SkillMetadata",
    "SkillResult",
    "SkillScope",
    # Builtins
    "web_search",
    "web_fetch",
    "read_file",
    "write_file",
    "run_command",
    "analyze_code",
    "format_json",
    "validate_json",
    "calculate",
    "translate",
]
