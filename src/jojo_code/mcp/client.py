"""MCP 客户端 - 支持 MCP 协议的工具调用"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp

from jojo_code.core.exceptions import NetworkError


@dataclass
class MCPConfig:
    """MCP 服务器配置"""

    name: str  # 服务器名称
    url: str  # 服务器 URL
    transport: str = "stdio"  # 传输方式: stdio/http/sse
    auth: dict[str, str] = field(default_factory=dict)  # 认证信息
    timeout: float = 30.0  # 超时时间
    retry: int = 3  # 重试次数


@dataclass
class MCPTool:
    """MCP 工具"""

    name: str  # 工具名称
    description: str = ""  # 工具描述
    input_schema: dict[str, Any] = field(default_factory=dict)  # 输入 schema


@dataclass
class MCPResource:
    """MCP 资源"""

    uri: str  # 资源 URI
    name: str = ""  # 资源名称
    description: str = ""  # 资源描述
    mime_type: str = "text/plain"  # MIME 类型


class MCPClient:
    """MCP 客户端

    支持连接到 MCP 服务器并调用工具。
    """

    def __init__(self, config: MCPConfig):
        self.config = config
        self._tools: dict[str, MCPTool] = {}
        self._resources: dict[str, MCPResource] = {}
        self._connected = False
        self._process: asyncio.subprocess.Process | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """连接到 MCP 服务器"""
        if self._connected:
            return

        if self.config.transport == "stdio":
            await self._connect_stdio()
        elif self.config.transport in ("http", "sse"):
            await self._connect_http()
        else:
            raise ValueError(f"不支持的传输方式: {self.config.transport}")

        self._connected = True
        await self._discover_tools()

    async def _connect_stdio(self) -> None:
        """通过 stdio 连接"""
        # 解析命令
        cmd = self.config.url.split()
        if not cmd:
            raise ValueError("无效的 stdio 命令")

        # 启动进程
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def _connect_http(self) -> None:
        """通过 HTTP 连接"""
        import aiohttp

        self._session = aiohttp.ClientSession()

    async def _discover_tools(self) -> None:
        """发现可用工具"""
        # 发送 tools/list 请求
        result = await self._send_request("tools/list")

        if "tools" in result:
            for tool_data in result["tools"]:
                tool = MCPTool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                )
                self._tools[tool.name] = tool

    async def _send_request(self, method: str, params: dict | None = None) -> dict:
        """发送 MCP 请求"""
        request = {
            "jsonrpc": "2.0",
            "id": datetime.now().timestamp(),
            "method": method,
            "params": params or {},
        }

        if self.config.transport == "stdio":
            return await self._send_stdio(request)
        else:
            return await self._send_http(request)

    async def _send_stdio(self, request: dict) -> dict:
        """通过 stdio 发送请求"""
        if not self._process:
            raise RuntimeError("未连接到 MCP 服务器")

        # 发送请求
        request_json = json.dumps(request) + "\n"
        self._process.stdin.write(request_json.encode())
        await self._process.stdin.drain()

        # 读取响应
        response_line = await self._process.stdout.readline()
        return json.loads(response_line.decode())

    async def _send_http(self, request: dict) -> dict:
        """通过 HTTP 发送请求"""
        if not hasattr(self, "_session"):
            raise RuntimeError("未连接到 MCP 服务器")

        async with self._session.post(
            self.config.url,
            json=request,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
        ) as resp:
            return await resp.json()

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """调用 MCP 工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if not self._connected:
            await self.connect()

        result = await self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )

        if "error" in result:
            raise NetworkError(f"MCP 工具调用失败: {result['error']}")

        return result.get("result")

    def list_tools(self) -> list[MCPTool]:
        """列出所有可用工具"""
        return list(self._tools.values())

    def get_tool(self, name: str) -> MCPTool | None:
        """获取工具"""
        return self._tools.get(name)

    async def list_resources(self) -> list[MCPResource]:
        """列出所有资源"""
        result = await self._send_request("resources/list")

        resources = []
        if "resources" in result:
            for res_data in result["resources"]:
                resource = MCPResource(
                    uri=res_data.get("uri", ""),
                    name=res_data.get("name", ""),
                    description=res_data.get("description", ""),
                    mime_type=res_data.get("mimeType", "text/plain"),
                )
                resources.append(resource)
                self._resources[resource.uri] = resource

        return resources

    async def read_resource(self, uri: str) -> str:
        """读取资源内容"""
        result = await self._send_request(
            "resources/read",
            {
                "uri": uri,
            },
        )

        if "contents" in result and result["contents"]:
            return result["contents"][0].get("text", "")

        return ""

    async def close(self) -> None:
        """关闭连接"""
        if self._process:
            self._process.terminate()
            await self._process.wait()

        if hasattr(self, "_session"):
            await self._session.close()

        self._connected = False


class MCPClientManager:
    """MCP 客户端管理器"""

    def __init__(self):
        self._clients: dict[str, MCPClient] = {}

    def add_server(self, config: MCPConfig) -> MCPClient:
        """添加 MCP 服务器"""
        client = MCPClient(config)
        self._clients[config.name] = client
        return client

    def remove_server(self, name: str) -> bool:
        """移除 MCP 服务器"""
        client = self._clients.pop(name, None)
        if client:
            asyncio.create_task(client.close())
            return True
        return False

    def get_client(self, name: str) -> MCPClient | None:
        """获取 MCP 客户端"""
        return self._clients.get(name)

    def list_servers(self) -> list[str]:
        """列出所有服务器"""
        return list(self._clients.keys())

    async def connect_all(self) -> None:
        """连接所有服务器"""
        for client in self._clients.values():
            if not client.is_connected:
                await client.connect()

    async def close_all(self) -> None:
        """关闭所有连接"""
        for client in self._clients.values():
            await client.close()


# 全局管理器
_mcp_manager = MCPClientManager()


def get_mcp_manager() -> MCPClientManager:
    """获取 MCP 管理器"""
    return _mcp_manager


def add_mcp_server(name: str, url: str, **kwargs) -> MCPClient:
    """快速添加 MCP 服务器"""
    config = MCPConfig(name=name, url=url, **kwargs)
    return _mcp_manager.add_server(config)


__all__ = [
    "MCPConfig",
    "MCPTool",
    "MCPResource",
    "MCPClient",
    "MCPClientManager",
    "get_mcp_manager",
    "add_mcp_server",
]
