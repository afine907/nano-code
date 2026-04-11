"""Agent 状态定义"""

from typing import Annotated, Any

from typing_extensions import TypedDict


def merge_lists(left: list[Any] | None, right: list[Any] | None) -> list[Any]:
    """合并两个列表（用于 Annotated reducer）"""
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


class AgentState(TypedDict):
    """Agent 状态

    Attributes:
        messages: 对话历史
        tool_calls: 待执行的工具调用
        tool_results: 工具执行结果
        is_complete: 任务是否完成
        iteration: 当前循环次数
    """

    messages: Annotated[list[dict[str, Any]], merge_lists]
    tool_calls: list[dict[str, Any]]
    tool_results: list[str]
    is_complete: bool
    iteration: int


def create_initial_state(user_message: str) -> AgentState:
    """创建初始状态

    Args:
        user_message: 用户输入消息

    Returns:
        初始化的 Agent 状态
    """
    return AgentState(
        messages=[{"role": "user", "content": user_message}],
        tool_calls=[],
        tool_results=[],
        is_complete=False,
        iteration=0,
    )
