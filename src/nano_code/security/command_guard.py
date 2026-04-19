"""命令权限守卫"""

import re
from functools import lru_cache
from typing import Any

from nano_code.security.guards import BaseGuard
from nano_code.security.permission import PermissionLevel, PermissionResult


class CommandGuard(BaseGuard):
    """命令权限守卫

    控制 Shell 命令执行权限：
    - 命令白名单
    - 危险命令拦截
    - 超时限制
    - 网络命令控制
    """

    # 网络相关命令
    NETWORK_COMMANDS = frozenset(
        ["curl", "wget", "nc", "netcat", "ssh", "scp", "rsync", "ftp", "telnet"]
    )

    def __init__(
        self,
        enabled: bool = True,
        allowed_commands: list[str] | None = None,
        denied_commands: list[str] | None = None,
        default: PermissionLevel = PermissionLevel.CONFIRM,
        max_timeout: int = 300,
        allow_network: bool = False,
    ):
        """初始化命令守卫

        Args:
            enabled: 是否启用 shell 工具
            allowed_commands: 允许的命令列表（白名单）
            denied_commands: 禁止的命令列表（黑名单）
            default: 默认权限级别
            max_timeout: 最大超时时间（秒）
            allow_network: 是否允许网络命令
        """
        self.enabled = enabled
        self.allowed_commands = allowed_commands or []
        self.denied_commands = denied_commands or []
        self.default = default
        self.max_timeout = max_timeout
        self.allow_network = allow_network

    @property
    def name(self) -> str:
        return "command_guard"

    def check(self, tool_name: str, args: dict[str, Any]) -> PermissionResult:
        """检查 shell 命令的执行权限"""
        if tool_name != "run_command":
            return PermissionResult(PermissionLevel.ALLOW, tool_name, args)

        if not self.enabled:
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason="Shell 命令已被禁用",
            )

        command = args.get("command", "")
        timeout = args.get("timeout", 30)

        # 1. 检查超时限制
        if timeout > self.max_timeout:
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason=f"超时时间 {timeout}s 超过最大限制 {self.max_timeout}s",
            )

        # 2. 检查黑名单命令
        for denied in self.denied_commands:
            if self._match_command(command, denied):
                return PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"命令匹配禁止模式: {denied}",
                )

        # 3. 检查网络命令
        if not self.allow_network and self._is_network_command(command):
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason="网络命令已被禁用",
            )

        # 4. 检查白名单命令
        for allowed in self.allowed_commands:
            if self._match_command(command, allowed):
                return PermissionResult(PermissionLevel.ALLOW, tool_name, args)

        # 5. 返回默认策略
        return PermissionResult(
            self.default,
            tool_name,
            args,
            reason=f"命令 '{command}' 不在白名单中",
        )

    @staticmethod
    @lru_cache(maxsize=128)
    def _compile_pattern(pattern: str) -> re.Pattern:
        """编译命令模式为正则表达式（带缓存）

        Args:
            pattern: 通配符模式

        Returns:
            编译后的正则表达式
        """
        regex_pattern = ""
        for char in pattern:
            if char == "*":
                regex_pattern += ".*"
            elif char in ".^$+?{}[]|()\\":
                regex_pattern += "\\" + char
            else:
                regex_pattern += char
        return re.compile(f"^{regex_pattern}", re.IGNORECASE)

    def _match_command(self, command: str, pattern: str) -> bool:
        """匹配命令模式

        支持通配符匹配:
        - * 匹配任意字符
        - 例如 "rm *" 匹配所有 rm 命令
        """
        command = command.strip()
        pattern = pattern.strip()

        try:
            regex = self._compile_pattern(pattern)
            return bool(regex.match(command))
        except re.error:
            return False

    def _is_network_command(self, command: str) -> bool:
        """检查是否为网络命令"""
        command = command.strip().lower()
        for tool in self.NETWORK_COMMANDS:
            if command.startswith(tool):
                return True
        return False
