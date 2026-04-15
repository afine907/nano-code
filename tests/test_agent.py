"""
Nano Code - Agent 模块单元测试
"""

import pytest

from nano_code.agent.graph import AgentGraph, Edge, Node
from nano_code.agent.nodes import ActNode, ObserveNode, RouterNode, ThinkNode
from nano_code.agent.state import AgentState, StateManager


class TestAgentState:
    """测试 Agent 状态管理"""

    def test_initial_state(self):
        """测试初始状态"""
        state = AgentState()
        assert state.goal is None
        assert state.history == []
        assert state.context == {}

    def test_state_update(self):
        """测试状态更新"""
        state = AgentState()
        state.update(goal="test goal")
        assert state.goal == "test goal"

    def test_state_serialize(self):
        """测试状态序列化"""
        state = AgentState()
        state.goal = "test"
        state.context = {"key": "value"}
        data = state.to_dict()
        assert data["goal"] == "test"
        assert data["context"]["key"] == "value"


class TestStateManager:
    """测试状态管理器"""

    def test_create_state(self):
        """测试创建状态"""
        manager = StateManager()
        state = manager.create("session1")
        assert state.session_id == "session1"

    def test_get_state(self):
        """测试获取状态"""
        manager = StateManager()
        manager.create("session1")
        state = manager.get("session1")
        assert state.session_id == "session1"

    def test_delete_state(self):
        """测试删除状态"""
        manager = StateManager()
        manager.create("session1")
        manager.delete("session1")
        assert manager.get("session1") is None


class TestAgentGraph:
    """测试 Agent 图结构"""

    def test_add_node(self):
        """测试添加节点"""
        graph = AgentGraph()
        node = Node(id="node1", name="Test Node")
        graph.add_node(node)
        assert "node1" in graph.nodes

    def test_add_edge(self):
        """测试添加边"""
        graph = AgentGraph()
        node1 = Node(id="node1", name="Node 1")
        node2 = Node(id="node2", name="Node 2")
        graph.add_node(node1)
        graph.add_node(node2)
        edge = Edge(from_node="node1", to_node="node2")
        graph.add_edge(edge)
        assert len(graph.edges) == 1

    def test_execute(self):
        """测试图执行"""
        graph = AgentGraph()
        node = ThinkNode("think1")
        graph.add_node(node)

        state = AgentState()
        result = graph.execute(state)
        assert result is not None


class TestThinkNode:
    """测试思考节点"""

    @pytest.mark.asyncio
    async def test_execute(self):
        """测试执行"""
        node = ThinkNode("think1")
        state = AgentState(goal="test")
        result = await node.execute(state)
        assert result is not None


class TestActNode:
    """测试行动节点"""

    @pytest.mark.asyncio
    async def test_execute(self):
        """测试执行"""
        node = ActNode("act1")
        state = AgentState(goal="test")
        result = await node.execute(state)
        assert result is not None


class TestObserveNode:
    """测试观察节点"""

    @pytest.mark.asyncio
    async def test_execute(self):
        """测试执行"""
        node = ObserveNode("observe1")
        state = AgentState()
        result = await node.execute(state)
        assert result is not None


class TestRouterNode:
    """测试路由节点"""

    @pytest.mark.asyncio
    async def test_route(self):
        """测试路由"""
        node = RouterNode("router1", routes={"a": "node1", "b": "node2"})
        state = AgentState(context={"route": "a"})
        result = await node.execute(state)
        assert result == "node1"


class TestNodeBase:
    """测试节点基类"""

    def test_node_init(self):
        """测试节点初始化"""
        node = Node(id="test", name="Test")
        assert node.id == "test"
        assert node.name == "Test"

    def test_node_metadata(self):
        """测试节点元数据"""
        node = Node(id="test", name="Test", metadata={"key": "value"})
        assert node.metadata["key"] == "value"


class TestEdgeBase:
    """测试边基类"""

    def test_edge_init(self):
        """测试边初始化"""
        edge = Edge(from_node="a", to_node="b")
        assert edge.from_node == "a"
        assert edge.to_node == "b"

    def test_edge_condition(self):
        """测试边条件"""
        edge = Edge(from_node="a", to_node="b", condition=lambda x: x > 0)
        assert edge.condition(1) is True
        assert edge.condition(-1) is False


class TestGraphTraversal:
    """测试图遍历"""

    def test_find_path(self):
        """测试查找路径"""
        graph = AgentGraph()
        graph.add_node(Node(id="start"))
        graph.add_node(Node(id="end"))
        graph.add_edge(Edge("start", "end"))

        path = graph.find_path("start", "end")
        assert path == ["start", "end"]

    def test_cycles(self):
        """测试循环检测"""
        graph = AgentGraph()
        graph.add_node(Node(id="a"))
        graph.add_node(Node(id="b"))
        graph.add_edge(Edge("a", "b"))
        graph.add_edge(Edge("b", "a"))

        has_cycle = graph.has_cycle()
        assert has_cycle is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
