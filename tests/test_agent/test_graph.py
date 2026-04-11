"""Agent 图测试"""

from unittest.mock import MagicMock, patch

from nano_code.agent.graph import build_agent_graph
from nano_code.agent.state import AgentState


class TestAgentGraph:
    """Agent 状态图测试"""

    def test_graph_has_required_nodes(self):
        """图应该包含必需的节点"""
        graph = build_agent_graph()

        # 获取图的节点名称
        node_names = list(graph.nodes.keys())

        # 应该有 thinking 和 execute 节点
        assert "thinking" in node_names
        assert "execute" in node_names

    def test_graph_has_entry_point(self):
        """图应该有入口点"""
        graph = build_agent_graph()

        # LangGraph 编译后的图应该可以执行
        assert graph is not None


class TestAgentState:
    """Agent 状态测试"""

    def test_state_default_values(self):
        """状态应该有默认值"""
        state = AgentState(
            messages=[],
            tool_calls=[],
            tool_results=[],
            is_complete=False,
            iteration=0,
        )

        assert state["messages"] == []
        assert state["tool_calls"] == []
        assert state["tool_results"] == []
        assert state["is_complete"] is False
        assert state["iteration"] == 0

    def test_state_can_add_messages(self):
        """状态应该能添加消息"""
        new_state = AgentState(
            messages=[{"role": "user", "content": "Hello"}],
            tool_calls=[],
            tool_results=[],
            is_complete=False,
            iteration=0,
        )

        assert len(new_state["messages"]) == 1


class TestThinkingNode:
    """thinking 节点测试"""

    @patch("nano_code.agent.nodes.get_llm")
    def test_generates_response_without_tools(self, mock_get_llm):
        """没有工具调用时应该生成响应"""
        from nano_code.agent.nodes import thinking_node

        # Mock LLM 响应
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="你好！我是助手。",
            tool_calls=[],
        )
        mock_get_llm.return_value = mock_llm

        state = AgentState(
            messages=[{"role": "user", "content": "你好"}],
            tool_calls=[],
            tool_results=[],
            is_complete=False,
            iteration=0,
        )

        result = thinking_node(state)

        # 应该生成了响应
        assert result["is_complete"] is True

    @patch("nano_code.agent.nodes.get_llm")
    def test_generates_tool_calls(self, mock_get_llm):
        """需要操作时应该生成工具调用"""
        from nano_code.agent.nodes import thinking_node

        # Mock LLM 响应 - tool_calls 需要返回正确格式
        mock_response = MagicMock()
        mock_response.content = ""
        # tool_calls 需要是 dict 格式，不是 MagicMock
        mock_response.tool_calls = [
            {"name": "read_file", "args": {"path": "README.md"}, "id": "call_1"}
        ]

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        # bind_tools 返回自身
        mock_llm.bind_tools.return_value = mock_llm
        mock_get_llm.return_value = mock_llm

        state = AgentState(
            messages=[{"role": "user", "content": "读取 README.md"}],
            tool_calls=[],
            tool_results=[],
            is_complete=False,
            iteration=0,
        )

        result = thinking_node(state)

        # 应该有工具调用
        assert len(result["tool_calls"]) == 1
        assert result["is_complete"] is False


class TestExecuteNode:
    """execute 节点测试"""

    @patch("nano_code.agent.nodes.get_tool_registry")
    def test_executes_tool_calls(self, mock_get_registry):
        """应该执行工具调用"""
        from nano_code.agent.nodes import execute_node

        # Mock 工具注册表
        mock_registry = MagicMock()
        mock_registry.execute.return_value = "file content here"
        mock_get_registry.return_value = mock_registry

        state = AgentState(
            messages=[],
            tool_calls=[{"name": "read_file", "args": {"path": "test.txt"}, "id": "call_123"}],
            tool_results=[],
            is_complete=False,
            iteration=0,
        )

        result = execute_node(state)

        # 应该有工具结果
        assert len(result["tool_results"]) == 1
        assert "file content" in result["tool_results"][0]
        # 工具调用应该被清空
        assert result["tool_calls"] == []


class TestShouldContinue:
    """路由函数测试"""

    def test_continues_when_tool_calls_exist(self):
        """有工具调用时应该继续"""
        from nano_code.agent.nodes import should_continue

        state = AgentState(
            messages=[],
            tool_calls=[{"name": "test", "args": {}, "id": "1"}],
            tool_results=[],
            is_complete=False,
            iteration=1,
        )

        result = should_continue(state)
        assert result == "continue"

    def test_ends_when_complete(self):
        """完成时应该结束"""
        from nano_code.agent.nodes import should_continue

        state = AgentState(
            messages=[],
            tool_calls=[],
            tool_results=[],
            is_complete=True,
            iteration=1,
        )

        result = should_continue(state)
        assert result == "end"

    def test_ends_on_max_iterations(self):
        """达到最大迭代次数应该结束"""
        from nano_code.agent.nodes import should_continue

        state = AgentState(
            messages=[],
            tool_calls=[],
            tool_results=[],
            is_complete=False,
            iteration=100,  # 超过限制
        )

        result = should_continue(state)
        assert result == "end"
