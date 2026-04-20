"""JSON-RPC 2.0 协议定义"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class JSONRPCRequest:
    """JSON-RPC 请求"""

    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str = ""
    params: dict = None

    @classmethod
    def from_dict(cls, data: dict) -> "JSONRPCRequest":
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method", ""),
            params=data.get("params", {}),
        )


@dataclass
class JSONRPCResponse:
    """JSON-RPC 响应"""

    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Any = None
    error: Optional[dict] = None

    def to_dict(self) -> dict:
        data = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            data["error"] = self.error
        else:
            data["result"] = self.result
        return data


@dataclass
class JSONRPCNotification:
    """JSON-RPC 通知（无 id）"""

    jsonrpc: str = "2.0"
    method: str = ""
    params: dict = None

    def to_dict(self) -> dict:
        return {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params or {},
        }


@dataclass
class StreamEvent:
    """流式事件"""

    type: str  # thinking | tool_call | tool_result | response | done | error
    content: str
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {"type": self.type, "content": self.content}
        if self.metadata:
            result["metadata"] = self.metadata
        return result
