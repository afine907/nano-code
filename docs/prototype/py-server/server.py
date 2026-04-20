#!/usr/bin/env python3
"""JSON-RPC Server for Nano Code CLI

This server provides a JSON-RPC 2.0 interface over stdio for the TypeScript CLI.
"""

import asyncio
import json
import sys
from typing import Any, AsyncIterator
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class StreamEvent:
    """流式事件"""
    type: str  # thinking | tool_call | tool_result | response | done
    content: str
    metadata: dict | None = None
    
    def to_dict(self) -> dict:
        result = {"type": self.type, "content": self.content}
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class JSONRPCServer:
    """JSON-RPC 2.0 Server over stdio"""
    
    def __init__(self):
        self.request_id = 0
        self._setup_agent()
    
    def _setup_agent(self):
        """初始化 Agent"""
        try:
            from nano_code.agent.graph import get_agent_graph
            from nano_code.tools.registry import get_tool_registry
            from nano_code.core.config import get_settings
            
            self.graph = get_agent_graph()
            self.registry = get_tool_registry()
            self.settings = get_settings()
        except ImportError as e:
            print(f"Warning: Could not import agent modules: {e}", file=sys.stderr)
            self.graph = None
            self.registry = None
            self.settings = None
    
    def _send_response(self, response: dict) -> None:
        """发送响应"""
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    
    def _send_notification(self, method: str, params: dict) -> None:
        """发送通知（无 id）"""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        sys.stdout.write(json.dumps(notification) + "\n")
        sys.stdout.flush()
    
    async def handle_request(self, request: dict) -> None:
        """处理 JSON-RPC 请求"""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            # 方法映射
            method_map = {
                "agent.stream": self._handle_agent_stream,
                "tools.list": self._handle_tools_list,
                "tool.execute": self._handle_tool_execute,
                "config.get": self._handle_config_get,
                "config.set": self._handle_config_set,
            }
            
            handler = method_map.get(method)
            if not handler:
                self._send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                })
                return
            
            result = await handler(params)
            
            # 流式方法不返回结果（通过通知发送）
            if method != "agent.stream":
                self._send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                })
        
        except Exception as e:
            self._send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(e)}
            })
    
    async def _handle_agent_stream(self, params: dict) -> None:
        """流式对话"""
        prompt = params.get("prompt", "")
        mode = params.get("mode", "build")
        
        if not self.graph:
            self._send_notification("stream", {
                "type": "error",
                "content": "Agent not initialized"
            })
            return
        
        from nano_code.agent.state import create_initial_state
        
        state = create_initial_state(prompt, mode=mode)
        
        try:
            # 流式执行
            for chunk in self.graph.stream(state):
                for node_name, node_output in chunk.items():
                    if node_name == "thinking":
                        # 思考节点
                        messages = node_output.get("messages", [])
                        for msg in messages:
                            if isinstance(msg, dict):
                                content = msg.get("content", "")
                            else:
                                content = getattr(msg, "content", "")
                            
                            if content:
                                self._send_notification("stream", {
                                    "type": "response",
                                    "content": content
                                })
                        
                        # 工具调用
                        tool_calls = node_output.get("tool_calls", [])
                        for tc in tool_calls:
                            self._send_notification("stream", {
                                "type": "tool_call",
                                "content": f"Calling {tc['name']}...",
                                "metadata": {
                                    "toolName": tc["name"],
                                    "toolArgs": tc["args"]
                                }
                            })
                    
                    elif node_name == "execute":
                        # 执行结果
                        results = node_output.get("tool_results", [])
                        for result in results:
                            self._send_notification("stream", {
                                "type": "tool_result",
                                "content": result[:500] + "..." if len(result) > 500 else result
                            })
            
            # 完成
            self._send_notification("stream", {"type": "done", "content": ""})
        
        except Exception as e:
            self._send_notification("stream", {
                "type": "error",
                "content": str(e)
            })
    
    async def _handle_tools_list(self, params: dict) -> dict:
        """获取工具列表"""
        if not self.registry:
            return {"tools": []}
        
        tools = []
        for name, tool in self.registry._tools.items():
            tools.append({
                "name": name,
                "description": getattr(tool, "description", ""),
                "parameters": {}
            })
        
        return {"tools": tools}
    
    async def _handle_tool_execute(self, params: dict) -> dict:
        """执行工具"""
        name = params.get("name")
        args = params.get("args", {})
        
        if not self.registry:
            return {"success": False, "error": "Registry not initialized"}
        
        try:
            result = self.registry.execute(name, args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_config_get(self, params: dict) -> dict:
        """获取配置"""
        if not self.settings:
            return {"model": "gpt-4o-mini", "provider": "unknown"}
        
        return {
            "model": self.settings.model,
            "provider": "openai" if self.settings.openai_api_key else "unknown"
        }
    
    async def _handle_config_set(self, params: dict) -> dict:
        """设置配置"""
        # TODO: 实现配置设置
        return {"success": True}
    
    async def run(self) -> None:
        """运行服务器"""
        print("Nano Code JSON-RPC Server started", file=sys.stderr)
        
        # 从 stdin 读取请求
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # 异步读取一行
                line = await loop.run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # 解析请求
                request = json.loads(line)
                
                # 处理请求
                await self.handle_request(request)
            
            except json.JSONDecodeError as e:
                self._send_response({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                })
            
            except KeyboardInterrupt:
                break
            
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)


def main():
    """入口"""
    server = JSONRPCServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
