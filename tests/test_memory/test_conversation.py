"""记忆系统测试"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from nano_code.memory.conversation import ConversationMemory


class TestConversationMemory:
    """对话记忆管理测试"""

    def test_add_message(self):
        """应该能添加消息"""
        memory = ConversationMemory()

        memory.add_message(HumanMessage(content="你好"))

        assert len(memory.messages) == 1
        assert memory.messages[0].content == "你好"

    def test_add_multiple_messages(self):
        """应该能添加多条消息"""
        memory = ConversationMemory()

        memory.add_message(HumanMessage(content="问题1"))
        memory.add_message(AIMessage(content="回答1"))
        memory.add_message(HumanMessage(content="问题2"))

        assert len(memory.messages) == 3

    def test_token_count(self):
        """应该能计算 token 数量"""
        memory = ConversationMemory()

        memory.add_message(HumanMessage(content="Hello World"))

        count = memory.token_count()
        assert count > 0

    def test_token_count_with_multiple_messages(self):
        """多条消息的 token 计数应该累加"""
        memory = ConversationMemory()

        memory.add_message(HumanMessage(content="Hello"))
        memory.add_message(AIMessage(content="Hi there!"))

        count = memory.token_count()
        assert count > 3  # 至少包含一些 tokens

    def test_get_context(self):
        """应该返回适合 LLM 的上下文"""
        memory = ConversationMemory()
        memory.add_message(HumanMessage(content="User message"))

        context = memory.get_context()

        assert isinstance(context, list)
        assert len(context) == 1

    def test_clear_memory(self):
        """应该能清空记忆"""
        memory = ConversationMemory()
        memory.add_message(HumanMessage(content="Test"))

        memory.clear()

        assert len(memory.messages) == 0

    def test_get_last_n_messages(self):
        """应该能获取最近 N 条消息"""
        memory = ConversationMemory()

        for i in range(10):
            memory.add_message(HumanMessage(content=f"Message {i}"))

        last_3 = memory.get_last_n_messages(3)

        assert len(last_3) == 3
        assert "Message 7" in last_3[0].content
        assert "Message 9" in last_3[2].content


class TestMemoryCompression:
    """记忆压缩测试"""

    def test_compress_when_exceeds_limit(self):
        """超过限制时应该压缩"""
        memory = ConversationMemory(max_tokens=100)

        # 添加大量消息
        for i in range(50):
            memory.add_message(HumanMessage(content=f"Message {i}" * 50))

        # 应该触发压缩，消息数量应该减少
        # 原始 50 条，压缩后应该 <= 22 (20 条最近 + 1 条摘要 + 可能有系统消息)
        assert len(memory.messages) <= 25

    def test_compress_preserves_system_messages(self):
        """压缩时应该保留系统消息"""
        memory = ConversationMemory(max_tokens=100)

        memory.add_message(SystemMessage(content="You are a helpful assistant."))
        for i in range(30):
            memory.add_message(HumanMessage(content=f"User {i}" * 30))

        # 系统消息应该被保留
        system_messages = [m for m in memory.messages if isinstance(m, SystemMessage)]
        assert len(system_messages) > 0

    def test_compress_preserves_recent_messages(self):
        """压缩时应该保留最近的消息"""
        memory = ConversationMemory(max_tokens=100)

        for i in range(50):
            memory.add_message(HumanMessage(content=f"Message {i}" * 30))

        # 最近的消息应该被保留
        recent = memory.get_last_n_messages(5)
        assert len(recent) == 5
        assert "Message 49" in recent[-1].content


class TestMemoryPersistence:
    """记忆持久化测试"""

    def test_save_and_load(self, tmp_path):
        """应该能保存和加载记忆"""
        memory = ConversationMemory(storage_path=tmp_path / "memory.json")
        memory.add_message(HumanMessage(content="Test message"))

        # 保存
        memory.save()

        # 加载到新实例
        memory2 = ConversationMemory(storage_path=tmp_path / "memory.json")
        memory2.load()

        assert len(memory2.messages) == 1
        assert memory2.messages[0].content == "Test message"

    def test_auto_save_on_add(self, tmp_path):
        """添加消息时应该自动保存（如果配置了）"""
        memory = ConversationMemory(storage_path=tmp_path / "memory.json", auto_save=True)

        memory.add_message(HumanMessage(content="Test"))

        # 文件应该存在
        assert (tmp_path / "memory.json").exists()
