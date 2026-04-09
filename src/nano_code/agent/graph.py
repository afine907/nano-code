"""LangGraph 状态图定义"""
from langgraph.graph import END, StateGraph

from nano_code.agent.nodes import execute_node, should_continue, thinking_node
from nano_code.agent.state import AgentState


def build_agent_graph() -> StateGraph:
    """构建 Agent 状态图

    图结构:
        START -> thinking -> [continue -> execute -> thinking] or [end -> END]

    Returns:
        编译后的 LangGraph 图
    """
    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("thinking", thinking_node)
    workflow.add_node("execute", execute_node)

    # 设置入口点
    workflow.set_entry_point("thinking")

    # 添加条件边
    workflow.add_conditional_edges(
        "thinking",
        should_continue,
        {
            "continue": "execute",
            "end": END,
        },
    )

    # 执行后返回思考
    workflow.add_edge("execute", "thinking")

    return workflow.compile()


# 全局图实例（延迟创建）
_graph = None


def get_agent_graph():
    """获取 Agent 图实例（单例）"""
    global _graph
    if _graph is None:
        _graph = build_agent_graph()
    return _graph
