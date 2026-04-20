"""统一异常层次结构"""


class NanoCodeError(Exception):
    """基础异常类

    所有 nano-code 异常的基类，提供统一的错误消息和提示格式。

    Attributes:
        message: 错误消息
        hint: 解决方案提示（可选）
    """

    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        if self.hint:
            return f"{self.message}\n💡 提示: {self.hint}"
        return self.message


class ConfigError(NanoCodeError):
    """配置错误

    当配置缺失、无效或无法加载时抛出。
    """

    pass


class LLMError(NanoCodeError):
    """LLM 调用错误

    当 LLM API 调用失败时抛出。
    """

    pass


class ToolError(NanoCodeError):
    """工具执行错误

    当工具执行失败时抛出。
    """

    pass


class SecurityError(NanoCodeError):
    """安全错误

    当安全检查失败时抛出。
    """

    pass


class ValidationError(NanoCodeError):
    """验证错误

    当输入验证失败时抛出。
    """

    pass
