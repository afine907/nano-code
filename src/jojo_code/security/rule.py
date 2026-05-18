"""权限规则引擎 - 支持通配符匹配和灵活规则"""

import fnmatch
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuleAction(Enum):
    """规则动作"""

    ALLOW = "allow"  # 允许
    DENY = "deny"  # 拒绝
    ASK = "ask"  # 询问用户


class RuleMatchType(Enum):
    """规则匹配类型"""

    EXACT = "exact"  # 精确匹配
    GLOB = "glob"  # 通配符匹配 (fnmatch)
    REGEX = "regex"  # 正则匹配
    PREFIX = "prefix"  # 前缀匹配


@dataclass
class PermissionRule:
    """权限规则

    用于匹配工具调用并决定权限动作。
    支持多种匹配方式：精确、通配符、正则、前缀。
    """

    # 规则名称（用于日志和调试）
    name: str = ""

    # 工具名匹配
    tool_pattern: str = "*"
    match_type: RuleMatchType = RuleMatchType.GLOB

    # 参数匹配 (可选)
    # 例如: {"command": "rm *", "path": "*.py"}
    args_pattern: dict[str, str] = field(default_factory=dict)

    # 规则动作
    action: RuleAction = RuleAction.ALLOW

    # 规则优先级 (数字越大优先级越高)
    priority: int = 0

    # 规则描述
    description: str = ""

    # 是否启用
    enabled: bool = True

    def matches_tool(self, tool_name: str) -> bool:
        """检查工具名是否匹配此规则

        Args:
            tool_name: 工具名称

        Returns:
            是否匹配
        """
        if not self.enabled:
            return False

        if self.match_type == RuleMatchType.EXACT:
            return tool_name == self.tool_pattern
        elif self.match_type == RuleMatchType.GLOB:
            return fnmatch.fnmatch(tool_name, self.tool_pattern)
        elif self.match_type == RuleMatchType.REGEX:
            return bool(re.match(self.tool_pattern, tool_name))
        elif self.match_type == RuleMatchType.PREFIX:
            return tool_name.startswith(self.tool_pattern)
        return False

    def matches_args(self, args: dict[str, Any]) -> bool:
        """检查参数是否匹配此规则

        Args:
            args: 工具参数

        Returns:
            是否匹配所有指定的条件
        """
        if not self.args_pattern:
            return True  # 没有参数模式要求，默认匹配

        for key, pattern in self.args_pattern.items():
            if key not in args:
                return False

            value = str(args[key])
            if not fnmatch.fnmatch(value, pattern):
                return False

        return True

    def matches(self, tool_name: str, args: dict[str, Any]) -> bool:
        """检查工具调用是否完全匹配此规则

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            是否完全匹配
        """
        return self.matches_tool(tool_name) and self.matches_args(args)

    def __repr__(self) -> str:
        name = self.name or self.tool_pattern
        return f"PermissionRule({name}, action={self.action.value}, priority={self.priority})"


class RuleEngine:
    """权限规则引擎

    管理一组权限规则，按优先级匹配并返回结果。
    """

    def __init__(self):
        self.rules: list[PermissionRule] = []
        self._default_action: RuleAction = RuleAction.ASK

    @property
    def default_action(self) -> RuleAction:
        return self._default_action

    @default_action.setter
    def default_action(self, action: RuleAction) -> None:
        self._default_action = action

    def add_rule(self, rule: PermissionRule) -> None:
        """添加规则

        Args:
            rule: 权限规则
        """
        self.rules.append(rule)
        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def add_rules(self, rules: list[PermissionRule]) -> None:
        """批量添加规则

        Args:
            rules: 权限规则列表
        """
        for rule in rules:
            self.add_rule(rule)

    def remove_rule(self, name: str) -> bool:
        """移除规则

        Args:
            name: 规则名称

        Returns:
            是否成功移除
        """
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                self.rules.pop(i)
                return True
        return False

    def find_matching_rule(self, tool_name: str, args: dict[str, Any]) -> PermissionRule | None:
        """查找第一个匹配的规则

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            匹配的规则，如果没有匹配的规则则返回 None
        """
        for rule in self.rules:
            if rule.matches(tool_name, args):
                return rule
        return None

    def check(self, tool_name: str, args: dict[str, Any]) -> RuleAction:
        """检查工具调用并返回规则动作

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            规则动作 (ALLOW/DENY/ASK)
        """
        rule = self.find_matching_rule(tool_name, args)
        if rule:
            return rule.action
        return self._default_action

    def clear(self) -> None:
        """清空所有规则"""
        self.rules.clear()

    def list_rules(self) -> list[PermissionRule]:
        """列出所有规则

        Returns:
            规则列表
        """
        return self.rules.copy()

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "RuleEngine":
        """从配置创建规则引擎

        Args:
            config: 配置字典

        Returns:
            RuleEngine 实例
        """
        engine = cls()

        # 设置默认动作
        if "default_action" in config:
            engine.default_action = RuleAction(config["default_action"])

        # 添加规则
        for rule_config in config.get("rules", []):
            rule = PermissionRule(
                name=rule_config.get("name", ""),
                tool_pattern=rule_config.get("tool_pattern", "*"),
                match_type=RuleMatchType(rule_config.get("match_type", "glob")),
                args_pattern=rule_config.get("args_pattern", {}),
                action=RuleAction(rule_config.get("action", "allow")),
                priority=rule_config.get("priority", 0),
                description=rule_config.get("description", ""),
                enabled=rule_config.get("enabled", True),
            )
            engine.add_rule(rule)

        return engine


# 预定义规则工厂
class RuleFactory:
    """规则工厂 - 常用规则模板"""

    @staticmethod
    def allow_all_tools() -> PermissionRule:
        """允许所有工具"""
        return PermissionRule(
            name="allow_all",
            tool_pattern="*",
            action=RuleAction.ALLOW,
            priority=0,
            description="允许所有工具执行",
        )

    @staticmethod
    def deny_dangerous_commands() -> list[PermissionRule]:
        """危险命令拒绝规则"""
        return [
            PermissionRule(
                name="deny_rm_rf",
                tool_pattern="run_command",
                args_pattern={"command": "rm -rf *"},
                action=RuleAction.DENY,
                priority=100,
                description="禁止 rm -rf 命令",
            ),
            PermissionRule(
                name="deny_sudo",
                tool_pattern="run_command",
                args_pattern={"command": "sudo *"},
                action=RuleAction.DENY,
                priority=100,
                description="禁止 sudo 命令",
            ),
            PermissionRule(
                name="deny_chmod_777",
                tool_pattern="run_command",
                args_pattern={"command": "chmod 777 *"},
                action=RuleAction.DENY,
                priority=100,
                description="禁止 chmod 777",
            ),
        ]

    @staticmethod
    def require_confirmation_for_writes() -> list[PermissionRule]:
        """MANUAL 模式：写操作需要确认"""
        write_tools = ["write_file", "edit_file", "run_command", "delete_file"]
        rules = []
        for tool in write_tools:
            rules.append(
                PermissionRule(
                    name=f"ask_{tool}",
                    tool_pattern=tool,
                    action=RuleAction.ASK,
                    priority=50,
                    description=f"执行 {tool} 需要确认",
                )
            )
        return rules


__all__ = [
    "RuleAction",
    "RuleMatchType",
    "PermissionRule",
    "RuleEngine",
    "RuleFactory",
]
