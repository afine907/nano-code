"""
Nano Code - API Server
提供 RESTful API 服务
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiohttp import web
from aiohttp.web import Request, Response

logger = logging.getLogger(__name__)


@dataclass
class APIRoute:
    """API 路由"""

    path: str
    method: str
    handler: Any
    auth_required: bool = False


@dataclass
class APIError:
    """API 错误"""

    code: int
    message: str
    details: dict | None = None


class APIMiddleware:
    """API 中间件基类"""

    async def process_request(self, request: Request) -> Response | None:
        """处理请求"""
        return None

    async def process_response(self, response: Response) -> Response:
        """处理响应"""
        return response


class AuthMiddleware(APIMiddleware):
    """认证中间件"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def process_request(self, request: Request) -> Response | None:
        if not self.api_key:
            return None

        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return json_error(401, "Missing authorization")

        token = auth_header[7:]

        if token != self.api_key:
            return json_error(401, "Invalid token")

        return None


class CORSMiddleware(APIMiddleware):
    """CORS 中间件"""

    def __init__(self, allowed_origins: list[str] = None):
        self.allowed_origins = allowed_origins or ["*"]

    async def process_response(self, response: Response) -> Response:
        response.headers["Access-Control-Allow-Origin"] = ", ".join(self.allowed_origins)
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response


class RateLimitMiddleware(APIMiddleware):
    """速率限制中间件"""

    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests: dict[str, list[float]] = {}

    async def process_request(self, request: Request) -> Response | None:
        ip = request.remote
        now = datetime.now().timestamp()

        if ip not in self.requests:
            self.requests[ip] = []

        # 清理过期请求
        self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]

        if len(self.requests[ip]) >= self.max_requests:
            return json_error(429, "Rate limit exceeded")

        self.requests[ip].append(now)

        return None


class APIServer:
    """API 服务器"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080, api_key: str | None = None):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.routes: list[APIRoute] = []
        self.middlewares: list[APIMiddleware] = []

        # 添加默认中间件
        self.middlewares.append(AuthMiddleware(api_key))
        self.middlewares.append(CORSMiddleware())
        self.middlewares.append(RateLimitMiddleware())

        # 注册内置路由
        self._register_builtin_routes()

    def _register_builtin_routes(self):
        """注册内置路由"""
        self.add_route("GET", "/health", self.health_check)
        self.add_route("GET", "/api/routes", self.list_routes)

    def add_route(self, method: str, path: str, handler: Any, auth_required: bool = False):
        """添加路由"""
        route = APIRoute(path, method, handler, auth_required)
        self.routes.append(route)

        # 注册到 aiohttp
        method_map = {
            "GET": self.app.router.get,
            "POST": self.app.router.post,
            "PUT": self.app.router.put,
            "DELETE": self.app.router.delete,
            "PATCH": self.app.router.patch,
        }

        method_map[method](path, self._wrap_handler(handler))

        logger.info(f"Registered route: {method} {path}")

    async def _wrap_handler(self, handler: Any):
        """包装处理器"""

        async def wrapper(request: Request):
            # 执行中间件
            for middleware in self.middlewares:
                response = await middleware.process_request(request)
                if response:
                    return response

            # 执行处理器
            try:
                result = await handler(request)

                # 处理返回值
                if isinstance(result, Response):
                    response = result
                elif isinstance(result, dict):
                    response = json_response(result)
                elif isinstance(result, str):
                    response = Response(text=result)
                else:
                    response = json_response({"data": result})

                # 执行响应中间件
                for middleware in self.middlewares:
                    response = await middleware.process_response(response)

                return response

            except web.HTTPException:
                raise
            except Exception as e:
                logger.error(f"Handler error: {e}")
                return json_error(500, str(e))

        return wrapper

    async def health_check(self, request: Request):
        """健康检查"""
        return json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})

    async def list_routes(self, request: Request):
        """列出所有路由"""
        return json_response(
            {
                "routes": [
                    {"method": r.method, "path": r.path, "auth_required": r.auth_required}
                    for r in self.routes
                ]
            }
        )

    def run(self):
        """运行服务器"""
        logger.info(f"Starting API server on {self.host}:{self.port}")
        web.run_app(self.app, host=self.host, port=self.port)


# 辅助函数
def json_response(data: Any, status: int = 200) -> Response:
    """JSON 响应"""
    return Response(
        text=json.dumps(data, indent=2, default=str), status=status, content_type="application/json"
    )


def json_error(code: int, message: str, details: Any = None) -> Response:
    """JSON 错误响应"""
    return json_response(
        {"error": {"code": code, "message": message, "details": details}}, status=code
    )


def require_auth(handler: Any):
    """认证装饰器"""

    async def wrapper(request: Request):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return json_error(401, "Missing authorization")

        # 验证 token
        # ... (实际验证逻辑)

        return await handler(request)

    return wrapper


# 内置 API 处理器
class ConversationAPI:
    """对话 API"""

    def __init__(self, conversation_manager):
        self.manager = conversation_manager

    async def list_conversations(self, request: Request):
        """列出对话"""
        limit = int(request.query.get("limit", 20))
        offset = int(request.query.get("offset", 0))

        conversations = self.manager.list_conversations()[offset : offset + limit]

        return json_response(
            {
                "conversations": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "message_count": len(c.messages),
                        "created_at": c.created_at.isoformat() if c.created_at else None,
                    }
                    for c in conversations
                ]
            }
        )

    async def get_conversation(self, request: Request):
        """获取对话"""
        conv_id = request.match_info["id"]

        conv = self.manager.get_conversation(conv_id)

        if not conv:
            return json_error(404, "Conversation not found")

        return json_response(
            {
                "id": conv.id,
                "title": conv.title,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    }
                    for m in conv.messages
                ],
            }
        )

    async def create_conversation(self, request: Request):
        """创建对话"""
        data = await request.json()

        conv = self.manager.create_conversation(title=data.get("title", "Untitled"))

        return json_response({"id": conv.id, "title": conv.title}, status=201)

    async def send_message(self, request: Request):
        """发送消息"""
        conv_id = request.match_info["id"]
        data = await request.json()

        conv = self.manager.get_conversation(conv_id)

        if not conv:
            return json_error(404, "Conversation not found")

        # 添加用户消息
        user_message = data.get("content")
        conv.add_message(role="user", content=user_message)

        # TODO: 调用 AI 处理
        response_content = f"收到: {user_message}"

        # 添加助手消息
        conv.add_message(role="assistant", content=response_content)

        return json_response({"role": "assistant", "content": response_content})


class AgentAPI:
    """Agent API"""

    def __init__(self, agent_manager):
        self.manager = agent_manager

    async def create_agent(self, request: Request):
        """创建 Agent"""
        data = await request.json()

        agent = await self.manager.create_agent(name=data.get("name"), model=data.get("model"))

        return json_response({"agent_id": agent.id, "name": agent.name}, status=201)

    async def execute(self, request: Request):
        """执行任务"""
        agent_id = request.match_info["id"]
        data = await request.json()

        result = await self.manager.execute(agent_id, data.get("task"))

        return json_response({"result": result})

    async def get_status(self, request: Request):
        """获取状态"""
        agent_id = request.match_info["id"]

        status = await self.manager.get_status(agent_id)

        return json_response(status)


class MetricsAPI:
    """指标 API"""

    def __init__(self, metrics_collector):
        self.collector = metrics_collector

    async def get_metrics(self, request: Request):
        """获取指标"""
        name = request.query.get("name")

        if name:
            metrics = await self.collector.get_metrics(name)
        else:
            metrics = {}
            for name in self.collector.metrics:
                latest = await self.collector.get_latest(name)
                if latest:
                    metrics[name] = {
                        "value": latest.value,
                        "timestamp": latest.timestamp.isoformat(),
                    }

        return json_response({"metrics": metrics})

    async def record_metric(self, request: Request):
        """记录指标"""
        data = await request.json()

        await self.collector.record(
            name=data["name"], value=data["value"], tags=data.get("tags", {})
        )

        return json_response({"success": True}, status=201)


# 服务器构建器
class APIServerBuilder:
    """API 服务器构建器"""

    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 8080
        self.api_key = None
        self.middlewares = []
        self.routes = []

    def host(self, host: str) -> "APIServerBuilder":
        self.host = host
        return self

    def port(self, port: int) -> "APIServerBuilder":
        self.port = port
        return self

    def api_key(self, key: str) -> "APIServerBuilder":
        self.api_key = key
        return self

    def add_middleware(self, middleware: APIMiddleware) -> "APIServerBuilder":
        self.middlewares.append(middleware)
        return self

    def add_route(self, method: str, path: str, handler: Any) -> "APIServerBuilder":
        self.routes.append((method, path, handler))
        return self

    def build(self) -> APIServer:
        server = APIServer(self.host, self.port, self.api_key)

        # 添加中间件
        for middleware in self.middlewares:
            server.middlewares.append(middleware)

        # 添加路由
        for method, path, handler in self.routes:
            server.add_route(method, path, handler)

        return server


# 全局 API 服务器
_api_server: APIServer | None = None


def create_api_server(**kwargs) -> APIServer:
    """创建 API 服务器"""
    global _api_server
    _api_server = APIServerBuilder().build()
    return _api_server


def get_api_server() -> APIServer | None:
    """获取 API 服务器"""
    return _api_server
