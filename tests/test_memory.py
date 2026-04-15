"""
Nano Code - Memory 模块单元测试
"""

import json
import os
import tempfile

import pytest

from nano_code.memory.conversation import Conversation, ConversationManager, MemoryStore, Message


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
        data = msg.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "test"

    def test_message_from_dict(self):
        """测试消息反序列化"""
        data = {"role": "user", "content": "test", "timestamp": "2024-01-01T00:00:00"}
        msg = Message.from_dict(data)
        assert msg.role == "user"
        assert msg.content == "test"


class TestConversation:
    """测试对话类"""

    def test_conversation_creation(self):
        """测试创建对话"""
        conv = Conversation(id="conv1", title="Test Conversation")
        assert conv.id == "conv1"
        assert conv.title == "Test Conversation"
        assert len(conv.messages) == 0

    def test_add_message(self):
        """测试添加消息"""
        conv = Conversation()
        conv.add_message(role="user", content="Hello")
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"

    def test_add_multiple_messages(self):
        """测试添加多条消息"""
        conv = Conversation()
        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi there!")
        conv.add_message(role="user", content="How are you?")

        assert len(conv.messages) == 3
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"

    def test_get_messages_by_role(self):
        """测试按角色获取消息"""
        conv = Conversation()
        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi")
        conv.add_message(role="user", content="Bye")

        user_messages = conv.get_messages(role="user")
        assert len(user_messages) == 2

    def test_conversation_to_dict(self):
        """测试对话序列化"""
        conv = Conversation(id="conv1", title="Test")
        conv.add_message(role="user", content="Hello")

        data = conv.to_dict()
        assert data["id"] == "conv1"
        assert len(data["messages"]) == 1

    def test_conversation_from_dict(self):
        """测试对话反序列化"""
        data = {"id": "conv1", "title": "Test", "messages": [{"role": "user", "content": "Hello"}]}
        conv = Conversation.from_dict(data)
        assert conv.id == "conv1"
        assert len(conv.messages) == 1

    def test_clear_conversation(self):
        """测试清空对话"""
        conv = Conversation()
        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi")

        conv.clear()
        assert len(conv.messages) == 0

    def test_conversation_length(self):
        """测试对话长度"""
        conv = Conversation()
        for i in range(10):
            conv.add_message(role="user", content=f"Message {i}")

        assert len(conv) == 10


class TestConversationManager:
    """测试对话管理器"""

    def test_create_conversation(self):
        """测试创建对话"""
        manager = ConversationManager()
        conv = manager.create_conversation(title="New Chat")
        assert conv.id is not None
        assert conv.title == "New Chat"

    def test_get_conversation(self):
        """测试获取对话"""
        manager = ConversationManager()
        conv = manager.create_conversation()

        retrieved = manager.get_conversation(conv.id)
        assert retrieved.id == conv.id

    def test_delete_conversation(self):
        """测试删除对话"""
        manager = ConversationManager()
        conv = manager.create_conversation()

        manager.delete_conversation(conv.id)
        assert manager.get_conversation(conv.id) is None

    def test_list_conversations(self):
        """测试列出对话"""
        manager = ConversationManager()
        manager.create_conversation(title="Chat 1")
        manager.create_conversation(title="Chat 2")

        conversations = manager.list_conversations()
        assert len(conversations) >= 2

    def test_search_conversations(self):
        """测试搜索对话"""
        manager = ConversationManager()
        conv1 = manager.create_conversation(title="Python Help")
        conv1.add_message(role="user", content="How to use lists?")

        conv2 = manager.create_conversation(title="JS Help")
        conv2.add_message(role="user", content="What is a closure?")

        results = manager.search_conversations("lists")
        assert len(results) >= 1

    def test_conversation_limit(self):
        """测试对话数量限制"""
        manager = ConversationManager(max_conversations=3)

        for i in range(5):
            manager.create_conversation(title=f"Chat {i}")

        conversations = manager.list_conversations()
        assert len(conversations) <= 3


class TestMemoryStore:
    """测试记忆存储"""

    def test_store_creation(self):
        """测试创建存储"""
        store = MemoryStore()
        assert store is not None

    def test_save_and_load(self):
        """测试保存和加载"""
        store = MemoryStore()
        temp_file = tempfile.mktemp(suffix=".json")

        try:
            # 保存数据
            data = {"key": "value", "number": 42}
            store.save(temp_file, data)

            # 加载数据
            loaded = store.load(temp_file)
            assert loaded["key"] == "value"
            assert loaded["number"] == 42
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_load_nonexistent(self):
        """测试加载不存在的文件"""
        store = MemoryStore()
        result = store.load("/nonexistent/file.json")
        assert result is None

    def test_append_memory(self):
        """测试追加记忆"""
        store = MemoryStore()

        store.append("session1", {"role": "user", "content": "Hello"})
        store.append("session1", {"role": "assistant", "content": "Hi"})

        memory = store.get("session1")
        assert len(memory) == 2

    def test_clear_memory(self):
        """测试清空记忆"""
        store = MemoryStore()

        store.append("session1", {"role": "user", "content": "Hello"})
        store.clear("session1")

        memory = store.get("session1")
        assert len(memory) == 0

    def test_memory_expiry(self):
        """测试记忆过期"""
        store = MemoryStore()

        store.append("session1", {"role": "user", "content": "Old"})

        # 模拟过期
        store.expiry_seconds = -1  # 已过期
        is_expired = store.is_expired("session1")
        assert is_expired is True

    def test_backup_and_restore(self):
        """测试备份和恢复"""
        store = MemoryStore()
        temp_dir = tempfile.mkdtemp()

        try:
            # 添加数据
            store.append("session1", {"role": "user", "content": "Test"})

            # 备份
            backup_path = os.path.join(temp_dir, "backup.json")
            store.backup(backup_path)

            # 清空
            store.clear("session1")

            # 恢复
            store.restore(backup_path)

            memory = store.get("session1")
            assert len(memory) == 1
        finally:
            import shutil

            shutil.rmtree(temp_dir)


class TestConversationPersistence:
    """测试对话持久化"""

    def test_save_conversation(self):
        """测试保存对话"""
        manager = ConversationManager()
        conv = manager.create_conversation(title="Test")
        conv.add_message(role="user", content="Hello")

        temp_file = tempfile.mktemp(suffix=".json")

        try:
            manager.save_conversation(conv, temp_file)
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_load_conversation(self):
        """测试加载对话"""
        manager = ConversationManager()

        temp_file = tempfile.mktemp(suffix=".json")

        try:
            # 创建并保存对话
            conv = Conversation(id="conv1", title="Test")
            conv.add_message(role="user", content="Hello")
            manager.save_conversation(conv, temp_file)

            # 加载对话
            loaded = manager.load_conversation(temp_file)
            assert loaded.id == "conv1"
            assert len(loaded.messages) == 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestMemoryCompression:
    """测试记忆压缩"""

    def test_compress_long_conversation(self):
        """测试压缩长对话"""
        store = MemoryStore()

        # 添加长对话
        for i in range(100):
            store.append(
                "session1",
                {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}" * 10},
            )

        # 压缩
        store.compress("session1", keep_recent=20)

        memory = store.get("session1")
        assert len(memory) <= 20

    def test_summarize_conversation(self):
        """测试摘要对话"""
        store = MemoryStore()

        # 添加对话
        for i in range(10):
            store.append(
                "session1",
                {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"This is message number {i}",
                },
            )

        # 生成摘要
        summary = store.summarize("session1")
        assert summary is not None
        assert len(summary) > 0


class TestContextWindow:
    """测试上下文窗口管理"""

    def test_context_truncation(self):
        """测试上下文截断"""
        manager = ConversationManager()
        conv = manager.create_conversation()

        # 添加很多消息
        for i in range(50):
            conv.add_message(role="user", content=f"User message {i}")

        # 截断到指定长度
        truncated = conv.get_context_window(max_messages=10)
        assert len(truncated) == 10

    def test_context_tokens_limit(self):
        """测试 token 限制"""
        conv = Conversation()

        # 添加长消息
        for i in range(10):
            long_content = "word " * 100  # 500 words
            conv.add_message(role="user", content=long_content)

        # 获取上下文窗口（按 token）
        context = conv.get_context_window(max_tokens=500)

        # 验证 token 数量
        total_tokens = sum(len(m.content.split()) for m in context)
        assert total_tokens <= 600  # 允许一些误差


class TestConversationExport:
    """测试对话导出"""

    def test_export_json(self):
        """测试导出 JSON"""
        manager = ConversationManager()
        conv = manager.create_conversation(title="Test")
        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi")

        json_export = conv.export_json()
        data = json.loads(json_export)

        assert data["title"] == "Test"
        assert len(data["messages"]) == 2

    def test_export_markdown(self):
        """测试导出 Markdown"""
        manager = ConversationManager()
        conv = manager.create_conversation(title="Test")
        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi there!")

        md_export = conv.export_markdown()

        assert "Test" in md_export
        assert "Hello" in md_export
        assert "Hi there!" in md_export

    def test_export_html(self):
        """测试导出 HTML"""
        manager = ConversationManager()
        conv = manager.create_conversation(title="Test")
        conv.add_message(role="user", content="Hello")

        html_export = conv.export_html()

        assert "Test" in html_export
        assert "Hello" in html_export


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
