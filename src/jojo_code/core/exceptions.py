"""统一异常层次结构 - 带错误码"""

from jojo_code.core.error_code import ErrorCode, ErrorContext


class JojoCodeError(Exception):
    """基础异常类

    所有 jojo-code 异常的基类，提供统一的错误消息和提示格式。

    Attributes:
        message: 错误消息
        hint: 解决方案提示（可选）
        error_code: 错误码
        context: 错误上下文
    """

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        error_code: ErrorCode | None = None,
        context: ErrorContext | None = None,
    ):
        self.message = message
        self.hint = hint
        self.error_code = error_code or ErrorCode.INTERNAL_ERROR
        self.context = context
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        parts = [f"[{self.error_code:d}] {self.message}"]
        if self.hint:
            parts.append(f"💡 提示: {self.hint}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "error_code": int(self.error_code),
            "message": self.message,
            "hint": self.hint,
            "context": self.context.details if self.context else None,
        }


class ConfigError(JojoCodeError):
    """配置错误

    当配置缺失、无效或无法加载时抛出。
    """

    def __init__(self, message: str, hint: str | None = None, **kwargs):
        super().__init__(
            message,
            hint=hint,
            error_code=ErrorCode.CONFIG_INVALID,
            **kwargs,
        )


class LLMError(JojoCodeError):
    """LLM 调用错误

    当 LLM API 调用失败时抛出。
    """

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        error_code: ErrorCode | None = None,
        **kwargs,
    ):
        super().__init__(
            message,
            hint=hint,
            error_code=error_code or ErrorCode.LLM_API_ERROR,
            **kwargs,
        )


class ToolError(JojoCodeError):
    """工具执行错误

    当工具执行失败时抛出。
    """

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        error_code: ErrorCode | None = None,
        **kwargs,
    ):
        super().__init__(
            message,
            hint=hint,
            error_code=error_code or ErrorCode.TOOL_EXECUTION_FAILED,
            **kwargs,
        )


class SecurityError(JojoCodeError):
    """安全错误

    当安全检查失败时抛出。
    """

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        error_code: ErrorCode | None = None,
        **kwargs,
    ):
        super().__init__(
            message,
            hint=hint,
            error_code=error_code or ErrorCode.SECURITY_DENIED,
            **kwargs,
        )


class ValidationError(JojoCodeError):
    """验证错误

    当输入验证失败时抛出。
    """

    def __init__(self, message: str, hint: str | None = None, **kwargs):
        super().__init__(
            message,
            hint=hint,
            error_code=ErrorCode.VALIDATION_FAILED,
            **kwargs,
        )


class TaskError(JojoCodeError):
    """任务执行错误

    当任务执行失败时抛出。
    """

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        error_code: ErrorCode | None = None,
        **kwargs,
    ):
        super().__init__(
            message,
            hint=hint,
            error_code=error_code or ErrorCode.TASK_FAILED,
            **kwargs,
        )


class NetworkError(JojoCodeError):
    """网络错误

    当网络请求失败时抛出。
    """

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        error_code: ErrorCode | None = None,
        **kwargs,
    ):
        super().__init__(
            message,
            hint=hint,
            error_code=error_code or ErrorCode.NETWORK_ERROR,
            **kwargs,
        )
