"""
Nano Code - Webhook 模块
提供 Webhook 回调、事件触发、HTTP 回调等功能
"""

import asyncio
import hashlib
import hmac
import json
import ssl
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse

import aiohttp


class WebhookEventType(Enum):
    """Webhook 事件类型"""

    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"


@dataclass
class WebhookEvent:
    """Webhook 事件"""

    id: str
    type: WebhookEventType
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "nano-code"
    version: str = "1.0.0"


@dataclass
class WebhookConfig:
    """Webhook 配置"""

    url: str
    secret: str | None = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    enabled: bool = True
    events: list[WebhookEventType] = field(default_factory=list)


class WebhookSignatureError(Exception):
    """签名验证错误"""

    pass


class WebhookDeliveryError(Exception):
    """投递错误"""

    pass


class WebhookManager:
    """Webhook 管理器"""

    def __init__(self):
        self.webhooks: dict[str, WebhookConfig] = {}
        self.event_handlers: dict[WebhookEventType, list[Callable]] = {}
        self.delivery_history: list[dict] = []
        self._lock = asyncio.Lock()

    def register_webhook(self, name: str, config: WebhookConfig) -> None:
        """注册 Webhook"""
        self.webhooks[name] = config
        if config.events:
            for event_type in config.events:
                if event_type not in self.event_handlers:
                    self.event_handlers[event_type] = []

    def unregister_webhook(self, name: str) -> None:
        """注销 Webhook"""
        if name in self.webhooks:
            del self.webhooks[name]

    def get_webhook(self, name: str) -> WebhookConfig | None:
        """获取 Webhook 配置"""
        return self.webhooks.get(name)

    def list_webhooks(self) -> list[str]:
        """列出所有 Webhook"""
        return list(self.webhooks.keys())

    def on(self, event_type: WebhookEventType, handler: Callable) -> None:
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def off(self, event_type: WebhookEventType, handler: Callable) -> None:
        """注销事件处理器"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)

    async def trigger(self, event: WebhookEvent) -> list[dict[str, Any]]:
        """触发事件"""
        results = []

        async with self._lock:
            # 查找匹配的 Webhook
            for name, config in self.webhooks.items():
                if not config.enabled:
                    continue

                if config.events and event.type not in config.events:
                    continue

                # 投递事件
                result = await self._deliver(name, config, event)
                results.append(result)

            # 调用本地处理器
            if event.type in self.event_handlers:
                for handler in self.event_handlers[event.type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        results.append({"webhook": "local", "success": False, "error": str(e)})

        return results

    async def _deliver(
        self, name: str, config: WebhookConfig, event: WebhookEvent
    ) -> dict[str, Any]:
        """投递事件到 Webhook"""
        payload = self._build_payload(event)

        # 添加签名
        if config.secret:
            payload["signature"] = self._sign(payload, config.secret)

        # 发送请求，带重试
        last_error = None
        for attempt in range(config.retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        config.url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=config.timeout),
                        ssl=ssl.create_default_context()
                        if config.url.startswith("https")
                        else False,
                    ) as response:
                        if response.status < 400:
                            result = {
                                "webhook": name,
                                "success": True,
                                "status": response.status,
                                "attempt": attempt + 1,
                            }
                            self._record_delivery(result)
                            return result
                        else:
                            last_error = f"HTTP {response.status}"
            except TimeoutError:
                last_error = "Timeout"
            except Exception as e:
                last_error = str(e)

            # 等待后重试
            if attempt < config.retry_count - 1:
                await asyncio.sleep(config.retry_delay * (attempt + 1))

        result = {
            "webhook": name,
            "success": False,
            "error": last_error,
            "attempt": config.retry_count,
        }
        self._record_delivery(result)
        return result

    def _build_payload(self, event: WebhookEvent) -> dict[str, Any]:
        """构建请求载荷"""
        return {
            "id": event.id,
            "type": event.type.value,
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "version": event.version,
        }

    def _sign(self, payload: dict, secret: str) -> str:
        """生成签名"""
        data = json.dumps(payload, sort_keys=True)
        return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()

    def _record_delivery(self, result: dict) -> None:
        """记录投递结果"""
        self.delivery_history.append({**result, "timestamp": datetime.now().isoformat()})

        # 只保留最近 1000 条记录
        if len(self.delivery_history) > 1000:
            self.delivery_history = self.delivery_history[-1000:]

    def get_delivery_history(self, webhook_name: str | None = None, limit: int = 100) -> list[dict]:
        """获取投递历史"""
        history = self.delivery_history

        if webhook_name:
            history = [h for h in history if h.get("webhook") == webhook_name]

        return history[-limit:]

    def verify_signature(self, payload: dict, signature: str, secret: str) -> bool:
        """验证签名"""
        expected = self._sign(payload, secret)
        return hmac.compare_digest(expected, signature)


class WebhookBuilder:
    """Webhook 构建器"""

    def __init__(self):
        self._url: str | None = None
        self._secret: str | None = None
        self._timeout: int = 30
        self._retry_count: int = 3
        self._retry_delay: float = 1.0
        self._enabled: bool = True
        self._events: list[WebhookEventType] = []

    def url(self, url: str) -> "WebhookBuilder":
        """设置 URL"""
        parsed = urlparse(url)
        if not parsed.scheme:
            raise ValueError("Invalid URL: missing scheme")
        self._url = url
        return self

    def secret(self, secret: str) -> "WebhookBuilder":
        """设置签名密钥"""
        self._secret = secret
        return self

    def timeout(self, seconds: int) -> "WebhookBuilder":
        """设置超时时间"""
        self._timeout = seconds
        return self

    def retries(self, count: int, delay: float = 1.0) -> "WebhookBuilder":
        """设置重试参数"""
        self._retry_count = count
        self._retry_delay = delay
        return self

    def enabled(self, enabled: bool) -> "WebhookBuilder":
        """设置启用状态"""
        self._enabled = enabled
        return self

    def events(self, *events: WebhookEventType) -> "WebhookBuilder":
        """设置监听事件"""
        self._events = list(events)
        return self

    def build(self) -> WebhookConfig:
        """构建 Webhook 配置"""
        if not self._url:
            raise ValueError("URL is required")

        return WebhookConfig(
            url=self._url,
            secret=self._secret,
            timeout=self._timeout,
            retry_count=self._retry_count,
            retry_delay=self._retry_delay,
            enabled=self._enabled,
            events=self._events,
        )


# 全局 Webhook 管理器
_webhook_manager: WebhookManager | None = None


def get_webhook_manager() -> WebhookManager:
    """获取全局 Webhook 管理器"""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager


async def emit_event(
    event_type: WebhookEventType, data: dict[str, Any], source: str = "nano-code"
) -> list[dict[str, Any]]:
    """触发一个事件"""
    import uuid

    event = WebhookEvent(id=str(uuid.uuid4()), type=event_type, data=data, source=source)
    manager = get_webhook_manager()
    return await manager.trigger(event)
