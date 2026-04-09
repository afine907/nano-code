"""Agent 节点实现"""
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from nano_code.agent.state import AgentState

# 最大迭代次数
MAX_ITERATIONS = 50


def get_llm():
    """获取 LLM 实例（延迟导入避免循环依赖）"""
    from nano_code.core.llm import get_llm as _get_llm

    return _get_llm()


def get_tool_registry():
    """获取工具注册表"""
    from nano_code.tools.registry import ToolRegistry

    return ToolRegistry()


def thinking_node(state: AgentState) -> dict:
    """思考节点：调用 LLM 决定下一步行动

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的状态片段
    """
    llm = get_llm()
    registry = get_tool_registry()

    # 转换消息格式
    messages = []
    for msg in state["messages"]:
        if isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
        else:
            messages.append(msg)

    # 添加工具结果到消息
    for result in state["tool_results"]:
        messages.append(ToolMessage(content=result, tool_call_id="tool_call"))

    # 调用 LLM（带工具绑定）
    tools = registry.get_langchain_tools()
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    response = llm_with_tools.invoke(messages)

    # 处理工具调用
    tool_calls = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            tool_calls.append(
                {
                    "name": tc["name"],
                    "args": tc["args"],
                    "id": tc.get("id", "call_" + str(len(tool_calls))),
                }
            )

    # 判断是否完成
    is_complete = len(tool_calls) == 0

    # 添加助手消息到历史
    new_messages = []
    if response.content:
        new_messages.append({"role": "assistant", "content": response.content})

    return {
        "messages": new_messages,
        "tool_calls": tool_calls,
        "tool_results": [],  # 清空上一次的结果
        "is_complete": is_complete,
        "iteration": state["iteration"] + 1,
    }


def execute_node(state: AgentState) -> dict:
    """执行节点：运行工具调用

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的状态片段
    """
    registry = get_tool_registry()
    results = []

    for tool_call in state["tool_calls"]:
        try:
            result = registry.execute(tool_call["name"], tool_call["args"])
            results.append(result)
        except Exception as e:
            results.append(f"Error executing {tool_call['name']}: {e}")

    return {
        "tool_results": results,
        "tool_calls": [],  # 清空工具调用
    }


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """路由函数：决定是否继续循环

    Args:
        state: 当前 Agent 状态

    Returns:
        "continue" 继续执行，"end" 结束循环
    """
    # 有工具调用则继续
    if state["tool_calls"]:
        return "continue"

    # 任务完成
    if state["is_complete"]:
        return "end"

    # 达到最大迭代次数
    if state["iteration"] >= MAX_ITERATIONS:
        return "end"

    return "end"
