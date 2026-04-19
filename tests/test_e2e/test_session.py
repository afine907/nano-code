"""CLI 会话持久化测试

配置方式（设置环境变量）：
- OPENAI_API_KEY: LongCat API Key
- OPENAI_BASE_URL: https://api.longcat.chat/openai/v1

运行:
  - pytest tests/test_e2e/test_session.py -v  # 基础测试
  - pytest -m longcat tests/test_e2e/test_session.py -v  # 需要 API
"""

import os

import pytest
from langchain_core.messages import HumanMessage

from nano_code.memory.conversation import ConversationMemory

pytestmark = pytest.mark.longcat


class TestSessionBasic:
    """基础会话测试（不需要 API）"""

    def test_conversation_save_and_restore(self, tmp_path):
        """测试：对话 → 保存 → 重启 → 历史恢复"""
        storage = tmp_path / "session.json"

        memory = ConversationMemory(storage_path=storage, auto_save=True)
        memory.add_message(HumanMessage(content="Hello"))
        memory.add_message(HumanMessage(content="World"))

        memory2 = ConversationMemory(storage_path=storage)
        context = memory2.get_context()

        assert len(context) == 2
        assert context[0].content == "Hello"
        assert context[1].content == "World"

    def test_conversation_clear(self, tmp_path):
        """测试：清空会话"""
        storage = tmp_path / "clear.json"

        memory = ConversationMemory(storage_path=storage)
        memory.add_message(HumanMessage(content="Test"))
        memory.clear()

        context = memory.get_context()
        assert len(context) == 0

    def test_token_count(self):
        """测试：token 计数"""
        memory = ConversationMemory()

        memory.add_message(HumanMessage(content="Hello"))
        memory.add_message(HumanMessage(content="World"))

        count = memory.token_count()
        assert count > 0

    def test_message_retrieval(self):
        """测试：获取消息"""
        memory = ConversationMemory()

        memory.add_message(HumanMessage(content="Hello"))
        memory.add_message(HumanMessage(content="World"))
        memory.add_message(HumanMessage(content="Test"))

        context = memory.get_context()
        assert len(context) == 3

        last_one = memory.get_last_n_messages(1)
        assert len(last_one) == 1


@pytest.fixture
def longcat_configured():
    """检查 LongCat 配置是否完整"""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY 未设置")
    if not os.getenv("OPENAI_BASE_URL"):
        pytest.skip("OPENAI_BASE_URL 未设置")


class TestSessionWithAgent:
    """需要 Agent 的会话测试（需要 API）"""

    @pytest.mark.slow
    def test_full_conversation_with_agent(
        self, longcat_configured, tmp_path
    ):
        """测试：完整对话链 + 持久化 + 恢复"""
        from nano_code.agent.graph import build_agent_graph
        from nano_code.agent.state import create_initial_state

        storage = tmp_path / "full.json"
        memory = ConversationMemory(storage_path=storage, auto_save=True)

        graph = build_agent_graph()
        state = create_initial_state("你好")
        result = graph.invoke(state)

        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            content = (
                last_msg.content
                if hasattr(last_msg, "content")
                else last_msg.get("content")
            )
            memory.add_message(HumanMessage(content="用户: 你好"))
            memory.add_message(HumanMessage(content=content or "响应"))

        memory2 = ConversationMemory(storage_path=storage)
        context = memory2.get_context()

        assert len(context) >= 2
        print(f"\n恢复的会话: {len(context)} 条消息")