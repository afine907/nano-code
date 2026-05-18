"""重试机制 - 支持指数退避"""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from jojo_code.core.error_code import ErrorCode, is_retryable_error

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """重试配置"""

    max_attempts: int = 3  # 最大尝试次数
    base_delay: float = 1.0  # 基础延迟 (秒)
    max_delay: float = 60.0  # 最大延迟 (秒)
    exponential_base: float = 2.0  # 指数退避基数
    jitter: bool = True  # 是否添加随机抖动
    retry_on: list[ErrorCode] = field(default_factory=list)  # 重试的错误码


@dataclass
class RetryStats:
    """重试统计"""

    attempts: int = 0
    successes: int = 0
    failures: int = 0
    total_delay: float = 0.0
    last_error: str | None = None


def calculate_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """计算延迟时间 (指数退避)

    Args:
        attempt: 当前尝试次数 (从 1 开始)
        config: 重试配置

    Returns:
        延迟时间 (秒)
    """
    # 指数退避
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)

    # 添加随机抖动
    if config.jitter:
        import random

        jitter = delay * 0.1 * random.random()
        delay += jitter

    return delay


def retry(
    config: RetryConfig | None = None,
    retry_codes: list[ErrorCode] | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """重试装饰器

    Args:
        config: 重试配置
        retry_codes: 需要重试的错误码列表
        on_retry: 重试回调 (exception, attempt_number)

    Returns:
        装饰器函数
    """
    config = config or RetryConfig()
    retry_codes = retry_codes or []

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            stats = RetryStats()
            last_exception: Exception | None = None

            for attempt in range(1, config.max_attempts + 1):
                stats.attempts += 1

                try:
                    result = func(*args, **kwargs)
                    stats.successes += 1
                    return result

                except Exception as e:
                    last_exception = e

                    # 检查是否需要重试
                    should_retry = False

                    # 如果指定了错误码，检查错误码
                    if retry_codes and hasattr(e, "error_code"):
                        should_retry = e.error_code in retry_codes
                    # 否则检查是否可重试
                    elif hasattr(e, "error_code"):
                        should_retry = is_retryable_error(e.error_code)

                    # 如果是最后一次尝试，或者不应该重试
                    if attempt >= config.max_attempts or not should_retry:
                        stats.failures += 1
                        raise

                    # 计算延迟
                    delay = calculate_delay(attempt, config)
                    stats.total_delay += delay
                    stats.last_error = str(e)

                    logger.warning(
                        f"重试 {func.__name__} (尝试 {attempt}/{config.max_attempts}): "
                        f"{e}, 延迟 {delay:.2f}s"
                    )

                    # 调用重试回调
                    if on_retry:
                        on_retry(e, attempt)

                    # 等待后再重试
                    time.sleep(delay)

            # 所有重试都失败
            stats.failures += 1
            raise last_exception

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            stats = RetryStats()
            last_exception: Exception | None = None

            for attempt in range(1, config.max_attempts + 1):
                stats.attempts += 1

                try:
                    result = await func(*args, **kwargs)
                    stats.successes += 1
                    return result

                except Exception as e:
                    last_exception = e

                    # 检查是否需要重试
                    should_retry = False

                    if retry_codes and hasattr(e, "error_code"):
                        should_retry = e.error_code in retry_codes
                    elif hasattr(e, "error_code"):
                        should_retry = is_retryable_error(e.error_code)

                    if attempt >= config.max_attempts or not should_retry:
                        stats.failures += 1
                        raise

                    delay = calculate_delay(attempt, config)
                    stats.total_delay += delay
                    stats.last_error = str(e)

                    logger.warning(
                        f"重试 {func.__name__} (尝试 {attempt}/{config.max_attempts}): "
                        f"{e}, 延迟 {delay:.2f}s"
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    await asyncio.sleep(delay)

            stats.failures += 1
            raise last_exception

        # 根据函数类型返回同步或异步包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper

    return decorator


class RetryContext:
    """重试上下文 - 用于手动重试控制"""

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self.stats = RetryStats()
        self._cancelled = False

    def cancel(self) -> None:
        """取消重试"""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    async def run(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """运行函数并重试

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数结果
        """
        last_exception: Exception | None = None

        for attempt in range(1, self.config.max_attempts + 1):
            self.stats.attempts += 1

            if self._cancelled:
                raise RuntimeError("重试已取消")

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                self.stats.successes += 1
                return result

            except Exception as e:
                last_exception = e

                should_retry = hasattr(e, "error_code") and is_retryable_error(e.error_code)

                if attempt >= self.config.max_attempts or not should_retry:
                    self.stats.failures += 1
                    raise

                delay = calculate_delay(attempt, self.config)
                self.stats.total_delay += delay
                self.stats.last_error = str(e)

                logger.warning(f"重试 (尝试 {attempt}): {e}")
                await asyncio.sleep(delay)

        self.stats.failures += 1
        raise last_exception


__all__ = [
    "RetryConfig",
    "RetryStats",
    "RetryContext",
    "retry",
    "calculate_delay",
]
