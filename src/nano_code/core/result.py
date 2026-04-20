"""类型安全的 Result 类型

用于函数式错误处理，避免异常抛出。
"""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T]):
    """Result 类型，表示可能成功或失败的操作结果

    使用示例:
        >>> result = Result.ok(42)
        >>> result.is_ok()
        True
        >>> result.unwrap()
        42

        >>> result = Result.err(ConfigError("配置缺失"))
        >>> result.is_err()
        True
        >>> result.unwrap_or(0)
        0
    """

    def __init__(self, value: T | None = None, error: Exception | None = None):
        self._value = value
        self._error = error

    def is_ok(self) -> bool:
        """检查是否成功"""
        return self._error is None

    def is_err(self) -> bool:
        """检查是否失败"""
        return self._error is not None

    def unwrap(self) -> T:
        """获取成功值，如果失败则抛出异常

        Raises:
            Exception: 如果 Result 是错误状态
        """
        if self._error is not None:
            raise self._error
        return self._value

    def unwrap_or(self, default: T) -> T:
        """获取成功值，如果失败则返回默认值"""
        if self._error is not None:
            return default
        return self._value

    def unwrap_err(self) -> Exception | None:
        """获取错误，如果成功则返回 None"""
        return self._error

    def map(self, f: Callable[[T], Any]) -> "Result":
        """映射成功值"""
        if self._error is not None:
            return self
        try:
            return Result.ok(f(self._value))
        except Exception as e:
            return Result.err(e)

    def and_then(self, f: Callable[[T], "Result"]) -> "Result":
        """链式操作，如果成功则调用 f"""
        if self._error is not None:
            return self
        return f(self._value)

    def or_else(self, f: Callable[[Exception], "Result"]) -> "Result":
        """如果失败则调用 f"""
        if self._error is None:
            return self
        return f(self._error)

    @staticmethod
    def ok(value: T) -> "Result[T]":
        """创建成功的 Result"""
        return Result(value=value)

    @staticmethod
    def err(error: Exception) -> "Result[T]":
        """创建失败的 Result"""
        return Result(error=error)

    def __repr__(self) -> str:
        if self._error is None:
            return f"Result.ok({self._value!r})"
        return f"Result.err({self._error!r})"
