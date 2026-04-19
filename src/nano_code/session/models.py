from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime


def _now_timestamp() -> float:
    """获取当前 UTC 时间戳"""
    return datetime.now(UTC).timestamp()


@dataclass
class Message:
    role: str  # e.g., 'user', 'assistant', 'system'
    content: str
    timestamp: float = field(default_factory=_now_timestamp)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> Message:
        return Message(
            role=d["role"],
            content=d["content"],
            timestamp=d.get("timestamp", _now_timestamp()),
        )


@dataclass
class Session:
    id: str
    user_id: str | None = None
    created_at: float = field(default_factory=_now_timestamp)
    last_seen_at: float = field(default_factory=_now_timestamp)
    messages: list[Message] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        self.last_seen_at = _now_timestamp()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_seen_at": self.last_seen_at,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(d: dict) -> Session:
        msgs = [Message.from_dict(md) for md in d.get("messages", [])]
        s = Session(
            id=d["id"],
            user_id=d.get("user_id"),
            created_at=d.get("created_at", _now_timestamp()),
            last_seen_at=d.get("last_seen_at", _now_timestamp()),
            messages=msgs,
            metadata=d.get("metadata", {}),
        )
        return s
