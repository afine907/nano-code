"""增强版权限管理器 - 集成规则引擎和拒绝追踪"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from jojo_code.security.denial import AdaptivePermissionMixin, DenialTracker
from jojo_code.security.manager import PermissionConfig
from jojo_code.security.manager import PermissionManager as BasePermissionManager
from jojo_code.security.modes import PermissionMode
from jojo_code.security.permission import PermissionLevel, PermissionResult
from jojo_code.security.rule import (
    RuleAction,
    RuleEngine,
    RuleFactory,
)

# 用户确认回调类型
ConfirmCallback = Callable[[PermissionResult], bool]


@dataclass
class EnhancedPermissionConfig:
    """增强版权限配置"""

    # 基础配置
    base: PermissionConfig = field(default_factory=PermissionConfig)

    # 规则引擎配置
    enable_rule_engine: bool = True
    default_rule_action: str = "ask"  # allow/deny/ask

    # 拒绝追踪配置
    enable_denial_tracking: bool = True
    denial_threshold: int = 3  # 超过此次数认为是重复请求
    denial_window_seconds: int = 300  # 时间窗口

    # 用户确认回调
    confirm_callback: ConfirmCallback | None = None


class EnhancedPermissionManager(AdaptivePermissionMixin):
    """增强版权限管理器

    整合了:
    1. 基础权限检查 (PathGuard, CommandGuard)
    2. 规则引擎 (RuleEngine) - 灵活匹配
    3. 拒绝追踪 (DenialTracker) - 防止重复被拒
    4. 用户确认回调 - 交互式确认
    """

    def __init__(self, config: EnhancedPermissionConfig | None = None):
        # 初始化配置
        self.config = config or EnhancedPermissionConfig()

        # 基础权限管理器
        self._base = BasePermissionManager(self.config.base)

        # 规则引擎
        if self.config.enable_rule_engine:
            self._rule_engine = RuleEngine()
            self._rule_engine.default_action = RuleAction(self.config.default_rule_action)
            self._init_default_rules()
        else:
            self._rule_engine = None

        # 拒绝追踪
        if self.config.enable_denial_tracking:
            self._denial_tracker = DenialTracker(
                threshold=self.config.denial_threshold,
                window_seconds=self.config.denial_window_seconds,
            )
        else:
            self._denial_tracker = None

        # 用户确认回调
        self._confirm_callback = self.config.confirm_callback

    def _init_default_rules(self) -> None:
        """初始化默认规则"""
        # 添加危险命令拒绝规则
        for rule in RuleFactory.deny_dangerous_commands():
            self._rule_engine.add_rule(rule)

    @property
    def mode(self) -> PermissionMode:
        """获取权限模式"""
        return self._base.mode

    def set_mode(self, mode: str) -> None:
        """设置权限模式"""
        self._base.set_mode(mode)

    def set_confirm_callback(self, callback: ConfirmCallback) -> None:
        """设置用户确认回调

        Args:
            callback: 确认回调函数，接收 PermissionResult，返回是否确认
        """
        self._confirm_callback = callback

    def add_rule(
        self,
        tool_pattern: str,
        action: str,
        args_pattern: dict[str, str] | None = None,
        priority: int = 50,
        name: str = "",
        description: str = "",
    ) -> None:
        """添加权限规则

        Args:
            tool_pattern: 工具名匹配模式 (支持通配符)
            action: 动作 (allow/deny/ask)
            args_pattern: 参数匹配模式
            priority: 优先级
            name: 规则名称
            description: 规则描述
        """
        if self._rule_engine:
            from jojo_code.security.rule import PermissionRule, RuleAction

            rule = PermissionRule(
                name=name or tool_pattern,
                tool_pattern=tool_pattern,
                action=RuleAction(action),
                args_pattern=args_pattern or {},
                priority=priority,
                description=description,
            )
            self._rule_engine.add_rule(rule)

    def check(self, tool_name: str, args: dict[str, Any]) -> PermissionResult:
        """检查工具调用权限

        检查流程:
        1. 规则引擎匹配
        2. 基础权限检查
        3. 拒绝追踪检查
        4. 用户确认回调

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            权限检查结果
        """
        # 1. 规则引擎检查
        if self._rule_engine:
            rule_action = self._rule_engine.check(tool_name, args)
            if rule_action == RuleAction.ALLOW:
                return PermissionResult(PermissionLevel.ALLOW, tool_name, args)
            elif rule_action == RuleAction.DENY:
                result = PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"规则拒绝: {tool_name}",
                )
                self._record_denial(tool_name, args, result)
                return result
            # ASK 继续往下走

        # 2. 基础权限检查
        base_result = self._base.check(tool_name, args)

        # 3. 拒绝追踪检查
        if base_result.denied and self._denial_tracker:
            self._denial_tracker.record(tool_name, args, base_result.reason or "权限被拒绝")

            if self._denial_tracker.is_threshold_exceeded(tool_name, args):
                return PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"操作被连续拒绝 {self._denial_tracker.threshold} 次，已停止请求",
                )

        # 4. 需要确认的情况
        if base_result.needs_confirm:
            if self._confirm_callback:
                # 调用用户确认回调
                confirmed = self._confirm_callback(base_result)
                if confirmed:
                    return PermissionResult(PermissionLevel.ALLOW, tool_name, args)
                else:
                    result = PermissionResult(
                        PermissionLevel.DENY,
                        tool_name,
                        args,
                        reason="用户拒绝执行",
                    )
                    self._record_denial(tool_name, args, result)
                    return result
            # 没有回调，返回需要确认
            return base_result

        return base_result

    def _record_denial(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: PermissionResult,
    ) -> None:
        """记录拒绝

        Args:
            tool_name: 工具名称
            args: 工具参数
            result: 权限结果
        """
        if self._denial_tracker:
            self._denial_tracker.record(tool_name, args, result.reason or "权限被拒绝")

    def get_rule_engine(self) -> RuleEngine | None:
        """获取规则引擎"""
        return self._rule_engine

    def get_denial_tracker(self) -> DenialTracker | None:
        """获取拒绝追踪器"""
        return self._denial_tracker

    def list_rules(self) -> list:
        """列出所有规则"""
        if self._rule_engine:
            return self._rule_engine.list_rules()
        return []

    def clear_rules(self) -> None:
        """清空所有规则"""
        if self._rule_engine:
            self._rule_engine.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = {
            "mode": self.mode.value,
            "rules_count": len(self.list_rules()),
        }

        if self._denial_tracker:
            stats["denial_tracker"] = self._denial_tracker.get_stats()

        return stats


# 全局实例
_enhanced_manager: EnhancedPermissionManager | None = None


def get_enhanced_permission_manager() -> EnhancedPermissionManager:
    """获取增强版权限管理器实例 (单例)"""
    global _enhanced_manager
    if _enhanced_manager is None:
        _enhanced_manager = EnhancedPermissionManager()
    return _enhanced_manager


def init_enhanced_permission_manager(
    config: EnhancedPermissionConfig | None = None,
) -> EnhancedPermissionManager:
    """初始化增强版权限管理器

    Args:
        config: 增强版权限配置

    Returns:
        EnhancedPermissionManager 实例
    """
    global _enhanced_manager
    _enhanced_manager = EnhancedPermissionManager(config)
    return _enhanced_manager


def set_enhanced_permission_manager(
    manager: EnhancedPermissionManager,
) -> None:
    """设置增强版权限管理器实例

    Args:
        manager: EnhancedPermissionManager 实例
    """
    global _enhanced_manager
    _enhanced_manager = manager


__all__ = [
    "EnhancedPermissionConfig",
    "EnhancedPermissionManager",
    "ConfirmCallback",
    "get_enhanced_permission_manager",
    "init_enhanced_permission_manager",
    "set_enhanced_permission_manager",
]
