"""权限管理器"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jojo_code.security.command_guard import CommandGuard
from jojo_code.security.guards import BaseGuard
from jojo_code.security.modes import PermissionMode, RiskLevel
from jojo_code.security.path_guard import PathGuard
from jojo_code.security.permission import PermissionLevel, PermissionResult
from jojo_code.security.risk import assess_risk


@dataclass
class PermissionConfig:
    """权限配置

    可通过代码创建或从 YAML 文件加载。
    """

    # Workspace 配置
    workspace_root: Path = field(default_factory=lambda: Path("."))
    allow_outside: bool = False

    # 文件权限
    allowed_paths: list[str] = field(default_factory=lambda: ["*"])
    denied_paths: list[str] = field(default_factory=list)
    confirm_on_write: list[str] = field(default_factory=list)

    # Shell 权限
    shell_enabled: bool = True
    allowed_commands: list[str] = field(default_factory=list)
    denied_commands: list[str] = field(default_factory=lambda: ["rm -rf /", "sudo"])
    shell_default: PermissionLevel = PermissionLevel.CONFIRM
    max_timeout: int = 300
    allow_network: bool = False

    # 全局设置
    max_tool_calls: int = 100
    audit_log: bool = True
    audit_log_path: Path = field(default_factory=lambda: Path(".jojo-code/audit.log"))

    # 权限模式
    mode: str = "auto"  # auto | manual | bypass (与 Claude Code 一致)

    def __post_init__(self) -> None:
        """确保路径是 Path 对象"""
        if isinstance(self.workspace_root, str):
            self.workspace_root = Path(self.workspace_root)
        if isinstance(self.audit_log_path, str):
            self.audit_log_path = Path(self.audit_log_path)

    @classmethod
    def from_yaml(cls, path: Path) -> "PermissionConfig":
        """从 YAML 文件加载配置

        Args:
            path: YAML 配置文件路径

        Returns:
            PermissionConfig 实例
        """
        try:
            import yaml
        except ImportError:
            return cls()

        if not path.exists():
            return cls()

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        workspace = data.get("workspace", {})
        file_config = data.get("file", {})
        shell_config = data.get("shell", {})
        global_config = data.get("global", {})

        # 解析默认权限级别
        shell_default = PermissionLevel.CONFIRM
        if "default" in shell_config:
            try:
                shell_default = PermissionLevel(shell_config["default"])
            except ValueError:
                pass

        return cls(
            workspace_root=Path(workspace.get("root", ".")),
            allow_outside=workspace.get("allow_outside", False),
            allowed_paths=file_config.get("allowed_paths", ["*"]),
            denied_paths=file_config.get("denied_paths", []),
            confirm_on_write=file_config.get("confirm_on_write", []),
            shell_enabled=shell_config.get("enabled", True),
            allowed_commands=shell_config.get("allowed_commands", []),
            denied_commands=shell_config.get("denied_commands", ["rm -rf /", "sudo"]),
            shell_default=shell_default,
            max_timeout=shell_config.get("max_timeout", 300),
            allow_network=shell_config.get("allow_network", False),
            max_tool_calls=global_config.get("max_tool_calls", 100),
            audit_log=global_config.get("audit_log", True),
            audit_log_path=Path(global_config.get("audit_log_path", ".jojo-code/audit.log")),
        )

    @classmethod
    def development(cls) -> "PermissionConfig":
        """开发模式配置（宽松）"""
        return cls(
            workspace_root=Path("."),
            allow_outside=False,
            denied_paths=[".env", "*.pem", "*.key"],
            shell_enabled=True,
            shell_default=PermissionLevel.CONFIRM,
            denied_commands=["rm -rf /", "rm -rf ~", "sudo"],
        )

    @classmethod
    def production(cls) -> "PermissionConfig":
        """生产模式配置（严格）"""
        return cls(
            workspace_root=Path("."),
            allow_outside=False,
            allowed_paths=["src/**", "tests/**", "*.md", "*.txt"],
            denied_paths=[".env", ".git/**", "secrets/**", "*.pem", "*.key"],
            confirm_on_write=["**"],
            shell_enabled=True,
            allowed_commands=["ls", "cat", "head", "tail", "grep", "pytest"],
            denied_commands=["rm *", "sudo *", "curl *", "wget *"],
            shell_default=PermissionLevel.CONFIRM,
            allow_network=False,
            max_tool_calls=50,
            audit_log=True,
        )


class PermissionManager:
    """权限管理器

    协调所有权限守卫进行权限检查。
    支持权限模式和风险评估。
    """

    # 日志缓冲区大小
    LOG_BUFFER_SIZE = 10

    def __init__(self, config: PermissionConfig):
        """初始化权限管理器

        Args:
            config: 权限配置
        """
        self.config = config
        self._mode = PermissionMode(config.mode)
        self.guards: list[BaseGuard] = []
        self._call_count = 0
        self._audit_log: list[dict[str, Any]] = []
        self._log_buffer: list[str] = []

        # 初始化守卫
        self._init_guards()

    @property
    def mode(self) -> PermissionMode:
        """获取当前权限模式"""
        return self._mode

    def set_mode(self, mode: str) -> None:
        """设置权限模式

        Args:
            mode: 权限模式字符串 (yolo | auto_approve | interactive | strict | readonly)
        """
        self._mode = PermissionMode.from_string(mode)
        self.config.mode = mode

    def _init_guards(self) -> None:
        """初始化权限守卫"""
        self.guards = [
            PathGuard(
                workspace_root=self.config.workspace_root,
                allowed_patterns=self.config.allowed_paths,
                denied_patterns=self.config.denied_paths,
                confirm_patterns=self.config.confirm_on_write,
                allow_outside=self.config.allow_outside,
            ),
            CommandGuard(
                enabled=self.config.shell_enabled,
                allowed_commands=self.config.allowed_commands,
                denied_commands=self.config.denied_commands,
                default=self.config.shell_default,
                max_timeout=self.config.max_timeout,
                allow_network=self.config.allow_network,
            ),
        ]

    def check(self, tool_name: str, args: dict[str, Any]) -> PermissionResult:
        """检查工具调用权限

        根据权限模式和风险评估决定是否允许执行。

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            权限检查结果
        """
        # 1. BYPASS 模式直接放行
        if self._mode == PermissionMode.BYPASS:
            return PermissionResult(PermissionLevel.ALLOW, tool_name, args)

        # 2. 检查调用次数限制
        if self._call_count >= self.config.max_tool_calls:
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason=f"已达到最大调用次数 {self.config.max_tool_calls}",
            )

        # 3. 评估风险等级
        risk = assess_risk(tool_name, args)

        # 4. MANUAL 模式检查 (所有写操作需要确认)
        if self._mode == PermissionMode.MANUAL:
            if risk in ("medium", "high", "critical"):
                return PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"Manual 模式拒绝 {risk} 风险操作",
                )

        # 5. 运行守卫检查
        final_result = PermissionResult(PermissionLevel.ALLOW, tool_name, args)

        for guard in self.guards:
            result = guard.check(tool_name, args)

            # 记录审计日志
            if self.config.audit_log:
                self._log_call(tool_name, args, result)

            # 取最严格的权限级别
            if result.level > final_result.level:
                final_result = result

            # 如果被拒绝，立即返回
            if result.denied:
                return result

        # 6. 根据权限模式和风险等级调整决策
        if final_result.level == PermissionLevel.ALLOW:
            risk_level = RiskLevel.from_string(risk)

            # MANUAL 模式: 所有操作都需确认
            if self._mode == PermissionMode.MANUAL:
                return PermissionResult(
                    PermissionLevel.CONFIRM,
                    tool_name,
                    args,
                    reason=f"Manual 模式需要确认所有操作 (风险: {risk})",
                )

            # AUTO 模式: 中高风险需确认 (MEDIUM+)
            if self._mode == PermissionMode.AUTO:
                if risk_level >= RiskLevel.MEDIUM:
                    return PermissionResult(
                        PermissionLevel.CONFIRM,
                        tool_name,
                        args,
                        reason=f"操作需要确认 (风险: {risk})",
                    )

        self._call_count += 1
        return final_result

    def _log_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: PermissionResult,
    ) -> None:
        """记录审计日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "args": args,
            "result": result.level.value,
            "reason": result.reason,
        }
        self._audit_log.append(entry)

        # 写入缓冲区
        if self.config.audit_log_path:
            self._log_buffer.append(json.dumps(entry, ensure_ascii=False))

            # 缓冲区满时批量写入
            if len(self._log_buffer) >= self.LOG_BUFFER_SIZE:
                self._flush_log_buffer()

    def _flush_log_buffer(self) -> None:
        """刷新日志缓冲区到文件"""
        if not self._log_buffer or not self.config.audit_log_path:
            return

        self.config.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.audit_log_path, "a", encoding="utf-8") as f:
            for line in self._log_buffer:
                f.write(line + "\n")
        self._log_buffer.clear()

    def flush(self) -> None:
        """手动刷新日志缓冲区"""
        self._flush_log_buffer()

    def get_audit_log(self) -> list[dict[str, Any]]:
        """获取审计日志

        Returns:
            审计日志列表
        """
        return self._audit_log.copy()

    def reset_call_count(self) -> None:
        """重置调用计数"""
        self._call_count = 0


# 全局权限管理器实例
_permission_manager: PermissionManager | None = None


def get_permission_manager() -> PermissionManager | None:
    """获取全局权限管理器实例"""
    return _permission_manager


def set_permission_manager(manager: PermissionManager) -> None:
    """设置全局权限管理器实例"""
    global _permission_manager
    _permission_manager = manager


def init_permission_manager(config: PermissionConfig | None = None) -> PermissionManager:
    """初始化权限管理器

    Args:
        config: 权限配置，默认使用开发模式

    Returns:
        PermissionManager 实例
    """
    global _permission_manager
    if config is None:
        config = PermissionConfig.development()
    _permission_manager = PermissionManager(config)
    return _permission_manager
