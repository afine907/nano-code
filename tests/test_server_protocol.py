"""测试 JSON-RPC Server"""

from nano_code.server.protocol import JSONRPCRequest, JSONRPCResponse, StreamEvent


class TestProtocol:
    """测试协议类"""

    def test_request_from_dict(self):
        """测试请求解析"""
        data = {"jsonrpc": "2.0", "id": "1", "method": "test", "params": {"a": 1}}
        request = JSONRPCRequest.from_dict(data)
        assert request.jsonrpc == "2.0"
        assert request.id == "1"
        assert request.method == "test"
        assert request.params == {"a": 1}

    def test_response_to_dict(self):
        """测试响应序列化"""
        response = JSONRPCResponse(id="1", result={"status": "ok"})
        data = response.to_dict()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "1"
        assert data["result"] == {"status": "ok"}

    def test_response_with_error(self):
        """测试错误响应"""
        response = JSONRPCResponse(id="1", error={"code": -32000, "message": "Error"})
        data = response.to_dict()
        assert "error" in data
        assert data["error"]["code"] == -32000

    def test_stream_event(self):
        """测试流式事件"""
        event = StreamEvent(type="response", content="hello", metadata={"tool": "test"})
        data = event.to_dict()
        assert data["type"] == "response"
        assert data["content"] == "hello"
        assert data["metadata"]["tool"] == "test"

    def test_stream_event_without_metadata(self):
        """测试无元数据的流式事件"""
        event = StreamEvent(type="done", content="")
        data = event.to_dict()
        assert data["type"] == "done"
        assert "metadata" not in data
