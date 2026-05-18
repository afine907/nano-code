"""记忆检索模块"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from jojo_code.memory.long_term import LongTermMemory
from jojo_code.memory.short_term import ShortTermMemory
from jojo_code.memory.types import MemoryItem, MemoryType, SearchResult


@dataclass
class MemoryRetriever:
    """记忆检索器

    统一接口检索短期和长期记忆：
    - 短期记忆（当前会话）
    - 长期记忆（历史会话）
    - 混合搜索
    """

    def __init__(
        self,
        short_term: ShortTermMemory | None = None,
        long_term: LongTermMemory | None = None,
    ) -> None:
        """初始化检索器

        Args:
            short_term: 短期记忆实例
            long_term: 长期记忆实例
        """
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemory()

    def search(
        self,
        keyword: str,
        scope: str = "all",  # "current" | "history" | "all"
        limit: int = 10,
    ) -> dict[str, list[SearchResult]]:
        """搜索记忆

        Args:
            keyword: 关键词
            scope: 搜索范围 (current/histroy/all)
            limit: 返回结果数量

        Returns:
            按类型分组的搜索结果
        """
        results: dict[str, list[SearchResult]] = {
            "current_session": [],
            "history": [],
        }

        # 搜索短期记忆
        if scope in ("current", "all"):
            messages = self.short_term.search(keyword)
            for msg in messages[:limit]:
                role = "user" if hasattr(msg, "type") and msg.type == "human" else "ai"
                item = MemoryItem(
                    id="short-term",
                    content=msg.content if isinstance(msg.content, str) else str(msg.content),
                    memory_type=MemoryType.SHORT_TERM,
                    session_id=self.short_term.session_id,
                    metadata={"role": role},
                )
                results["current_session"].append(
                    SearchResult(
                        item=item,
                        score=1.0,
                        matched_content=msg.content
                        if isinstance(msg.content, str)
                        else str(msg.content),
                    )
                )

        # 搜索长期记忆
        if scope in ("history", "all"):
            history_results = self.long_term.search(
                keyword,
                session_id=None,
                limit=limit,
            )
            results["history"] = history_results

        return results

    def search_current_session(self, keyword: str, limit: int = 10) -> list[SearchResult]:
        """搜索当前会话

        Args:
            keyword: 关键词
            limit: 返回结果数量

        Returns:
            搜索结果
        """
        return self.search(keyword, scope="current", limit=limit)["current_session"]

    def search_history(
        self, keyword: str, session_id: str | None = None, limit: int = 10
    ) -> list[SearchResult]:
        """搜索历史会话

        Args:
            keyword: 关键词
            session_id: 会话 ID（None 搜索所有）
            limit: 返回结果数量

        Returns:
            搜索结果
        """
        return self.long_term.search(keyword, session_id=session_id, limit=limit)

    def get_recent_memories(self, limit: int = 10) -> list[MemoryItem]:
        """获取最近的记忆

        Args:
            limit: 返回数量

        Returns:
            记忆列表
        """
        # 获取当前会话记忆
        current = self.short_term.to_memory_items()

        # 获取历史记忆
        sessions = self.long_term.list_sessions()
        history = []
        for sid in sessions[-5:]:  # 最近 5 个会话
            history.extend(self.long_term.get_session_memories(sid, limit=5))

        # 合并并按时间排序
        all_memories = current + history
        all_memories.sort(key=lambda x: x.created_at, reverse=True)

        return all_memories[:limit]

    def save_current_session(self) -> None:
        """保存当前会话到长期记忆"""
        items = self.short_term.to_memory_items()
        for item in items:
            self.long_term.add(
                content=item.content,
                session_id=f"archived_{item.session_id}",
                tags=item.tags,
                metadata=item.metadata,
            )

    def load_session(self, session_id: str) -> list[MemoryItem]:
        """加载历史会话

        Args:
            session_id: 会话 ID

        Returns:
            记忆列表
        """
        return self.long_term.get_session_memories(session_id)

    def get_all_sessions(self) -> list[str]:
        """获取所有会话 ID

        Returns:
            会话 ID 列表
        """
        # 合并当前会话和历史会话
        sessions = [self.short_term.session_id]
        sessions.extend(self.long_term.list_sessions())
        return list(set(sessions))


@dataclass
class SessionMemory:
    """统一的会话记忆接口

    整合短期记忆和长期记忆，提供统一 API：
    - add_message: 添加消息
    - get_context: 获取上下文
    - search: 搜索
    - save: 保存会话
    - load: 加载会话
    """

    def __init__(
        self,
        session_id: str | None = None,
        max_tokens: int = 100000,
        storage_dir: str | None = None,
    ) -> None:
        """初始化会话记忆

        Args:
            session_id: 会话 ID
            max_tokens: 最大 token 数量
            storage_dir: 长期记忆存储目录
        """
        from jojo_code.memory.long_term import LongTermMemory
        from jojo_code.memory.short_term import ShortTermMemory

        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 短期记忆
        self.short_term = ShortTermMemory(
            session_id=self.session_id,
            max_tokens=max_tokens,
        )

        # 长期记忆
        self.long_term = LongTermMemory(
            storage_dir=storage_dir,
        )

        # 检索器
        self.retriever = MemoryRetriever(
            short_term=self.short_term,
            long_term=self.long_term,
        )

    def add_message(self, content: str, role: str = "user") -> None:
        """添加消息

        Args:
            content: 消息内容
            role: 角色 (user/ai/system)
        """
        if role == "user":
            self.short_term.add_user_message(content)
        elif role in ("ai", "assistant"):
            self.short_term.add_ai_message(content)
        elif role == "system":
            self.short_term.add_system_message(content)

        # 同时保存到长期记忆
        self.long_term.add_message(content, role, self.session_id)

    def get_context(self, max_messages: int | None = None) -> list[Any]:
        """获取上下文

        Args:
            max_messages: 最大消息数（None 返回全部）

        Returns:
            消息列表
        """
        if max_messages is None:
            return self.short_term.get_messages()
        return self.short_term.get_last_n(max_messages)

    def search(self, keyword: str, scope: str = "all") -> dict[str, list[SearchResult]]:
        """搜索记忆

        Args:
            keyword: 关键词
            scope: 搜索范围 (current/history/all)

        Returns:
            搜索结果
        """
        return self.retriever.search(keyword, scope=scope)

    def save(self) -> None:
        """保存当前会话（实际上在 add_message 时已经持久化）"""
        pass

    def clear(self) -> None:
        """清空当前会话记忆"""
        self.short_term.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息
        """
        return {
            "session_id": self.session_id,
            "current_messages": self.short_term.message_count,
            "current_tokens": self.short_term.token_count(),
            "history_sessions": len(self.long_term.list_sessions()),
        }


def create_session_memory(session_id: str | None = None, max_tokens: int = 100000) -> SessionMemory:
    """创建会话记忆（工厂函数）

    Args:
        session_id: 会话 ID
        max_tokens: 最大 token 数量

    Returns:
        会话记忆实例
    """
    return SessionMemory(session_id=session_id, max_tokens=max_tokens)
