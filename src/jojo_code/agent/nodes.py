"""Agent 节点实现"""

from typing import Any, Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from jojo_code.agent.modes import PlanMode
from jojo_code.agent.state import AgentState
from jojo_code.tools.registry import ToolRegistry

# 最大迭代次数
MAX_ITERATIONS = 50

# 为了向后兼容，提供节点类型别名
ThinkNode = None  # 占位符
ObserveNode = None  # 占位符
ActNode = None  # 占位符
RouterNode = None  # 占位符


def get_llm() -> BaseChatModel:
    """获取 LLM 实例（延迟导入避免循环依赖）"""
    from jojo_code.core.llm import get_llm as _get_llm

    return _get_llm()


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表"""
    from jojo_code.tools.registry import get_tool_registry as _get_tool_registry

    return _get_tool_registry()


def thinking_node(state: AgentState) -> dict[str, Any]:
    """思考节点：调用 LLM 决定下一步行动

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的状态片段
    """
    llm = get_llm()
    registry = get_tool_registry()

    # 读取模式，PlanMode.BUILD 为构建模式，PlanMode.PLAN 为计划模式
    mode = state.get("mode", PlanMode.BUILD.value)

    # 转换消息格式
    messages: list[BaseMessage] = []
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
            # 已经是消息对象
            messages.append(msg)

    # 添加工具结果到消息
    tool_calls = state.get("tool_calls", [])
    for i, result in enumerate(state["tool_results"]):
        tool_call_id = tool_calls[i].get("id", f"call_{i}") if i < len(tool_calls) else f"call_{i}"
        messages.append(ToolMessage(content=result, tool_call_id=tool_call_id))

    # 调用 LLM（根据模式决定是否绑定工具）
    tools = registry.get_langchain_tools()
    if mode == PlanMode.PLAN.value:
        # Plan 模式：不绑定工具，LLM 只给出计划文本
        llm_with_tools = llm
    else:
        llm_with_tools = llm.bind_tools(tools) if tools else llm

    # 支持流式响应
    response = llm_with_tools.invoke(messages)

    # 处理工具调用
    tool_calls: list[dict[str, Any]] = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            tool_calls.append(
                {
                    "name": tc["name"],
                    "args": tc["args"],
                    "id": tc.get("id", "call_" + str(len(tool_calls))),
                }
            )

    # Plan 模式额外处理：如果是 PLAN 模式，且有写操作的 tool_calls，需要阻止执行并给出计划
    if mode == PlanMode.PLAN.value and tool_calls:
        # 过滤出写操作（需要阻止执行）
        write_tools = [
            tc for tc in tool_calls if registry._tool_categories.get(tc["name"], "read") == "write"
        ]
        if write_tools:
            plan_ops = []
            for tc in write_tools:
                plan_ops.append(f"{tc['name']}({tc['args']})")
            plan_text = (
                "Plan 模式阻止写操作。将要执行的写操作: "
                + ", ".join(plan_ops)
                + ". 这是只读计划，实际执行将切换回 BUILD 模式或继续分析。"
            )
            new_messages: list[dict[str, Any]] = [{"role": "assistant", "content": plan_text}]
            return {
                "messages": new_messages,
                "tool_calls": [],
                "tool_results": [],
                "is_complete": True,
                "iteration": state["iteration"] + 1,
            }

    # 判断是否完成
    is_complete = len(tool_calls) == 0

    # 添加助手消息到历史（保留之前的消息）
    # 获取之前的消息并添加新的助手消息
    existing_messages = state.get("messages", [])
    new_messages: list[dict[str, Any]] = []

    # 保留之前非空的消息
    for msg in existing_messages:
        if isinstance(msg, dict) and msg.get("content"):
            new_messages.append(msg)
        elif hasattr(msg, "content") and msg.content:  # 消息对象
            new_messages.append({"role": "assistant", "content": msg.content})

    # 添加当前轮的助手消息
    if response.content:
        content = response.content if isinstance(response.content, str) else str(response.content)
        new_messages.append({"role": "assistant", "content": content})

    return {
        "messages": new_messages,
        "tool_calls": tool_calls,
        "tool_results": [],  # 清空上一次的结果
        "is_complete": is_complete,
        "iteration": state["iteration"] + 1,
    }


def execute_node(state: AgentState) -> dict[str, Any]:
    """执行节点：运行工具调用

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的状态片段
    """
    registry = get_tool_registry()
    results: list[str] = []

    for tool_call in state["tool_calls"]:
        try:
            if "name" not in tool_call or "args" not in tool_call:
                results.append("Error: tool_call missing 'name' or 'args' key")
                continue
            result = registry.execute(tool_call["name"], tool_call["args"])
            results.append(result)
        except Exception as e:
            results.append(f"Error executing {tool_call.get('name', 'unknown')}: {e}")

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
