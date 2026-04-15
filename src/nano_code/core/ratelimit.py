"""
Nano Code - 限流和配额管理
提供 API 限流、用户配额管理功能
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """超过速率限制"""

    pass


class QuotaError(Exception):
    """超过配额"""

    pass


class LimitAlgorithm(Enum):
    """限流算法"""

    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    requests: int  # 允许的请求数
    window: int  # 时间窗口（秒）
    algorithm: LimitAlgorithm = LimitAlgorithm.TOKEN_BUCKET


@dataclass
class QuotaConfig:
    """配额配置"""

    limit: int
    period: int  # 周期（秒）
    unit: str = "requests"  # requests, tokens, storage


@dataclass
class UsageRecord:
    """使用记录"""

    timestamp: datetime
    amount: int
    metadata: dict = field(default_factory=dict)


class TokenBucket:
    """令牌桶算法"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # 每秒补充的令牌数
        self._tokens = float(capacity)
        self._last_refill = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """消耗令牌"""
        async with self._lock:
            await self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    async def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    @property
    def available_tokens(self) -> float:
        return self._tokens


class LeakyBucket:
    """漏桶算法"""

    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate  # 每秒漏出的请求数
        self._level = 0.0
        self._last_leak = time.time()
        self._lock = asyncio.Lock()

    async def add(self) -> bool:
        """添加请求"""
        async with self._lock:
            await self._leak()

            if self._level < self.capacity:
                self._level += 1
                return True

            return False

    async def _leak(self) -> None:
        """漏水"""
        now = time.time()
        elapsed = now - self._last_leak
        self._level = max(0, self._level - elapsed * self.leak_rate)
        self._last_leak = now

    @property
    def level(self) -> float:
        return self._level


class SlidingWindow:
    """滑动窗口算法"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: deque = deque()
        self._lock = asyncio.Lock()

    async def allow(self) -> bool:
        """检查是否允许"""
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # 移除过期的请求
            while self._requests and self._requests[0] < cutoff:
                self._requests.popleft()

            if len(self._requests) < self.max_requests:
                self._requests.append(now)
                return True

            return False

    @property
    def current_count(self) -> int:
        return len(self._requests)


class FixedWindow:
    """固定窗口算法"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._window_start = time.time()
        self._count = 0
        self._lock = asyncio.Lock()

    async def allow(self) -> bool:
        """检查是否允许"""
        async with self._lock:
            now = time.time()

            # 窗口过期，重置
            if now - self._window_start >= self.window_seconds:
                self._window_start = now
                self._count = 0

            if self._count < self.max_requests:
                self._count += 1
                return True

            return False


class RateLimiter:
    """速率限制器"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._limiter = self._create_limiter()

    def _create_limiter(self):
        """创建限流器"""
        if self.config.algorithm == LimitAlgorithm.TOKEN_BUCKET:
            refill_rate = self.config.requests / self.config.window
            return TokenBucket(self.config.requests, refill_rate)

        elif self.config.algorithm == LimitAlgorithm.LEAKY_BUCKET:
            leak_rate = self.config.requests / self.config.window
            return LeakyBucket(self.config.requests, leak_rate)

        elif self.config.algorithm == LimitAlgorithm.SLIDING_WINDOW:
            return SlidingWindow(self.config.requests, self.config.window)

        elif self.config.algorithm == LimitAlgorithm.FIXED_WINDOW:
            return FixedWindow(self.config.requests, self.config.window)

        else:
            return SlidingWindow(self.config.requests, self.config.window)

    async def check(self) -> bool:
        """检查是否允许请求"""
        if isinstance(self._limiter, TokenBucket):
            return await self._limiter.consume()
        elif isinstance(self._limiter, LeakyBucket):
            return await self._limiter.add()
        else:
            return await self._limiter.allow()

    async def acquire(self, blocking: bool = True) -> None:
        """获取许可"""
        if blocking:
            while not await self.check():
                await asyncio.sleep(0.1)
        else:
            if not await self.check():
                raise RateLimitError("Rate limit exceeded")


class QuotaManager:
    """配额管理器"""

    def __init__(self):
        self._quotas: dict[str, QuotaConfig] = {}
        self._usage: dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._lock = asyncio.Lock()

    def register_quota(self, name: str, config: QuotaConfig) -> None:
        """注册配额"""
        self._quotas[name] = config

    async def check_quota(self, quota_name: str, amount: int = 1) -> bool:
        """检查配额"""
        if quota_name not in self._quotas:
            return True

        config = self._quotas[quota_name]

        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=config.period)

            # 清理过期记录
            usage = self._usage[quota_name]
            while usage and usage[0].timestamp < cutoff:
                usage.popleft()

            # 计算当前使用量
            current = sum(r.amount for r in usage)

            return current + amount <= config.limit

    async def consume_quota(
        self, quota_name: str, amount: int = 1, metadata: dict | None = None
    ) -> None:
        """消耗配额"""
        if quota_name not in self._quotas:
            return

        if not await self.check_quota(quota_name, amount):
            raise QuotaError(f"Quota exceeded: {quota_name}")

        async with self._lock:
            record = UsageRecord(timestamp=datetime.now(), amount=amount, metadata=metadata or {})
            self._usage[quota_name].append(record)

    async def get_usage(self, quota_name: str, period: int | None = None) -> int:
        """获取使用量"""
        if quota_name not in self._quotas:
            return 0

        config = self._quotas[quota_name]
        period = period or config.period

        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=period)

            usage = self._usage[quota_name]
            return sum(r.amount for r in usage if r.timestamp >= cutoff)

    async def get_remaining(self, quota_name: str) -> int:
        """获取剩余配额"""
        if quota_name not in self._quotas:
            return -1  # 无限制

        config = self._quotas[quota_name]
        current = await self.get_usage(quota_name)

        return max(0, config.limit - current)


class IPRateLimiter:
    """基于 IP 的速率限制器"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._limiters: dict[str, RateLimiter] = {}
        self._lock = asyncio.Lock()

    async def check(self, ip: str) -> bool:
        """检查 IP"""
        async with self._lock:
            if ip not in self._limiters:
                self._limiters[ip] = RateLimiter(self.config)

            return await self._limiters[ip].check()

    async def block_ip(self, ip: str, duration: int = 300) -> None:
        """封禁 IP"""
        async with self._lock:
            # 创建一个永远拒绝的限流器
            self._limiters[ip] = RateLimiter(RateLimitConfig(requests=0, window=1))

        # 自动解封
        asyncio.create_task(self._unblock_ip(ip, duration))

    async def _unblock_ip(self, ip: str, duration: int) -> None:
        """解封 IP"""
        await asyncio.sleep(duration)

        async with self._lock:
            if ip in self._limiters:
                del self._limiters[ip]


class UserRateLimiter:
    """基于用户的速率限制器"""

    def __init__(self):
        self._limiters: dict[str, RateLimiter] = {}
        self._lock = asyncio.Lock()

    async def create_limiter(self, user_id: str, config: RateLimitConfig) -> None:
        """为用户创建限流器"""
        async with self._lock:
            self._limiters[user_id] = RateLimiter(config)

    async def check(self, user_id: str) -> bool:
        """检查用户"""
        async with self._lock:
            if user_id not in self._limiters:
                # 默认限流
                self._limiters[user_id] = RateLimiter(RateLimitConfig(requests=60, window=60))

            return await self._limiters[user_id].check()

    async def set_limit(self, user_id: str, config: RateLimitConfig) -> None:
        """设置用户限制"""
        async with self._lock:
            self._limiters[user_id] = RateLimiter(config)


# 装饰器：速率限制
def rate_limit(config: RateLimitConfig):
    """速率限制装饰器"""
    limiter = RateLimiter(config)

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            await limiter.acquire(blocking=True)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 装饰器：配额限制
def quota_limit(quota_name: str, amount: int = 1):
    """配额限制装饰器"""

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            manager = get_quota_manager()
            await manager.consume_quota(quota_name, amount)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 全局实例
_quota_manager: QuotaManager | None = None
_user_rate_limiter: UserRateLimiter | None = None


def get_quota_manager() -> QuotaManager:
    """获取全局配额管理器"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager


def get_user_rate_limiter() -> UserRateLimiter:
    """获取全局用户限流器"""
    global _user_rate_limiter
    if _user_rate_limiter is None:
        _user_rate_limiter = UserRateLimiter()
    return _user_rate_limiter
