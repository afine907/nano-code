"""短期记忆管理 - 当前会话"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from jojo_code.memory.types import MemoryItem, MemoryType


@dataclass
class ShortTermMemory:
    """短期记忆 - 当前会话

    管理当前会话的记忆，支持：
    - 消息添加和获取
    - Token 计数和自动压缩
    - 会话管理
    - 消息搜索
    """

    def __init__(
        self,
        session_id: str | None = None,
        max_tokens: int = 100000,
    ) -> None:
        """初始化短期记忆

        Args:
            session_id: 会话 ID（默认自动生成）
            max_tokens: 最大 token 数量
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.max_tokens = max_tokens
        self.messages: list[BaseMessage] = []
        self._created_at = datetime.now()

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def message_count(self) -> int:
        """消息数量"""
        return len(self.messages)

    def add_message(self, message: BaseMessage) -> None:
        """添加消息

        Args:
            message: 要添加的消息
        """
        self.messages.append(message)

        # 检查是否需要压缩
        if self.token_count() > self.max_tokens:
            self._compress()

    def add_messages(self, messages: list[BaseMessage]) -> None:
        """批量添加消息

        Args:
            messages: 消息列表
        """
        for msg in messages:
            self.add_message(msg)

    def add_user_message(self, content: str) -> HumanMessage:
        """添加用户消息

        Args:
            content: 消息内容

        Returns:
            创建的消息
        """
        msg = HumanMessage(content=content)
        self.add_message(msg)
        return msg

    def add_ai_message(self, content: str) -> AIMessage:
        """添加 AI 消息

        Args:
            content: 消息内容

        Returns:
            创建的消息
        """
        msg = AIMessage(content=content)
        self.add_message(msg)
        return msg

    def add_system_message(self, content: str) -> SystemMessage:
        """添加系统消息

        Args:
            content: 消息内容

        Returns:
            创建的消息
        """
        msg = SystemMessage(content=content)
        self.add_message(msg)
        return msg

    def get_messages(self) -> list[BaseMessage]:
        """获取所有消息

        Returns:
            消息列表副本
        """
        return self.messages.copy()

    def get_last_n(self, n: int) -> list[BaseMessage]:
        """获取最近 N 条消息

        Args:
            n: 消息数量

        Returns:
            最近 N 条消息
        """
        if n >= len(self.messages):
            return self.messages.copy()
        return self.messages[-n:]

    def get_messages_by_role(self, role: str) -> list[BaseMessage]:
        """按角色获取消息

        Args:
            role: 角色 (user/ai/system)

        Returns:
            匹配的消息
        """
        role_map = {
            "user": HumanMessage,
            "ai": AIMessage,
            "assistant": AIMessage,
            "system": SystemMessage,
        }
        msg_class = role_map.get(role.lower())
        if not msg_class:
            return []
        return [m for m in self.messages if isinstance(m, msg_class)]

    def token_count(self) -> int:
        """计算当前 token 数量

        Returns:
            token 总数
        """
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            # 如果 tiktoken 不可用，使用简单估算
            return sum(len(str(m.content)) // 4 for m in self.messages)

        total = 0
        for msg in self.messages:
            content = msg.content
            if isinstance(content, str):
                total += len(encoding.encode(content))
            else:
                total += len(encoding.encode(str(content)))
        return total

    def clear(self) -> None:
        """清空记忆"""
        self.messages = []

    def to_memory_items(self) -> list[MemoryItem]:
        """转换为记忆条目

        Returns:
            记忆条目列表
        """
        items = []
        for msg in self.messages:
            role = (
                "user"
                if isinstance(msg, HumanMessage)
                else "ai"
                if isinstance(msg, AIMessage)
                else "system"
            )
            items.append(
                MemoryItem(
                    id=str(uuid.uuid4()),
                    content=msg.content,
                    memory_type=MemoryType.SHORT_TERM,
                    session_id=self.session_id,
                    metadata={"role": role},
                )
            )
        return items

    def _compress(self, keep_recent: int = 20) -> None:
        """压缩记忆：保留系统消息 + 最近消息

        Args:
            keep_recent: 保留的最近消息数量
        """
        if len(self.messages) <= keep_recent:
            return

        # 分离系统消息和普通消息
        system_messages = [m for m in self.messages if isinstance(m, SystemMessage)]
        other_messages = [m for m in self.messages if not isinstance(m, SystemMessage)]

        # 保留最近的 keep_recent 条普通消息
        keep_count = min(keep_recent, len(other_messages))
        recent_messages = other_messages[-keep_count:]

        # 如果有被丢弃的消息，生成摘要
        discarded_count = len(other_messages) - keep_count
        if discarded_count > 0:
            summary = HumanMessage(
                content=f"[系统] 已压缩 {discarded_count} 条早期对话，保留最近 {keep_count} 条"
            )
            self.messages = system_messages + [summary] + recent_messages
        else:
            self.messages = system_messages + recent_messages

    def search(self, keyword: str, case_sensitive: bool = False) -> list[BaseMessage]:
        """搜索消息内容

        Args:
            keyword: 关键词
            case_sensitive: 是否区分大小写

        Returns:
            匹配的消息
        """
        if not case_sensitive:
            keyword = keyword.lower()

        results = []
        for msg in self.messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            search_content = content if case_sensitive else content.lower()
            if keyword in search_content:
                results.append(msg)
        return results

    def get_context(self) -> list[BaseMessage]:
        """获取上下文（兼容旧 API）

        Returns:
            消息列表
        """
        return self.get_messages()

    def get_last_n_messages(self, n: int) -> list[BaseMessage]:
        """获取最近 N 条消息（兼容旧 API）

        Args:
            n: 消息数量

        Returns:
            最近 N 条消息
        """
        return self.get_last_n(n)


def create_session_memory(
    session_id: str | None = None, max_tokens: int = 100000
) -> ShortTermMemory:
    """创建会话记忆（工厂函数）

    Args:
        session_id: 会话 ID
        max_tokens: 最大 token 数量

    Returns:
        短期记忆实例
    """
    return ShortTermMemory(session_id=session_id, max_tokens=max_tokens)
