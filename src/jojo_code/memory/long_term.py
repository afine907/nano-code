"""长期记忆管理 - 持久化存储"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from jojo_code.memory.types import MemoryItem, MemoryType, SearchResult


@dataclass
class LongTermMemoryConfig:
    """长期记忆配置"""

    storage_dir: Path  # 存储目录
    max_items: int = 10000  # 最大条目数
    retention_days: int = 90  # 保留天数
    auto_cleanup: bool = True  # 自动清理过期数据


class LongTermMemory:
    """长期记忆 - 持久化存储

    支持多会话记忆存储和管理：
    - 多会话持久化
    - 基于时间的清理
    - 关键词搜索
    - 记忆摘要
    """

    def __init__(
        self,
        storage_dir: Path | str | None = None,
        max_items: int = 10000,
        retention_days: int = 90,
    ) -> None:
        """初始化长期记忆

        Args:
            storage_dir: 存储目录（默认 ~/.jojo-code/memory）
            max_items: 最大条目数
            retention_days: 保留天数
        """
        if storage_dir is None:
            from pathlib import Path

            storage_dir = Path.home() / ".jojo-code" / "memory"

        self.storage_dir = Path(storage_dir)
        self.max_items = max_items
        self.retention_days = retention_days

        # 确保目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._cache: dict[str, MemoryItem] = {}
        self._index_loaded = False

        # 自动清理
        if self.retention_days > 0:
            self.cleanup()

    def _get_session_dir(self, session_id: str) -> Path:
        """获取会话存储目录"""
        return self.storage_dir / session_id

    def _get_items_file(self, session_id: str) -> Path:
        """获取会话记忆文件"""
        return self._get_session_dir(session_id) / "memory.json"

    def add(
        self,
        content: str,
        session_id: str,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> MemoryItem:
        """添加记忆

        Args:
            content: 记忆内容
            session_id: 会话 ID
            tags: 标签
            metadata: 元数据

        Returns:
            创建的记忆条目
        """
        item = MemoryItem(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=MemoryType.LONG_TERM,
            session_id=session_id,
            tags=tags or [],
            metadata=metadata or {},
        )

        # 保存到文件
        self._save_item(item)

        # 添加到缓存
        self._cache[item.id] = item

        return item

    def add_message(self, content: str, role: str, session_id: str) -> MemoryItem:
        """添加消息记忆

        Args:
            content: 消息内容
            role: 角色 (user/ai/system)
            session_id: 会话 ID

        Returns:
            创建的记忆条目
        """
        return self.add(
            content=content,
            session_id=session_id,
            metadata={"role": role},
        )

    def get(self, memory_id: str) -> MemoryItem | None:
        """获取记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            记忆条目，不存在返回 None
        """
        # 先检查缓存
        if memory_id in self._cache:
            return self._cache[memory_id]

        # 搜索所有会话
        for session_dir in self.storage_dir.iterdir():
            if not session_dir.is_dir():
                continue
            items_file = session_dir / "memory.json"
            if not items_file.exists():
                continue

            data = json.loads(items_file.read_text(encoding="utf-8"))
            for item_data in data.get("items", []):
                if item_data["id"] == memory_id:
                    item = MemoryItem.from_dict(item_data)
                    self._cache[memory_id] = item
                    return item

        return None

    def get_session_memories(self, session_id: str, limit: int = 100) -> list[MemoryItem]:
        """获取会话记忆

        Args:
            session_id: 会话 ID
            limit: 返回数量限制

        Returns:
            记忆条目列表
        """
        items_file = self._get_items_file(session_id)
        if not items_file.exists():
            return []

        data = json.loads(items_file.read_text(encoding="utf-8"))
        items = [MemoryItem.from_dict(d) for d in data.get("items", [])]
        return items[-limit:]

    def list_sessions(self) -> list[str]:
        """列出所有会话

        Returns:
            会话 ID 列表
        """
        sessions = []
        for session_dir in self.storage_dir.iterdir():
            if session_dir.is_dir():
                sessions.append(session_dir.name)
        return sorted(sessions)

    def search(
        self, keyword: str, session_id: str | None = None, limit: int = 10
    ) -> list[SearchResult]:
        """搜索记忆

        Args:
            keyword: 关键词
            session_id: 会话 ID（None 搜索所有会话）
            limit: 返回结果数量

        Returns:
            搜索结果列表
        """
        results: list[SearchResult] = []
        keyword_lower = keyword.lower()

        # 确定搜索范围
        if session_id:
            sessions = [session_id]
        else:
            sessions = self.list_sessions()

        for sid in sessions:
            items = self.get_session_memories(sid)
            for item in items:
                # 简单关键词匹配
                if keyword_lower in item.content.lower():
                    # 计算相关性分数（简单实现）
                    score = self._calculate_score(item.content, keyword)
                    results.append(
                        SearchResult(
                            item=item,
                            score=score,
                            matched_content=self._extract_match(item.content, keyword),
                        )
                    )

        # 按相关性排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def delete_session(self, session_id: str) -> bool:
        """删除会话记忆

        Args:
            session_id: 会话 ID

        Returns:
            是否成功删除
        """
        session_dir = self._get_session_dir(session_id)
        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir)

            # 清理缓存
            self._cache = {k: v for k, v in self._cache.items() if v.session_id != session_id}
            return True
        return False

    def cleanup(self, retention_days: int | None = None) -> int:
        """清理过期记忆

        Args:
            retention_days: 保留天数（None 使用默认配置）

        Returns:
            清理的条目数量
        """
        retention = retention_days or self.retention_days
        cutoff = datetime.now() - timedelta(days=retention)
        cleaned = 0

        for session_dir in self.storage_dir.iterdir():
            if not session_dir.is_dir():
                continue

            items_file = session_dir / "memory.json"
            if not items_file.exists():
                continue

            data = json.loads(items_file.read_text(encoding="utf-8"))
            items = [MemoryItem.from_dict(d) for d in data.get("items", [])]

            # 过滤未过期的
            valid_items = [item for item in items if item.created_at.replace(tzinfo=None) > cutoff]

            # 如果有清理，更新文件
            cleaned += len(items) - len(valid_items)
            if cleaned > 0:
                self._save_items(session_dir.name, valid_items)

        return cleaned

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        total_items = 0
        sessions = self.list_sessions()

        for session_id in sessions:
            items = self.get_session_memories(session_id, limit=10000)
            total_items += len(items)

        return {
            "total_items": total_items,
            "sessions": len(sessions),
            "session_ids": sessions[:10],  # 只返回前 10 个
            "storage_dir": str(self.storage_dir),
        }

    def _save_item(self, item: MemoryItem) -> None:
        """保存单个记忆条目"""
        session_dir = self._get_session_dir(item.session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        items_file = self._get_items_file(item.session_id)

        # 读取现有数据
        if items_file.exists():
            data = json.loads(items_file.read_text(encoding="utf-8"))
            items = [MemoryItem.from_dict(d) for d in data.get("items", [])]
        else:
            items = []

        # 添加新条目
        items.append(item)

        # 限制数量
        if len(items) > self.max_items:
            items = items[-self.max_items :]

        # 保存
        self._save_items(item.session_id, items)

    def _save_items(self, session_id: str, items: list[MemoryItem]) -> None:
        """保存记忆列表"""
        session_dir = self._get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        items_file = self._get_items_file(session_id)
        data = {
            "session_id": session_id,
            "updated_at": datetime.now().isoformat(),
            "items": [item.to_dict() for item in items],
        }

        items_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _calculate_score(self, content: str, keyword: str) -> float:
        """计算相关性分数

        Args:
            content: 内容
            keyword: 关键词

        Returns:
            分数 0-1
        """
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        # 基础分数
        score = 0.0

        # 精确匹配
        if keyword_lower in content_lower:
            score += 0.5

        # 词频
        count = content_lower.count(keyword_lower)
        score += min(count * 0.1, 0.3)

        # 位置（出现在开头更好）
        pos = content_lower.find(keyword_lower)
        if pos >= 0:
            score += 0.2 * (1 - pos / len(content_lower))

        return min(score, 1.0)

    def _extract_match(self, content: str, keyword: str, context_chars: int = 50) -> str:
        """提取匹配片段

        Args:
            content: 完整内容
            keyword: 关键词
            context_chars: 上下文字符数

        Returns:
            匹配的内容片段
        """
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        pos = content_lower.find(keyword_lower)
        if pos < 0:
            return content[:100]

        # 提取上下文
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(keyword) + context_chars)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet


def create_longterm_memory(storage_dir: Path | str | None = None) -> LongTermMemory:
    """创建长期记忆（工厂函数）

    Args:
        storage_dir: 存储目录

    Returns:
        长期记忆实例
    """
    return LongTermMemory(storage_dir=storage_dir)
