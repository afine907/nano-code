"""错误码和错误处理标准"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class ErrorCode(IntEnum):
    """错误码 - 与 Claude Code 保持一致

    错误码格式: XXXX
    - 1xxx: 配置错误
    - 2xxx: LLM 调用错误
    - 3xxx: 工具执行错误
    - 4xxx: 安全/权限错误
    - 5xxx: 验证错误
    - 6xxx: 网络错误
    - 7xxx: 任务执行错误
    - 9xxx: 内部错误
    """

    # 配置错误 (1xxx)
    CONFIG_NOT_FOUND = 1001
    CONFIG_INVALID = 1002
    CONFIG_PERMISSION_DENIED = 1003

    # LLM 调用错误 (2xxx)
    LLM_API_ERROR = 2001
    LLM_TIMEOUT = 2002
    LLM_RATE_LIMIT = 2003
    LLM_INVALID_RESPONSE = 2004
    LLM_MODEL_NOT_FOUND = 2005
    LLM_CONTEXT_OVERFLOW = 2006
    LLM_AUTH_FAILED = 2007

    # 工具执行错误 (3xxx)
    TOOL_NOT_FOUND = 3001
    TOOL_EXECUTION_FAILED = 3002
    TOOL_TIMEOUT = 3003
    TOOL_PERMISSION_DENIED = 3004
    TOOL_INVALID_INPUT = 3005
    TOOL_OUTPUT_TOO_LARGE = 3006

    # 安全/权限错误 (4xxx)
    SECURITY_DENIED = 4001
    SECURITY_RISK_HIGH = 4002
    SECURITY_PATH_FORBIDDEN = 4003
    SECURITY_COMMAND_FORBIDDEN = 4004

    # 验证错误 (5xxx)
    VALIDATION_FAILED = 5001
    VALIDATION_TYPE_ERROR = 5002
    VALIDATION_CONSTRAINT = 5003

    # 网络错误 (6xxx)
    NETWORK_ERROR = 6001
    NETWORK_TIMEOUT = 6002
    NETWORK_CONNECTION_REFUSED = 6003

    # 任务执行错误 (7xxx)
    TASK_NOT_FOUND = 7001
    TASK_FAILED = 7002
    TASK_TIMEOUT = 7003
    TASK_CANCELLED = 7004
    TASK_MAX_RETRIES_EXCEEDED = 7005

    # 内部错误 (9xxx)
    INTERNAL_ERROR = 9001
    NOT_IMPLEMENTED = 9002
    UNEXPECTED_ERROR = 9003


@dataclass
class ErrorContext:
    """错误上下文"""

    code: ErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    hint: str | None = None
    source: str | None = None  # 错误来源模块
    correlation_id: str | None = None  # 用于关联日志


class ErrorCategory:
    """错误类别映射"""

    _CATEGORIES = {
        ErrorCode.CONFIG_NOT_FOUND: "config",
        ErrorCode.CONFIG_INVALID: "config",
        ErrorCode.LLM_API_ERROR: "llm",
        ErrorCode.LLM_TIMEOUT: "llm",
        ErrorCode.TOOL_NOT_FOUND: "tool",
        ErrorCode.TOOL_EXECUTION_FAILED: "tool",
        ErrorCode.SECURITY_DENIED: "security",
        ErrorCode.SECURITY_RISK_HIGH: "security",
        ErrorCode.VALIDATION_FAILED: "validation",
        ErrorCode.NETWORK_ERROR: "network",
        ErrorCode.TASK_FAILED: "task",
        ErrorCode.INTERNAL_ERROR: "internal",
    }

    @classmethod
    def get(cls, code: ErrorCode) -> str:
        """获取错误类别"""
        return cls._CATEGORIES.get(code, "unknown")

    @classmethod
    def is_retryable(cls, code: ErrorCode) -> bool:
        """是否可重试"""
        retryable_codes = {
            ErrorCode.LLM_API_ERROR,
            ErrorCode.LLM_TIMEOUT,
            ErrorCode.LLM_RATE_LIMIT,
            ErrorCode.NETWORK_ERROR,
            ErrorCode.NETWORK_TIMEOUT,
            ErrorCode.TASK_FAILED,
        }
        return code in retryable_codes


# 错误消息模板
ERROR_MESSAGES = {
    ErrorCode.CONFIG_NOT_FOUND: "配置文件未找到",
    ErrorCode.CONFIG_INVALID: "配置文件格式无效",
    ErrorCode.LLM_API_ERROR: "LLM API 调用失败",
    ErrorCode.LLM_TIMEOUT: "LLM 请求超时",
    ErrorCode.LLM_RATE_LIMIT: "LLM 请求频率超限",
    ErrorCode.LLM_INVALID_RESPONSE: "LLM 响应格式无效",
    ErrorCode.LLM_MODEL_NOT_FOUND: "LLM 模型未找到",
    ErrorCode.LLM_CONTEXT_OVERFLOW: "上下文长度超出限制",
    ErrorCode.TOOL_NOT_FOUND: "工具未找到",
    ErrorCode.TOOL_EXECUTION_FAILED: "工具执行失败",
    ErrorCode.TOOL_TIMEOUT: "工具执行超时",
    ErrorCode.TOOL_PERMISSION_DENIED: "工具权限被拒绝",
    ErrorCode.SECURITY_DENIED: "安全检查未通过",
    ErrorCode.SECURITY_RISK_HIGH: "操作风险过高",
    ErrorCode.VALIDATION_FAILED: "输入验证失败",
    ErrorCode.NETWORK_ERROR: "网络请求失败",
    ErrorCode.TASK_NOT_FOUND: "任务未找到",
    ErrorCode.TASK_FAILED: "任务执行失败",
    ErrorCode.TASK_TIMEOUT: "任务执行超时",
    ErrorCode.INTERNAL_ERROR: "内部错误",
}


def get_error_message(code: ErrorCode) -> str:
    """获取错误码对应的默认消息

    Args:
        code: 错误码

    Returns:
        错误消息
    """
    return ERROR_MESSAGES.get(code, "未知错误")


def is_retryable_error(code: ErrorCode) -> bool:
    """检查错误是否可重试

    Args:
        code: 错误码

    Returns:
        是否可重试
    """
    return ErrorCategory.is_retryable(code)


__all__ = [
    "ErrorCode",
    "ErrorContext",
    "ErrorCategory",
    "ERROR_MESSAGES",
    "get_error_message",
    "is_retryable_error",
]
