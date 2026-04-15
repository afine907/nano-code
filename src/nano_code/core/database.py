"""
Nano Code - 数据库抽象层
提供统一的数据库操作接口，支持多种数据库后端
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class Query:
    """查询对象"""

    table: str
    filter: dict[str, Any] = field(default_factory=dict)
    projection: list[str] | None = None
    sort: list[tuple] | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass
class Record:
    """记录"""

    id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DatabaseError(Exception):
    """数据库错误"""

    pass


class ConnectionError(DatabaseError):
    """连接错误"""

    pass


class QueryError(DatabaseError):
    """查询错误"""

    pass


class DatabaseBackend(ABC):
    """数据库后端基类"""

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def execute(self, query: str, params: tuple = ()) -> Any:
        pass

    @abstractmethod
    async def fetch_one(self, query: Query) -> Record | None:
        pass

    @abstractmethod
    async def fetch_many(self, query: Query) -> list[Record]:
        pass

    @abstractmethod
    async def insert(self, table: str, data: dict) -> str:
        pass

    @abstractmethod
    async def update(self, table: str, id: str, data: dict) -> bool:
        pass

    @abstractmethod
    async def delete(self, table: str, id: str) -> bool:
        pass

    @abstractmethod
    async def create_table(self, table: str, schema: dict) -> None:
        pass

    @abstractmethod
    async def drop_table(self, table: str) -> None:
        pass


class SQLiteBackend(DatabaseBackend):
    """SQLite 后端"""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        import aiosqlite

        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        logger.info(f"Connected to SQLite: {self.db_path}")

    async def disconnect(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def execute(self, query: str, params: tuple = ()) -> Any:
        async with self._lock:
            cursor = await self._conn.execute(query, params)
            await self._conn.commit()
            return cursor

    async def fetch_one(self, query: Query) -> Record | None:
        sql, params = self._build_select(query)
        async with self._lock:
            cursor = await self._conn.execute(sql, params)
            row = await cursor.fetchone()

        if row:
            return self._row_to_record(row)
        return None

    async def fetch_many(self, query: Query) -> list[Record]:
        sql, params = self._build_select(query)
        async with self._lock:
            cursor = await self._conn.execute(sql, params)
            rows = await cursor.fetchall()

        return [self._row_to_record(row) for row in rows]

    async def insert(self, table: str, data: dict) -> str:
        import uuid

        id = str(uuid.uuid4())
        data["id"] = id
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])

        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        await self.execute(sql, tuple(data.values()))

        return id

    async def update(self, table: str, id: str, data: dict) -> bool:
        data["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE id = ?"

        cursor = await self.execute(sql, (*tuple(data.values()), id))
        return cursor.rowcount > 0

    async def delete(self, table: str, id: str) -> bool:
        sql = f"DELETE FROM {table} WHERE id = ?"
        cursor = await self.execute(sql, (id,))
        return cursor.rowcount > 0

    async def create_table(self, table: str, schema: dict) -> None:
        columns = []
        for name, info in schema.items():
            col_type = info.get("type", "TEXT")
            primary = "PRIMARY KEY" if info.get("primary") else ""
            nullable = "" if info.get("not_null") else "NULL"
            default = f"DEFAULT {info['default']}" if "default" in info else ""
            columns.append(f"{name} {col_type} {nullable} {primary} {default}".strip())

        sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
        await self.execute(sql)

    async def drop_table(self, table: str) -> None:
        await self.execute(f"DROP TABLE IF EXISTS {table}")

    def _build_select(self, query: Query) -> tuple:
        """构建 SELECT 语句"""
        columns = query.projection or ["*"]
        sql = f"SELECT {', '.join(columns)} FROM {query.table}"

        params = []
        if query.filter:
            where = " AND ".join([f"{k} = ?" for k in query.filter.keys()])
            sql += f" WHERE {where}"
            params = list(query.filter.values())

        if query.sort:
            order = ", ".join([f"{col} {dir}" for col, dir in query.sort])
            sql += f" ORDER BY {order}"

        if query.limit:
            sql += f" LIMIT {query.limit}"

        if query.offset:
            sql += f" OFFSET {query.offset}"

        return sql, tuple(params)

    def _row_to_record(self, row) -> Record:
        """行转记录"""
        data = dict(row)
        return Record(
            id=data.pop("id", None),
            data=data,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class MockDatabaseBackend(DatabaseBackend):
    """Mock 数据库后端（内存存储）"""

    def __init__(self):
        self._data: dict[str, list[Record]] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        logger.info("Connected to Mock Database")

    async def disconnect(self) -> None:
        self._data.clear()

    async def execute(self, query: str, params: tuple = ()) -> Any:
        # 简化的执行（不实际执行 SQL）
        return MockCursor()

    async def fetch_one(self, query: Query) -> Record | None:
        async with self._lock:
            records = self._data.get(query.table, [])

            # 简单过滤
            for record in records:
                if all(record.data.get(k) == v for k, v in query.filter.items()):
                    return record

            return None

    async def fetch_many(self, query: Query) -> list[Record]:
        async with self._lock:
            records = self._data.get(query.table, [])

            # 过滤
            filtered = records
            if query.filter:
                filtered = [
                    r for r in records if all(r.data.get(k) == v for k, v in query.filter.items())
                ]

            # 排序
            if query.sort:
                for col, direction in reversed(query.sort):
                    reverse = direction.lower() == "desc"
                    filtered = sorted(filtered, key=lambda r: r.data.get(col, ""), reverse=reverse)

            # 分页
            if query.offset:
                filtered = filtered[query.offset :]
            if query.limit:
                filtered = filtered[: query.limit]

            return filtered

    async def insert(self, table: str, data: dict) -> str:
        import uuid

        id = str(uuid.uuid4())

        async with self._lock:
            if table not in self._data:
                self._data[table] = []

            record = Record(id=id, data=data, created_at=datetime.now(), updated_at=datetime.now())
            self._data[table].append(record)

        return id

    async def update(self, table: str, id: str, data: dict) -> bool:
        async with self._lock:
            if table not in self._data:
                return False

            for record in self._data[table]:
                if record.id == id:
                    record.data.update(data)
                    record.updated_at = datetime.now()
                    return True

        return False

    async def delete(self, table: str, id: str) -> bool:
        async with self._lock:
            if table not in self._data:
                return False

            for i, record in enumerate(self._data[table]):
                if record.id == id:
                    self._data[table].pop(i)
                    return True

        return False

    async def create_table(self, table: str, schema: dict) -> None:
        async with self._lock:
            if table not in self._data:
                self._data[table] = []

    async def drop_table(self, table: str) -> None:
        async with self._lock:
            if table in self._data:
                del self._data[table]


class MockCursor:
    """Mock 游标"""

    def __init__(self):
        self.rowcount = 0

    @property
    def lastrowid(self):
        return None


# 仓库模式
class Repository(Generic[T]):
    """通用仓储"""

    def __init__(self, backend: DatabaseBackend, table: str, model_class: type[T]):
        self.backend = backend
        self.table = table
        self.model_class = model_class

    async def find_by_id(self, id: str) -> T | None:
        query = Query(table=self.table, filter={"id": id})
        record = await self.backend.fetch_one(query)
        if record:
            return self._record_to_model(record)
        return None

    async def find_one(self, filter: dict) -> T | None:
        query = Query(table=self.table, filter=filter)
        record = await self.backend.fetch_one(query)
        if record:
            return self._record_to_model(record)
        return None

    async def find_many(
        self,
        filter: dict | None = None,
        sort: list[tuple] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]:
        query = Query(table=self.table, filter=filter or {}, sort=sort, limit=limit, offset=offset)
        records = await self.backend.fetch_many(query)
        return [self._record_to_model(r) for r in records]

    async def create(self, data: dict) -> str:
        return await self.backend.insert(self.table, data)

    async def update(self, id: str, data: dict) -> bool:
        return await self.backend.update(self.table, id, data)

    async def delete(self, id: str) -> bool:
        return await self.backend.delete(self.table, id)

    async def count(self, filter: dict | None = None) -> int:
        records = await self.find_many(filter=filter)
        return len(records)

    def _record_to_model(self, record: Record) -> T:
        """记录转模型"""
        return self.model_class(**record.data)


# 数据库管理器
class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.backends: dict[str, DatabaseBackend] = {}
        self._default: DatabaseBackend | None = None

    def add_backend(self, name: str, backend: DatabaseBackend) -> None:
        self.backends[name] = backend

    def set_default(self, name: str) -> None:
        if name in self.backends:
            self._default = self.backends[name]

    def get_backend(self, name: str | None = None) -> DatabaseBackend:
        if name:
            if name not in self.backends:
                raise ValueError(f"Backend {name} not found")
            return self.backends[name]

        if self._default:
            return self._default

        if not self.backends:
            # 默认使用 Mock
            self._default = MockDatabaseBackend()
            self.backends["default"] = self._default

        return self._default

    @asynccontextmanager
    async def connection(self, name: str | None = None):
        backend = self.get_backend(name)
        await backend.connect()
        try:
            yield backend
        finally:
            await backend.disconnect()

    def get_repository(self, table: str, model_class: type[T]) -> Repository[T]:
        backend = self.get_backend()
        return Repository(backend, table, model_class)


# 全局数据库管理器
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_repository(table: str, model_class: type[T]) -> Repository[T]:
    """获取仓储"""
    return get_db_manager().get_repository(table, model_class)
