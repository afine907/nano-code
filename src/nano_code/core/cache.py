"""
Nano Code - 缓存系统
提供多层缓存：内存、磁盘、分布式缓存
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

import aioredis

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheBackend(ABC):
    """缓存后端基类"""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass


class MemoryCache(CacheBackend):
    """内存缓存 (LRU)"""

    def __init__(self, max_size: int = 1000, max_ttl: int = 3600):
        self.max_size = max_size
        self.max_ttl = max_ttl
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # 检查过期
            if entry["expires_at"] and time.time() > entry["expires_at"]:
                del self._cache[key]
                return None

            # 移到末尾 (LRU)
            self._cache.move_to_end(key)

            return entry["value"]

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        async with self._lock:
            # LRU 淘汰
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            expires_at = None
            if ttl:
                expires_at = time.time() + ttl
            elif self.max_ttl:
                expires_at = time.time() + self.max_ttl

            self._cache[key] = {"value": value, "expires_at": expires_at, "created_at": time.time()}

            # 移到末尾
            self._cache.move_to_end(key)

    async def delete(self, key: str) -> None:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]

    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def keys(self, pattern: str = "*") -> list[str]:
        """获取匹配的 keys"""
        import fnmatch

        async with self._lock:
            return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]


class DiskCache(CacheBackend):
    """磁盘缓存"""

    def __init__(self, cache_dir: Path, max_size_mb: int = 1000):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._lock = asyncio.Lock()

        cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """获取文件路径"""
        hashed = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{hashed}.cache"

    async def get(self, key: str) -> Any | None:
        path = self._get_path(key)

        if not path.exists():
            return None

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            # 检查过期
            if data.get("expires_at") and time.time() > data["expires_at"]:
                await self.delete(key)
                return None

            return data["value"]
        except Exception as e:
            logger.error(f"Disk cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        path = self._get_path(key)

        expires_at = None
        if ttl:
            expires_at = time.time() + ttl

        data = {"value": value, "expires_at": expires_at, "created_at": time.time()}

        try:
            # 写入临时文件然后重命名（原子操作）
            temp_path = path.with_suffix(".tmp")
            with open(temp_path, "wb") as f:
                pickle.dump(data, f)

            temp_path.rename(path)

            # 检查大小并清理
            await self._cleanup_if_needed()
        except Exception as e:
            logger.error(f"Disk cache set error: {e}")

    async def delete(self, key: str) -> None:
        path = self._get_path(key)
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None

    async def clear(self) -> None:
        async with self._lock:
            for path in self.cache_dir.glob("*.cache"):
                path.unlink()

    async def _cleanup_if_needed(self) -> None:
        """清理过期或过大的缓存"""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.cache"))

        if total_size > self.max_size_bytes:
            # 删除最老的文件
            files = sorted(self.cache_dir.glob("*.cache"), key=lambda f: f.stat().st_mtime)

            while total_size > self.max_size_bytes * 0.8 and files:
                oldest = files.pop(0)
                total_size -= oldest.stat().st_size
                oldest.unlink()


class RedisCache(CacheBackend):
    """Redis 缓存"""

    def __init__(self, url: str = "redis://localhost:6379"):
        self.url = url
        self._redis: aioredis.Redis | None = None
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> aioredis.Redis:
        """获取 Redis 连接"""
        if self._redis is None:
            self._redis = await aioredis.from_url(self.url)
        return self._redis

    async def get(self, key: str) -> Any | None:
        try:
            redis = await self._get_redis()
            value = await redis.get(key)

            if value is None:
                return None

            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            redis = await self._get_redis()
            serialized = json.dumps(value)

            if ttl:
                await redis.setex(key, ttl, serialized)
            else:
                await redis.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")

    async def delete(self, key: str) -> None:
        try:
            redis = await self._get_redis()
            await redis.delete(key)
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")

    async def exists(self, key: str) -> bool:
        try:
            redis = await self._get_redis()
            return await redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis cache exists error: {e}")
            return False

    async def clear(self) -> None:
        try:
            redis = await self._get_redis()
            await redis.flushdb()
        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")


class MultiLevelCache:
    """多级缓存 (L1: 内存, L2: 磁盘)"""

    def __init__(
        self,
        memory_cache: MemoryCache | None = None,
        disk_cache: DiskCache | None = None,
        redis_cache: RedisCache | None = None,
    ):
        self.l1 = memory_cache or MemoryCache()
        self.l2 = disk_cache
        self.l3 = redis_cache

    async def get(self, key: str) -> Any | None:
        # L1 内存缓存
        value = await self.l1.get(key)
        if value is not None:
            return value

        # L2 磁盘缓存
        if self.l2:
            value = await self.l2.get(key)
            if value is not None:
                # 回填 L1
                await self.l1.set(key, value)
                return value

        # L3 Redis 缓存
        if self.l3:
            value = await self.l3.get(key)
            if value is not None:
                # 回填 L1
                await self.l1.set(key, value)
                return value

        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        # 写入所有层级
        await self.l1.set(key, value, ttl)

        if self.l2:
            await self.l2.set(key, value, ttl)

        if self.l3:
            await self.l3.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        await self.l1.delete(key)

        if self.l2:
            await self.l2.delete(key)

        if self.l3:
            await self.l3.delete(key)

    async def clear(self) -> None:
        await self.l1.clear()

        if self.l2:
            await self.l2.clear()

        if self.l3:
            await self.l3.clear()


@dataclass
class CacheStats:
    """缓存统计"""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0


class CachedFunction(Generic[T]):
    """缓存函数装饰器"""

    def __init__(
        self,
        func: Callable[..., T],
        cache: CacheBackend,
        key_builder: Callable | None = None,
        ttl: int | None = None,
    ):
        self.func = func
        self.cache = cache
        self.key_builder = key_builder or (
            lambda *args, **kwargs: f"{func.__name__}:{str(args)}:{str(kwargs)}"
        )
        self.ttl = ttl
        self.stats = CacheStats()

    async def __call__(self, *args, **kwargs) -> T:
        key = self.key_builder(*args, **kwargs)

        # 尝试从缓存获取
        cached = await self.cache.get(key)
        if cached is not None:
            self.stats.hits += 1
            return cached

        self.stats.misses += 1

        # 执行函数
        if asyncio.iscoroutinefunction(self.func):
            result = await self.func(*args, **kwargs)
        else:
            result = self.func(*args, **kwargs)

        # 存入缓存
        await self.cache.set(key, result, self.ttl)
        self.stats.sets += 1

        return result

    def invalidate(self, *args, **kwargs) -> None:
        """使缓存失效"""
        key = self.key_builder(*args, **kwargs)
        asyncio.create_task(self.cache.delete(key))
        self.stats.deletes += 1

    def get_stats(self) -> CacheStats:
        return self.stats


def cached(cache: CacheBackend, key_builder: Callable | None = None, ttl: int | None = None):
    """缓存装饰器"""

    def decorator(func: Callable[..., T]) -> CachedFunction[T]:
        return CachedFunction(func, cache, key_builder, ttl)

    return decorator


class CacheWarmer:
    """缓存预热"""

    def __init__(self, cache: CacheBackend):
        self.cache = cache
        self._tasks: dict[str, Callable] = {}

    def register(self, key: str, loader: Callable, ttl: int | None = None) -> None:
        """注册预热任务"""
        self._tasks[key] = {"loader": loader, "ttl": ttl}

    async def warm_all(self) -> None:
        """预热所有"""
        for key, task in self._tasks.items():
            try:
                value = await task["loader"]()
                await self.cache.set(key, value, task["ttl"])
                logger.info(f"Warmed cache: {key}")
            except Exception as e:
                logger.error(f"Cache warm error for {key}: {e}")

    async def warm(self, key: str) -> None:
        """预热单个"""
        if key not in self._tasks:
            return

        task = self._tasks[key]
        try:
            value = await task["loader"]()
            await self.cache.set(key, value, task["ttl"])
        except Exception as e:
            logger.error(f"Cache warm error for {key}: {e}")


# 全局缓存实例
_memory_cache: MemoryCache | None = None
_disk_cache: DiskCache | None = None
_redis_cache: RedisCache | None = None
_multilevel_cache: MultiLevelCache | None = None


def get_memory_cache(max_size: int = 1000) -> MemoryCache:
    """获取内存缓存"""
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache(max_size=max_size)
    return _memory_cache


def get_disk_cache(cache_dir: Path = None) -> DiskCache:
    """获取磁盘缓存"""
    global _disk_cache
    if _disk_cache is None:
        cache_dir = cache_dir or Path.home() / ".nano-code" / "cache"
        _disk_cache = DiskCache(cache_dir)
    return _disk_cache


def get_redis_cache(url: str = "redis://localhost:6379") -> RedisCache:
    """获取 Redis 缓存"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache(url)
    return _redis_cache


def get_multilevel_cache() -> MultiLevelCache:
    """获取多级缓存"""
    global _multilevel_cache
    if _multilevel_cache is None:
        _multilevel_cache = MultiLevelCache(
            memory_cache=get_memory_cache(), disk_cache=get_disk_cache()
        )
    return _multilevel_cache
