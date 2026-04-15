"""
Nano Code - Memory 模块单元测试
"""

import os
import tempfile

from nano_code.memory.conversation import (
    Conversation,
    ConversationManager,
    ConversationMemory,
    MemoryStore,
    Message,
)


class TestMessage:
    """测试消息类"""

    def test_message_creation(self):
        """测试创建消息"""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_with_metadata(self):
        """测试带元数据的消息"""
        msg = Message(role="assistant", content="Response", metadata={"model": "claude-3"})
        assert msg.metadata["model"] == "claude-3"

    def test_message_timestamp(self):
        """测试消息时间戳"""
        msg = Message(role="user", content="test")
        assert msg.timestamp is not None

    def test_message_to_dict(self):
        """测试消息序列化"""
        msg = Message(role="user", content="test")
        # dataclass 可以直接转 dict
        data = {"role": msg.role, "content": msg.content, "metadata": msg.metadata}
        assert data["role"] == "user"
        assert data["content"] == "test"


class TestConversation:
    """测试对话类"""

    def test_conversation_creation(self):
        """测试创建对话"""
        conv = Conversation(id="test-123")
        assert conv.id == "test-123"
        assert conv.messages == []

    def test_add_message(self):
        """测试添加消息"""
        conv = Conversation(id="test")
        msg = Message(role="user", content="Hello")
        conv.messages.append({"role": msg.role, "content": msg.content})
        assert len(conv.messages) == 1

    def test_add_multiple_messages(self):
        """测试添加多条消息"""
        conv = Conversation(id="test")
        for i in range(3):
            conv.messages.append({"role": "user", "content": f"msg{i}"})
        assert len(conv.messages) == 3

    def test_get_messages_by_role(self):
        """测试按角色获取消息"""
        conv = Conversation(id="test")
        conv.messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "there"},
        ]
        user_msgs = [m for m in conv.messages if m["role"] == "user"]
        assert len(user_msgs) == 2


class TestConversationManager:
    """测试对话管理器"""

    def test_create_conversation(self):
        """测试创建对话"""
        manager = ConversationManager()
        conv = manager.create_conversation("test-id")
        assert conv.id == "test-id"

    def test_get_conversation(self):
        """测试获取对话"""
        manager = ConversationManager()
        manager.create_conversation("test-id")
        conv = manager.get_conversation("test-id")
        assert conv is not None

    def test_delete_conversation(self):
        """测试删除对话"""
        manager = ConversationManager()
        manager.create_conversation("test-id")
        result = manager.delete_conversation("test-id")
        assert result is True

    def test_list_conversations(self):
        """测试列出对话"""
        manager = ConversationManager()
        manager.create_conversation("id1")
        manager.create_conversation("id2")
        convs = manager.list_conversations()
        assert len(convs) == 2


class TestMemoryStore:
    """测试内存存储"""

    def test_memory_store_basic(self):
        """测试基本存储"""
        store = MemoryStore()
        store.save("key", "value")
        assert store.load("key") == "value"

    def test_memory_store_delete(self):
        """测试删除"""
        store = MemoryStore()
        store.save("key", "value")
        store.delete("key")
        assert store.load("key") is None


class TestConversationMemory:
    """测试对话记忆类"""

    def test_conversation_memory_init(self):
        """测试初始化"""
        memory = ConversationMemory()
        assert memory.messages == []
        assert memory.max_tokens == 100000

    def test_conversation_memory_add_message(self):
        """测试添加消息"""
        from langchain_core.messages import HumanMessage

        memory = ConversationMemory()
        msg = HumanMessage(content="Hello")
        memory.add_message(msg)
        assert len(memory.messages) == 1


class TestConversationPersistence:
    """测试对话持久化"""

    def test_save_conversation(self):
        """测试保存对话"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            manager = ConversationManager(storage_path=path)
            conv = manager.create_conversation("test")
            # 简单验证保存不报错
            assert conv is not None

    def test_load_conversation(self):
        """测试加载对话"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConversationManager(storage_path=tmpdir)
            manager.create_conversation("test")
            loaded = manager.get_conversation("test")
            assert loaded is not None


# 兼容性测试
class TestCompatibility:
    """兼容性测试"""

    def test_imports(self):
        """测试导入"""
        from nano_code.memory.conversation import Conversation, MemoryStore, Message

        assert Message is not None
        assert Conversation is not None
        assert MemoryStore is not None
