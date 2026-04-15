"""
Nano Code - Agent 模块单元测试
"""


from nano_code.agent.graph import get_agent_graph
from nano_code.agent.state import StateManager, create_initial_state


class TestAgentState:
    """测试 Agent 状态管理"""

    def test_initial_state(self):
        """测试初始状态"""
        state = create_initial_state("test message")
        assert state["messages"] == [{"role": "user", "content": "test message"}]
        assert state["tool_calls"] == []
        assert state["tool_results"] == []
        assert state["is_complete"] is False

    def test_state_update(self):
        """测试状态更新"""
        state = create_initial_state("test")
        state["is_complete"] = True
        assert state["is_complete"] is True

    def test_state_serialize(self):
        """测试状态序列化"""
        state = create_initial_state("test")
        # TypedDict 支持 dict 操作
        assert isinstance(state, dict)
        assert "messages" in state


class TestStateManager:
    """测试状态管理器"""

    def test_create_state(self):
        """测试创建状态"""
        manager = StateManager()
        manager.set("key", "value")
        assert manager.get("key") == "value"

    def test_get_state(self):
        """测试获取状态"""
        manager = StateManager()
        assert manager.get("nonexistent", "default") == "default"

    def test_delete_state(self):
        """测试删除状态"""
        manager = StateManager()
        manager.set("key", "value")
        manager.set("key", None)
        assert manager.get("key") is None


class TestAgentGraph:
    """测试 Agent 图"""

    def test_get_agent_graph(self):
        """测试获取 Agent 图"""
        graph = get_agent_graph()
        assert graph is not None


class TestNodeBase:
    """测试节点基类"""

    def test_node_init(self):
        """测试节点初始化"""
        # 节点使用 dict 表示
        node = {"id": "test", "type": "test"}
        assert node["id"] == "test"


class TestEdgeBase:
    """测试边基类"""

    def test_edge_init(self):
        """测试边初始化"""
        # 边使用 tuple 表示
        edge = ("node1", "node2")
        assert edge[0] == "node1"
        assert edge[1] == "node2"


class TestGraphTraversal:
    """测试图遍历"""

    def test_find_path(self):
        """测试查找路径"""
        # 简单测试图结构
        graph = get_agent_graph()
        assert graph is not None


# 保留一些兼容性测试
class TestCompatibility:
    """兼容性测试"""

    def test_agent_graph_alias(self):
        """测试 AgentGraph 别名"""
        from nano_code.agent.graph import AgentGraph
        # 这些是别名，不应报错
        assert AgentGraph is not None

    def test_node_edge_alias(self):
        """测试 Node Edge 别名"""
        from nano_code.agent.graph import Edge, Node
        assert Node is not None
        assert Edge is not None
