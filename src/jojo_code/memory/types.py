"""记忆模块类型定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryType(Enum):
    """记忆类型"""

    SHORT_TERM = "short_term"  # 短期记忆（当前会话）
    LONG_TERM = "long_term"  # 长期记忆（持久化）


class MemoryScope(Enum):
    """记忆作用域"""

    CURRENT_SESSION = "current_session"  # 当前会话
    ALL_SESSIONS = "all_sessions"  # 所有会话


@dataclass
class MemoryItem:
    """记忆条目"""

    id: str
    content: str
    memory_type: MemoryType
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryItem":
        """从字典反序列化"""
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )


@dataclass
class SearchResult:
    """搜索结果"""

    item: MemoryItem
    score: float  # 相关性分数 0-1
    matched_content: str  # 匹配的内容片段
