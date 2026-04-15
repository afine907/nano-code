"""
Nano Code - 分布式锁和同步机制
提供分布式环境下的锁、信号量、Barrier 等同步原语
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class LockError(Exception):
    """锁错误"""

    pass


class LockTimeoutError(LockError):
    """锁超时错误"""

    pass


class Lock:
    """异步锁"""

    def __init__(self, name: str, timeout: float = 30.0):
        self.name = name
        self.timeout = timeout
        self._locked = False
        self._holder: str | None = None
        self._queue: list[asyncio.Future] = []
        self._lock = asyncio.Lock()
        self._created_at = time.time()
        self._acquired_at: float | None = None

    async def acquire(self, holder: str | None = None) -> bool:
        """获取锁"""
        async with self._lock:
            if not self._locked:
                self._locked = True
                self._holder = holder or str(uuid.uuid4())
                self._acquired_at = time.time()
                return True

            # 创建等待者
            future = asyncio.Future()
            self._queue.append(future)

        # 等待锁
        try:
            await asyncio.wait_for(future, timeout=self.timeout)
            async with self._lock:
                self._locked = True
                self._holder = holder or str(uuid.uuid4())
                self._acquired_at = time.time()
            return True
        except TimeoutError:
            async with self._lock:
                if future in self._queue:
                    self._queue.remove(future)
            raise LockTimeoutError(f"Lock timeout: {self.name}") from None

    async def release(self) -> None:
        """释放锁"""
        async with self._lock:
            if not self._locked:
                return

            self._locked = False
            self._holder = None
            self._acquired_at = None

            # 唤醒下一个等待者
            if self._queue:
                future = self._queue.pop(0)
                if not future.done():
                    future.set_result(True)

    @property
    def is_locked(self) -> bool:
        return self._locked

    @property
    def holder(self) -> str | None:
        return self._holder

    @property
    def waiters(self) -> int:
        return len(self._queue)

    @asynccontextmanager
    async def __aenter__(self):
        await self.acquire()
        try:
            yield self
        finally:
            await self.release()


class RWLock:
    """读写锁"""

    def __init__(self, name: str):
        self.name = name
        self._readers: set[str] = set()
        self._writers: list[asyncio.Future] = []
        self._writer_active = False
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def read_lock(self, reader_id: str | None = None):
        """获取读锁"""
        reader_id = reader_id or str(uuid.uuid4())

        async with self._lock:
            while self._writer_active or self._writers:
                if self._writers:
                    # 有写者等待，优先处理
                    future = asyncio.Future()
                    self._writers.append(future)
                    break
                else:
                    future = asyncio.Future()
                    self._readers.add(future)
                    break

        if "future" in locals():
            try:
                await asyncio.wait_for(future, timeout=30.0)
            finally:
                async with self._lock:
                    self._readers.discard(future)

        try:
            yield
        finally:
            async with self._lock:
                self._readers.discard(reader_id)

    @asynccontextmanager
    async def write_lock(self, writer_id: str | None = None):
        """获取写锁"""
        writer_id = writer_id or str(uuid.uuid4())

        async with self._lock:
            future = asyncio.Future()
            self._writers.append(future)
            self._writer_active = False

        try:
            await asyncio.wait_for(future, timeout=30.0)
            async with self._lock:
                self._writer_active = True
            yield
        finally:
            async with self._lock:
                self._writer_active = False
                if self._writers:
                    next_future = self._writers.pop(0)
                    if not next_future.done():
                        next_future.set_result(True)


class Semaphore:
    """信号量"""

    def __init__(self, name: str, value: int = 1):
        self.name = name
        self._value = value
        self._max = value
        self._waiters: list[asyncio.Future] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """获取信号量"""
        async with self._lock:
            if self._value > 0:
                self._value -= 1
                return True

            # 等待
            future = asyncio.Future()
            self._waiters.append(future)

        await future
        return True

    async def release(self) -> None:
        """释放信号量"""
        async with self._lock:
            if self._waiters:
                # 唤醒一个等待者
                future = self._waiters.pop(0)
                if not future.done():
                    future.set_result(True)
            elif self._value < self._max:
                self._value += 1

    @property
    def available(self) -> int:
        return self._value

    @asynccontextmanager
    async def __aenter__(self):
        await self.acquire()
        try:
            yield self
        finally:
            await self.release()


class Barrier:
    """屏障 - 阻塞直到指定数量的协程到达"""

    def __init__(self, name: str, parties: int):
        self.name = name
        self.parties = parties
        self._count = 0
        self._waiters: list[asyncio.Future] = []
        self._generation = 0
        self._lock = asyncio.Lock()

    async def wait(self) -> int:
        """等待所有参与者"""
        async with self._lock:
            gen = self._generation
            self._count += 1

            if self._count >= self.parties:
                # 唤醒所有等待者
                self._count = 0
                self._generation += 1

                for future in self._waiters:
                    if not future.done():
                        future.set_result(self._generation)

                self._waiters.clear()
                return self._generation

            # 等待
            future = asyncio.Future()
            self._waiters.append(future)

        await future
        return gen

    @property
    def parties_arrived(self) -> int:
        return self._count

    @property
    def waiting(self) -> int:
        return len(self._waiters)


class Condition:
    """条件变量"""

    def __init__(self, name: str):
        self.name = name
        self._waiters: list[asyncio.Future] = []
        self._lock = asyncio.Lock()

    async def wait(self, predicate: Callable[[], bool] | None = None):
        """等待条件"""
        async with self._lock:
            if predicate and predicate():
                return

            future = asyncio.Future()
            self._waiters.append(future)

        await future

    async def notify(self) -> int:
        """唤醒一个等待者"""
        async with self._lock:
            if self._waiters:
                future = self._waiters.pop(0)
                if not future.done():
                    future.set_result(True)
                return 1
        return 0

    async def notify_all(self) -> int:
        """唤醒所有等待者"""
        async with self._lock:
            count = len(self._waiters)
            for future in self._waiters:
                if not future.done():
                    future.set_result(True)
            self._waiters.clear()
            return count


class Event:
    """事件 (一次性)"""

    def __init__(self, name: str):
        self.name = name
        self._set = False
        self._waiters: list[asyncio.Future] = []
        self._lock = asyncio.Lock()

    async def wait(self, timeout: float | None = None) -> bool:
        """等待事件"""
        async with self._lock:
            if self._set:
                return True

            future = asyncio.Future()
            self._waiters.append(future)

        try:
            if timeout:
                await asyncio.wait_for(future, timeout=timeout)
            else:
                await future
            return True
        except TimeoutError:
            async with self._lock:
                if future in self._waiters:
                    self._waiters.remove(future)
            return False

    def set(self) -> int:
        """设置事件"""
        self._set = True
        count = 0
        for future in self._waiters:
            if not future.done():
                future.set_result(True)
                count += 1
        self._waiters.clear()
        return count

    def clear(self) -> None:
        """清除事件"""
        self._set = False

    @property
    def is_set(self) -> bool:
        return self._set


class Counter:
    """计数器"""

    def __init__(self, name: str, initial: int = 0):
        self.name = name
        self._value = initial
        self._lock = asyncio.Lock()

    async def increment(self, delta: int = 1) -> int:
        """递增"""
        async with self._lock:
            self._value += delta
            return self._value

    async def decrement(self, delta: int = 1) -> int:
        """递减"""
        async with self._lock:
            self._value -= delta
            return self._value

    async def get(self) -> int:
        """获取值"""
        async with self._lock:
            return self._value

    async def set(self, value: int) -> None:
        """设置值"""
        async with self._lock:
            self._value = value


# 分布式锁管理器（支持 Redis 后端）
class DistributedLockManager:
    """分布式锁管理器"""

    def __init__(self, use_redis: bool = False, redis_url: str = "redis://localhost:6379"):
        self.use_redis = use_redis
        self.redis_url = redis_url
        self._local_locks: dict[str, Lock] = {}
        self._locks_lock = asyncio.Lock()
        self._redis = None

        if use_redis:
            self._init_redis()

    def _init_redis(self):
        """初始化 Redis 连接"""
        try:
            import aioredis

            self._redis = aioredis.from_url(self.redis_url)
        except ImportError:
            logger.warning("aioredis not installed, using local locks only")
            self.use_redis = False

    async def get_lock(self, name: str, timeout: float = 30.0, expire: float = 60.0) -> Lock:
        """获取锁"""
        if self.use_redis and self._redis:
            return await self._get_redis_lock(name, timeout, expire)
        else:
            return await self._get_local_lock(name, timeout)

    async def _get_local_lock(self, name: str, timeout: float) -> Lock:
        """获取本地锁"""
        async with self._locks_lock:
            if name not in self._local_locks:
                self._local_locks[name] = Lock(name, timeout)
            return self._local_locks[name]

    async def _get_redis_lock(self, name: str, timeout: float, expire: float) -> "RedisLock":
        """获取 Redis 锁"""
        from .cache import get_redis_cache

        return RedisLock(name, get_redis_cache()._get_redis(), timeout, expire)

    @asynccontextmanager
    async def lock(self, name: str, **kwargs):
        """锁上下文管理器"""
        lock = await self.get_lock(name, **kwargs)
        try:
            await lock.acquire()
            yield lock
        finally:
            await lock.release()


class RedisLock:
    """基于 Redis 的分布式锁"""

    def __init__(self, name: str, redis, timeout: float = 30.0, expire: float = 60.0):
        self.name = f"lock:{name}"
        self.redis = redis
        self.timeout = timeout
        self.expire = expire
        self._locked = False
        self._holder: str | None = None
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """获取锁"""
        holder = str(uuid.uuid4())

        # 尝试设置锁
        acquired = await self.redis.set(self.name, holder, nx=True, ex=int(self.expire))

        if acquired:
            self._locked = True
            self._holder = holder
            return True

        # 等待锁释放
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            await asyncio.sleep(0.1)

            acquired = await self.redis.set(self.name, holder, nx=True, ex=int(self.expire))

            if acquired:
                self._locked = True
                self._holder = holder
                return True

        raise LockTimeoutError(f"Redis lock timeout: {self.name}")

    async def release(self) -> None:
        """释放锁"""
        if not self._locked:
            return

        # 使用 Lua 脚本确保原子性删除
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        await self.redis.eval(script, 1, self.name, self._holder)
        self._locked = False
        self._holder = None

    @property
    def is_locked(self) -> bool:
        return self._locked


# 全局同步原语管理器
_sync_managers: dict[str, "DistributedLockManager"] = {}


def get_sync_manager(name: str = "default", **kwargs) -> DistributedLockManager:
    """获取同步管理器"""
    global _sync_managers

    if name not in _sync_managers:
        _sync_managers[name] = DistributedLockManager(**kwargs)

    return _sync_managers[name]
