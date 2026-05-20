"""WebSocket Server for jojo-code.

基于 FastAPI + WebSocket，将现有 JSON-RPC handlers 包装为 WebSocket 服务。

协议: JSON-RPC 2.0 over WebSocket
流式响应: 同一 request_id 发送多个 chunk，最后发送 done

启动方式:
    python -m jojo_code.server.ws_server
    jojo-code server start
"""

import asyncio
import json
import logging
import os
import traceback
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# ========== 配置 ==========

HOST = os.getenv("JOJO_CODE_HOST", "0.0.0.0")
PORT = int(os.getenv("JOJO_CODE_PORT", "8080"))

# ========== FastAPI App ==========

app = FastAPI(title="jojo-code Server", version="0.2.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Agent 管理 ==========

# 全局 Agent 实例（延迟初始化）
_agent = None
_agent_lock = asyncio.Lock()
_conversation_memory = None
_plugins_initialized = False


async def _ensure_plugins_initialized() -> None:
    """Ensure plugins are initialized (called on first request)"""
    global _plugins_initialized
    if _plugins_initialized:
        return

    from jojo_code.plugin.integration import init_plugins, register_plugin_tools

    # Initialize and load plugins
    init_plugins()

    # Register plugin tools with tool registry
    register_plugin_tools()

    _plugins_initialized = True
    logger.info("Plugins initialized")


async def get_agent():
    """获取 Agent 实例（延迟初始化，线程安全）"""
    global _agent, _conversation_memory
    if _agent is None:
        async with _agent_lock:
            if _agent is None:
                from jojo_code.agent.graph import get_agent_graph
                from jojo_code.memory.conversation import ConversationMemory

                _agent = get_agent_graph()
                _conversation_memory = ConversationMemory()
    return _agent


# ========== JSON-RPC 协议 ==========


@dataclass
class JsonRpcRequest:
    """JSON-RPC 请求"""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str = ""
    params: dict[str, Any] | None = None


@dataclass
class JsonRpcResponse:
    """JSON-RPC 响应"""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    result: Any = None
    error: dict | None = None

    def to_dict(self) -> dict:
        data: dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            data["error"] = self.error
        else:
            data["result"] = self.result
        return data


def make_error_response(req_id: str | int | None, code: int, message: str) -> dict:
    """创建错误响应"""
    return JsonRpcResponse(id=req_id, error={"code": code, "message": message}).to_dict()


# ========== Handler 映射 ==========


def _get_handler(method: str):
    """根据方法名获取 handler"""
    handlers = {
        "chat": handle_chat_ws,
        "clear": handle_clear_ws,
        "get_model": handle_get_model_ws,
        "get_stats": handle_get_stats_ws,
        "permission/mode": handle_permission_mode_ws,
        "permission/confirm": handle_permission_confirm_ws,
        "audit/query": handle_audit_query_ws,
        "audit/stats": handle_audit_stats_ws,
        "audit/recent": handle_audit_recent_ws,
    }
    return handlers.get(method)


# ========== WebSocket Handler ==========


async def handle_chat_ws(params: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """处理聊天请求（支持流式）"""
    message = params.get("message", "")
    stream = params.get("stream", False)

    if not message:
        await _send_response(ws, req_id, {"content": "错误: message 参数不能为空"})
        return

    # Initialize plugins on first request
    await _ensure_plugins_initialized()

    agent = await get_agent()

    from jojo_code.agent.state import create_initial_state

    state = create_initial_state(message)

    # Dispatch before_agent_run hook
    from jojo_code.plugin.hooks import HOOK_BEFORE_AGENT_RUN
    from jojo_code.plugin.integration import dispatch_hook

    dispatch_hook(HOOK_BEFORE_AGENT_RUN, message)

    try:
        if stream:
            await _stream_chat(agent, state, ws, req_id)
        else:
            await _sync_chat(agent, state, ws, req_id)
    finally:
        # Dispatch after_agent_run hook
        from jojo_code.plugin.hooks import HOOK_AFTER_AGENT_RUN

        dispatch_hook(HOOK_AFTER_AGENT_RUN)


async def _sync_chat(agent, state: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """同步聊天"""
    try:
        # 在线程池中运行同步的 agent.stream
        loop = asyncio.get_event_loop()

        def _run():
            for chunk in agent.stream(state):
                for node_name, node_state in chunk.items():
                    if node_name == "thinking":
                        messages = node_state.get("messages", [])
                        if messages:
                            last_message = messages[-1]
                            content = last_message.get("content", "")
                            if content:
                                return {"content": content}
                        if node_state.get("is_complete"):
                            return {"content": "任务完成"}
            return {"content": "No response from agent"}

        result = await loop.run_in_executor(None, _run)
        await _send_response(ws, req_id, result)

    except Exception as e:
        logger.error(f"Chat error: {e}\n{traceback.format_exc()}")
        try:
            await _send_response(ws, req_id, {"content": f"Error: {e}"})
        except Exception:
            pass  # 客户端可能已断开


async def _stream_chat(agent, state: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """流式聊天"""
    try:
        loop = asyncio.get_event_loop()

        # 使用队列在线程和异步之间传递数据
        queue: asyncio.Queue = asyncio.Queue()

        def _run_stream():
            try:
                for event in agent.stream(state):
                    # 将 event 放入队列（同步方式）
                    loop.call_soon_threadsafe(queue.put_nowait, event)

                # 标记完成
                loop.call_soon_threadsafe(queue.put_nowait, None)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, e)

        # 在线程池中启动流式处理
        loop.run_in_executor(None, _run_stream)

        # 从队列中读取并发送
        while True:
            event = await queue.get()

            if event is None:
                # 流结束
                break

            if isinstance(event, Exception):
                await _send_response(ws, req_id, {"type": "error", "message": str(event)})
                break

            # 解析事件并发送
            chunks = _parse_stream_event(event)
            for chunk in chunks:
                await _send_response(ws, req_id, chunk)

        # 发送 done 信号
        await _send_response(ws, req_id, {"type": "done"})

    except Exception as e:
        logger.error(f"Stream chat error: {e}\n{traceback.format_exc()}")
        await _send_response(ws, req_id, {"type": "error", "message": str(e)})


def _parse_stream_event(event: dict) -> list[dict]:
    """解析 agent stream 事件为 WebSocket 响应 chunks"""
    chunks = []

    if "thinking" in event:
        thinking_data = event["thinking"]
        if isinstance(thinking_data, dict):
            messages = thinking_data.get("messages", [])
            for msg in messages:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if content:
                        chunks.append({"type": "thinking", "text": content})
        elif isinstance(thinking_data, str):
            chunks.append({"type": "thinking", "text": thinking_data})

    if "tool_calls" in event:
        for tc in event["tool_calls"]:
            chunks.append(
                {
                    "type": "tool_call",
                    "tool_name": tc.get("name", ""),
                    "args": tc.get("args", {}),
                }
            )

    if "tool_results" in event:
        for tr in event["tool_results"]:
            if isinstance(tr, dict):
                chunks.append(
                    {
                        "type": "tool_result",
                        "tool_name": tr.get("name", ""),
                        "result": tr.get("result", ""),
                    }
                )
            else:
                chunks.append({"type": "tool_result", "result": str(tr)})

    if "content" in event:
        content = event["content"]
        if isinstance(content, dict):
            text = content.get("text", "")
            if text:
                chunks.append({"type": "content", "text": text})
        elif isinstance(content, str):
            chunks.append({"type": "content", "text": content})

    return chunks


async def _send_response(ws: WebSocket, req_id: str | int | None, result: Any) -> None:
    """发送 JSON-RPC 响应"""
    try:
        response = JsonRpcResponse(id=req_id, result=result)
        await ws.send_text(json.dumps(response.to_dict(), ensure_ascii=False))
    except Exception as e:
        logger.warning(f"Failed to send response: {e}")


async def handle_clear_ws(params: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """清空对话历史"""
    global _conversation_memory
    if _conversation_memory:
        _conversation_memory.clear()
    await _send_response(ws, req_id, {"status": "ok"})


async def handle_get_model_ws(params: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """获取当前模型"""
    from jojo_code.core.config import get_settings

    settings = get_settings()
    await _send_response(ws, req_id, {"model": settings.model})


async def handle_get_stats_ws(params: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """获取会话统计"""
    if _conversation_memory is None:
        await _send_response(ws, req_id, {"messages": 0, "tokens": 0})
        return
    await _send_response(
        ws,
        req_id,
        {
            "messages": len(_conversation_memory.messages),
            "tokens": getattr(_conversation_memory, "total_tokens", 0),
        },
    )


async def handle_permission_mode_ws(params: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """获取/设置权限模式"""
    from jojo_code.security.manager import get_permission_manager

    pm = get_permission_manager()
    if pm is None:
        error_msg = "Permission manager not initialized"
        await _send_response(ws, req_id, {"status": "error", "error": error_msg})
        return

    mode = params.get("mode")
    if mode:
        try:
            pm.set_mode(mode)
            await _send_response(ws, req_id, {"status": "ok", "mode": mode})
        except ValueError as e:
            await _send_response(ws, req_id, {"status": "error", "error": str(e)})
    else:
        await _send_response(ws, req_id, {"status": "ok", "mode": pm.mode.value})


async def handle_permission_confirm_ws(
    params: dict, ws: WebSocket, req_id: str | int | None
) -> None:
    """处理权限确认"""
    session_id = params.get("session_id")
    approved = params.get("approved", False)
    result = {"status": "ok", "session_id": session_id, "approved": approved}
    await _send_response(ws, req_id, result)


async def handle_audit_query_ws(params: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """查询审计日志"""
    from jojo_code.security.audit import AuditQuery

    query = AuditQuery()
    results = query.query(
        start_date=params.get("start_date"),
        end_date=params.get("end_date"),
        tool=params.get("tool"),
        allowed=params.get("allowed"),
        risk_level=params.get("risk_level"),
        limit=params.get("limit", 100),
    )
    await _send_response(ws, req_id, {"status": "ok", "results": results, "count": len(results)})


async def handle_audit_stats_ws(params: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """获取审计统计"""
    from jojo_code.security.audit import AuditQuery

    query = AuditQuery()
    stats = query.get_statistics(params.get("date"))
    await _send_response(ws, req_id, {"status": "ok", "statistics": stats})


async def handle_audit_recent_ws(params: dict, ws: WebSocket, req_id: str | int | None) -> None:
    """获取最近审计事件"""
    from jojo_code.security.audit import AuditQuery

    query = AuditQuery()
    limit = params.get("limit", 20)
    results = query.get_recent(limit=limit)
    await _send_response(ws, req_id, {"status": "ok", "results": results})


# ========== WebSocket 端点 ==========


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 主端点

    协议: JSON-RPC 2.0 over WebSocket

    请求格式:
        {"jsonrpc": "2.0", "id": 1, "method": "chat", "params": {"message": "hello"}}

    响应格式:
        {"jsonrpc": "2.0", "id": 1, "result": {"content": "..."}}

    流式响应:
        同一 id 发送多个 result，最后发送 {"type": "done"}
    """
    await websocket.accept()
    logger.info("Client connected")

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            # 解析 JSON-RPC 请求
            try:
                request_data = json.loads(data)
                request = JsonRpcRequest(
                    jsonrpc=request_data.get("jsonrpc", "2.0"),
                    id=request_data.get("id"),
                    method=request_data.get("method", ""),
                    params=request_data.get("params"),
                )
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps(make_error_response(None, -32700, "Parse error"))
                )
                continue

            # 获取 handler
            handler = _get_handler(request.method)
            if handler is None:
                error_msg = f"Method not found: {request.method}"
                await websocket.send_text(
                    json.dumps(make_error_response(request.id, -32601, error_msg))
                )
                continue

            # 执行 handler
            try:
                await handler(request.params or {}, websocket, request.id)
            except Exception as e:
                logger.error(f"Handler error: {e}\n{traceback.format_exc()}")
                await websocket.send_text(
                    json.dumps(make_error_response(request.id, -32603, str(e)))
                )

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}\n{traceback.format_exc()}")


# ========== HTTP 端点 ==========


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "0.2.0"}


# ========== 启动入口 ==========


def main():
    """启动 WebSocket 服务"""
    import uvicorn

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    logger.info(f"Starting jojo-code server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
