"""安全模块 - 工具权限控制"""

from jojo_code.security.audit import AuditEvent, AuditLogger, AuditQuery
from jojo_code.security.command_guard import CommandGuard
from jojo_code.security.denial import AdaptivePermissionMixin, DenialRecord, DenialTracker
from jojo_code.security.enhanced import (
    EnhancedPermissionConfig,
    EnhancedPermissionManager,
    get_enhanced_permission_manager,
    init_enhanced_permission_manager,
    set_enhanced_permission_manager,
)
from jojo_code.security.guards import BaseGuard
from jojo_code.security.manager import (
    PermissionConfig,
    PermissionManager,
    get_permission_manager,
    init_permission_manager,
    set_permission_manager,
)
from jojo_code.security.modes import PermissionMode, RiskLevel
from jojo_code.security.path_guard import PathGuard
from jojo_code.security.permission import PermissionLevel, PermissionResult
from jojo_code.security.risk import RISK_PATTERNS, assess_risk, get_risk_description
from jojo_code.security.rule import (
    PermissionRule,
    RuleAction,
    RuleEngine,
    RuleFactory,
    RuleMatchType,
)

__all__ = [
    # 权限级别和结果
    "PermissionLevel",
    "PermissionResult",
    # 权限模式和风险等级
    "PermissionMode",
    "RiskLevel",
    # 风险评估
    "assess_risk",
    "get_risk_description",
    "RISK_PATTERNS",
    # 审计日志
    "AuditEvent",
    "AuditLogger",
    "AuditQuery",
    # 守卫
    "BaseGuard",
    "PathGuard",
    "CommandGuard",
    # 管理器
    "PermissionConfig",
    "PermissionManager",
    "get_permission_manager",
    "set_permission_manager",
    "init_permission_manager",
    # 规则引擎 (新增)
    "RuleEngine",
    "PermissionRule",
    "RuleAction",
    "RuleMatchType",
    "RuleFactory",
    # 拒绝追踪 (新增)
    "DenialTracker",
    "DenialRecord",
    "AdaptivePermissionMixin",
    # 增强版管理器 (新增)
    "EnhancedPermissionManager",
    "EnhancedPermissionConfig",
    "get_enhanced_permission_manager",
    "init_enhanced_permission_manager",
    "set_enhanced_permission_manager",
]
