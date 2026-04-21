"""Agent handlers for JSON-RPC server."""

from collections.abc import Generator

from .jsonrpc import get_server

# 全局 Agent 实例
_agent = None
_conversation_memory = None


def init_agent():
    """初始化 Agent"""
    global _agent, _conversation_memory

    from jojo_code.agent.graph import get_agent_graph
    from jojo_code.memory.conversation import ConversationMemory

    _agent = get_agent_graph()
    _conversation_memory = ConversationMemory()


def handle_chat(message: str, stream: bool = False) -> dict | Generator:
    """处理聊天请求"""
    if _agent is None:
        init_agent()

    from jojo_code.agent.state import create_initial_state

    state = create_initial_state(message)

    if stream:
        return _stream_chat(state)
    else:
        return _sync_chat(state)


def _sync_chat(state: dict) -> dict:
    """同步聊天"""
    try:
        for chunk in _agent.stream(state):
            # chunk 格式: {'thinking': {...}} 或 {'execute': {...}}
            for node_name, node_state in chunk.items():
                if node_name == "thinking":
                    messages = node_state.get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        content = last_message.get("content", "")
                        if content:
                            return {"content": content}
                    # 检查是否完成
                    if node_state.get("is_complete"):
                        return {"content": "任务完成"}

        return {"content": "No response from agent"}
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"content": f"Error: {e}"}


def _stream_chat(state: dict) -> Generator[dict, None, None]:
    """流式聊天"""
    for event in _agent.stream(state):
        # 处理不同类型的事件
        if "thinking" in event:
            yield {"type": "thinking", "text": event["thinking"]}

        if "tool_calls" in event:
            for tool_call in event["tool_calls"]:
                yield {
                    "type": "tool_call",
                    "tool_name": tool_call.get("name"),
                    "args": tool_call.get("args", {}),
                }

        if "tool_results" in event:
            for result in event["tool_results"]:
                yield {
                    "type": "tool_result",
                    "tool_name": result.get("name"),
                    "result": result.get("result"),
                }

        if "content" in event:
            yield {"type": "content", "text": event["content"]}

    yield {"type": "done"}


def handle_clear() -> dict:
    """清空对话历史"""
    global _conversation_memory
    if _conversation_memory:
        _conversation_memory.clear()
    return {"status": "ok"}


def handle_get_model() -> dict:
    """获取当前模型"""
    from jojo_code.core.config import get_settings

    settings = get_settings()
    return {"model": settings.model}


def handle_get_stats() -> dict:
    """获取会话统计"""
    if _conversation_memory is None:
        return {"messages": 0, "tokens": 0}

    return {
        "messages": len(_conversation_memory.messages),
        "tokens": _conversation_memory.total_tokens,
    }


def register_handlers():
    """注册所有处理器"""
    server = get_server()

    server.register("chat", handle_chat)
    server.register("clear", handle_clear)
    server.register("get_model", handle_get_model)
    server.register("get_stats", handle_get_stats)
