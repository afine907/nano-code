"""多会话管理器

管理多个独立会话，支持：
- 会话创建、切换、删除
- 会话持久化
- 会话列表
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from nano_code.memory.conversation import ConversationMemory


@dataclass
class Session:
    """会话数据类"""

    id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    storage_path: Path | None = None
    memory: ConversationMemory | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            message_count=data.get("message_count", 0),
        )


class SessionManager:
    """会话管理器"""

    def __init__(self, sessions_dir: Path | None = None) -> None:
        """初始化会话管理器

        Args:
            sessions_dir: 会话存储目录
        """
        self.sessions_dir = sessions_dir or Path.home() / ".nano-code" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self._sessions: dict[str, Session] = {}
        self._current_session_id: str | None = None
        self._index_file = self.sessions_dir / "index.json"

        self._load_index()

    def _load_index(self) -> None:
        """加载会话索引"""
        if not self._index_file.exists():
            return

        try:
            with open(self._index_file) as f:
                data = json.load(f)

            for item in data.get("sessions", []):
                session = Session.from_dict(item)
                self._sessions[session.id] = session

            self._current_session_id = data.get("current_session_id")
        except Exception:
            pass

    def _save_index(self) -> None:
        """保存会话索引"""
        data = {
            "sessions": [s.to_dict() for s in self._sessions.values()],
            "current_session_id": self._current_session_id,
        }

        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_session(self, name: str | None = None) -> Session:
        """创建新会话

        Args:
            name: 会话名称（可选）

        Returns:
            新创建的会话
        """
        session_id = str(uuid.uuid4())[:8]
        session_name = name or f"会话 {session_id}"

        storage_path = self.sessions_dir / f"{session_id}.json"
        memory = ConversationMemory(storage_path=storage_path, auto_save=True)

        session = Session(
            id=session_id,
            name=session_name,
            storage_path=storage_path,
            memory=memory,
        )

        self._sessions[session_id] = session
        self._current_session_id = session_id
        self._save_index()

        return session

    def get_session(self, session_id: str) -> Session | None:
        """获取会话

        Args:
            session_id: 会话 ID

        Returns:
            会话，如果不存在则返回 None
        """
        return self._sessions.get(session_id)

    def switch_session(self, session_id: str) -> bool:
        """切换当前会话

        Args:
            session_id: 会话 ID

        Returns:
            是否切换成功
        """
        if session_id not in self._sessions:
            return False

        self._current_session_id = session_id
        self._save_index()
        return True

    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否删除成功
        """
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]
        if session.storage_path and session.storage_path.exists():
            try:
                session.storage_path.unlink()
            except OSError:
                pass  # 忽略删除失败，继续清理内存状态

        del self._sessions[session_id]

        if self._current_session_id == session_id:
            self._current_session_id = None

        self._save_index()
        return True

    def list_sessions(self) -> list[Session]:
        """列出所有会话

        Returns:
            会话列表（按更新时间排序）
        """
        sessions = list(self._sessions.values())
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def get_current_session(self) -> Session | None:
        """获取当前会话

        Returns:
            当前会话，如果不存在则返回 None
        """
        if not self._current_session_id:
            return None
        return self._sessions.get(self._current_session_id)

    def get_or_create_current_session(self) -> Session:
        """获取当前会话，如果不存在则创建新会话

        Returns:
            当前会话
        """
        session = self.get_current_session()
        if session:
            return session
        return self.create_session()

    def update_session_activity(self, session_id: str) -> None:
        """更新会话活动

        Args:
            session_id: 会话 ID
        """
        session = self._sessions.get(session_id)
        if session:
            session.updated_at = datetime.now()
            self._save_index()

    def add_message_to_session(self, session_id: str, role: str, content: str) -> None:
        """添加消息到会话

        Args:
            session_id: 会话 ID
            role: 消息角色
            content: 消息内容
        """
        session = self._sessions.get(session_id)
        if not session:
            return

        if session.memory:
            if role == "user":
                session.memory.add_message(HumanMessage(content=content))
            else:
                session.memory.add_message(AIMessage(content=content))

        session.message_count += 1
        session.updated_at = datetime.now()
        self._save_index()
