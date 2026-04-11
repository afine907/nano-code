"""对话记忆管理"""

import json
from pathlib import Path

import tiktoken
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


class ConversationMemory:
    """对话记忆管理

    管理对话历史，支持：
    - 消息添加和获取
    - Token 计数
    - 自动压缩
    - 持久化存储
    """

    def __init__(
        self,
        max_tokens: int = 100000,
        storage_path: Path | None = None,
        auto_save: bool = False,
    ) -> None:
        """初始化记忆管理

        Args:
            max_tokens: 最大 token 数量，超过时触发压缩
            storage_path: 存储文件路径
            auto_save: 是否在添加消息时自动保存
        """
        self.messages: list[BaseMessage] = []
        self.max_tokens = max_tokens
        self.storage_path = storage_path
        self.auto_save = auto_save

        # 初始化 tokenizer
        self._encoding = tiktoken.encoding_for_model("gpt-4")

        # 加载已有记忆
        if storage_path and storage_path.exists():
            self.load()

    def add_message(self, message: BaseMessage) -> None:
        """添加消息

        Args:
            message: 要添加的消息
        """
        self.messages.append(message)

        # 检查是否需要压缩
        if self.token_count() > self.max_tokens:
            self._compress()

        # 自动保存
        if self.auto_save and self.storage_path:
            self.save()

    def token_count(self) -> int:
        """计算当前 token 数量

        Returns:
            token 总数
        """
        total = 0
        for msg in self.messages:
            content = msg.content
            if isinstance(content, str):
                total += len(self._encoding.encode(content))
            else:
                # 对于复杂内容（如列表），转换为字符串处理
                total += len(self._encoding.encode(str(content)))
        return total

    def get_context(self) -> list[BaseMessage]:
        """获取当前上下文（所有消息）

        Returns:
            消息列表
        """
        return self.messages.copy()

    def get_last_n_messages(self, n: int) -> list[BaseMessage]:
        """获取最近 N 条消息

        Args:
            n: 消息数量

        Returns:
            最近 N 条消息
        """
        return self.messages[-n:] if n < len(self.messages) else self.messages.copy()

    def clear(self) -> None:
        """清空记忆"""
        self.messages = []
        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()

    def _compress(self) -> None:
        """压缩记忆：保留系统消息 + 最近消息"""
        if len(self.messages) <= 5:
            return

        # 分离系统消息和普通消息
        system_messages = [m for m in self.messages if isinstance(m, SystemMessage)]
        other_messages = [m for m in self.messages if not isinstance(m, SystemMessage)]

        # 保留最近的 20 条普通消息
        keep_count = min(20, len(other_messages))
        recent_messages = other_messages[-keep_count:]

        # 如果有被丢弃的消息，生成摘要（简化版）
        discarded_count = len(other_messages) - keep_count
        if discarded_count > 0:
            # 创建一个占位摘要
            summary = HumanMessage(content=f"[系统] 已压缩 {discarded_count} 条早期对话")
            self.messages = system_messages + [summary] + recent_messages
        else:
            self.messages = system_messages + recent_messages

    def save(self) -> None:
        """保存记忆到文件"""
        if not self.storage_path:
            return

        # 确保目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 序列化消息
        data = {
            "messages": [
                {
                    "type": msg.__class__.__name__,
                    "content": msg.content,
                }
                for msg in self.messages
            ]
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> None:
        """从文件加载记忆"""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, encoding="utf-8") as f:
            data = json.load(f)

        # 反序列化消息
        msg_classes: dict[str, type[BaseMessage]] = {
            "HumanMessage": HumanMessage,
            "AIMessage": AIMessage,
            "SystemMessage": SystemMessage,
        }

        self.messages = []
        for item in data.get("messages", []):
            msg_class = msg_classes.get(item["type"], HumanMessage)
            self.messages.append(msg_class(content=item["content"]))
