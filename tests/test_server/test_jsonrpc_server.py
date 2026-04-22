"""JSON-RPC Server 测试

测试 JSON-RPC Server 的基本功能：
- 协议解析
- 请求处理
- 响应格式
"""

import json

from jojo_code.server.jsonrpc import (
    JsonRpcRequest,
    JsonRpcResponse,
    JsonRpcServer,
    get_server,
)


class TestJsonRpcProtocol:
    """测试 JSON-RPC 协议实现"""

    def test_parse_valid_request(self):
        """测试解析有效请求"""
        request = JsonRpcRequest(jsonrpc="2.0", method="test", id=1)

        assert request.jsonrpc == "2.0"
        assert request.method == "test"
        assert request.id == 1

    def test_parse_request_with_params(self):
        """测试解析带参数的请求"""
        request = JsonRpcRequest(jsonrpc="2.0", method="test", params={"key": "value"}, id=2)

        assert request.params == {"key": "value"}

    def test_create_success_response(self):
        """测试创建成功响应"""
        response = JsonRpcResponse(jsonrpc="2.0", result={"content": "test"}, id=1)

        assert response.result == {"content": "test"}
        assert response.error is None

    def test_create_error_response(self):
        """测试创建错误响应"""
        response = JsonRpcResponse(
            jsonrpc="2.0", error={"code": -32600, "message": "Invalid Request"}, id=1
        )

        assert response.error is not None
        assert response.error["code"] == -32600


class TestJsonRpcServer:
    """测试 JSON-RPC Server"""

    def test_server_creation(self):
        """测试创建 Server"""
        server = JsonRpcServer()
        assert server is not None
        assert isinstance(server.handlers, dict)

    def test_register_handler(self):
        """测试注册处理器"""
        server = JsonRpcServer()

        @server.method("test_method")
        def test_handler(params):
            return {"result": "ok"}

        assert "test_method" in server.handlers

    def test_handle_valid_request(self):
        """测试处理有效请求"""
        server = JsonRpcServer()

        @server.method("echo")
        def echo_handler(**params):
            return params

        request = JsonRpcRequest(jsonrpc="2.0", method="echo", params={"message": "hello"}, id=1)

        response = server._handle_request(request)
        assert response.result == {"message": "hello"}

    def test_handle_unknown_method(self):
        """测试处理未知方法"""
        server = JsonRpcServer()

        request = JsonRpcRequest(jsonrpc="2.0", method="unknown", id=1)

        response = server._handle_request(request)
        assert response.error is not None
        assert response.error["code"] == -32601  # Method not found

    def test_handle_handler_exception(self):
        """测试处理器抛出异常"""
        server = JsonRpcServer()

        @server.method("error_method")
        def error_handler(**params):
            raise ValueError("Test error")

        request = JsonRpcRequest(jsonrpc="2.0", method="error_method", id=1)

        response = server._handle_request(request)
        assert response.error is not None
        assert response.error["code"] == -32603  # Internal error


class TestJsonRpcCommunication:
    """测试 JSON-RPC 通信"""

    def test_request_parsing(self):
        """测试请求解析"""
        server = JsonRpcServer()

        input_data = json.dumps({"jsonrpc": "2.0", "method": "test", "id": 1})

        request = server._parse_request(input_data)
        assert request is not None
        assert request.method == "test"

    def test_response_format(self):
        """测试响应格式"""
        response = JsonRpcResponse(jsonrpc="2.0", result={"content": "test response"}, id=1)

        response_json = response.to_json()
        parsed = json.loads(response_json)

        assert parsed["jsonrpc"] == "2.0"
        assert parsed["result"]["content"] == "test response"
        assert parsed["id"] == 1

    def test_error_response_format(self):
        """测试错误响应格式"""
        response = JsonRpcResponse(
            jsonrpc="2.0", error={"code": -32600, "message": "Invalid Request"}, id=1
        )

        response_json = response.to_json()
        parsed = json.loads(response_json)

        assert "error" in parsed
        assert parsed["error"]["code"] == -32600

    def test_get_server_singleton(self):
        """测试获取全局服务器实例"""
        server1 = get_server()
        server2 = get_server()

        assert server1 is server2


class TestJsonRpcNotification:
    """测试 JSON-RPC 通知"""

    def test_send_notification(self, capsys):
        """测试发送通知"""
        server = JsonRpcServer()
        server.send_notification("test_event", {"data": "value"})

        captured = capsys.readouterr()
        notification = json.loads(captured.out.strip())

        assert notification["jsonrpc"] == "2.0"
        assert notification["method"] == "test_event"
        assert notification["params"] == {"data": "value"}

    def test_send_stream_chunk(self, capsys):
        """测试发送流式响应块"""
        server = JsonRpcServer()
        server.send_stream_chunk(1, {"type": "content", "text": "Hello"})

        captured = capsys.readouterr()
        chunk = json.loads(captured.out.strip())

        assert chunk["jsonrpc"] == "2.0"
        assert chunk["id"] == 1
        assert chunk["result"]["type"] == "content"
