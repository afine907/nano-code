"""
Nano Code - 监控和指标模块
提供系统监控、性能指标、统计等功能
"""

import asyncio
import json
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import psutil

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """指标"""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class SystemMetrics:
    """系统指标"""

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    network_sent_mb: float
    network_recv_mb: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentMetrics:
    """Agent 指标"""

    agent_id: str
    total_conversations: int = 0
    total_messages: int = 0
    total_tokens: int = 0
    avg_response_time_ms: float = 0.0
    error_count: int = 0
    success_rate: float = 1.0
    uptime_seconds: float = 0.0


class MetricsCollector:
    """指标收集器"""

    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.metrics: dict[str, deque] = {}
        self._lock = asyncio.Lock()

        # 系统指标缓存
        self._last_system_metrics: SystemMetrics | None = None
        self._system_metrics_history: deque = deque(maxlen=1000)

    async def record(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: dict[str, str] | None = None,
        unit: str = "",
    ) -> None:
        """记录指标"""
        async with self._lock:
            metric = Metric(
                name=name, value=value, metric_type=metric_type, tags=tags or {}, unit=unit
            )

            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=10000)

            self.metrics[name].append(metric)

    async def increment(
        self, name: str, delta: float = 1.0, tags: dict[str, str] | None = None
    ) -> None:
        """递增计数器"""
        await self.record(name, delta, MetricType.COUNTER, tags)

    async def gauge(
        self, name: str, value: float, tags: dict[str, str] | None = None, unit: str = ""
    ) -> None:
        """设置仪表值"""
        await self.record(name, value, MetricType.GAUGE, tags, unit)

    async def histogram(
        self, name: str, value: float, tags: dict[str, str] | None = None, unit: str = ""
    ) -> None:
        """记录直方图值"""
        await self.record(name, value, MetricType.HISTOGRAM, tags, unit)

    async def timer(
        self, name: str, duration_ms: float, tags: dict[str, str] | None = None
    ) -> None:
        """记录计时器"""
        await self.record(name, duration_ms, MetricType.TIMER, tags, "ms")

    async def get_metrics(self, name: str, since: datetime | None = None) -> list[Metric]:
        """获取指标"""
        async with self._lock:
            if name not in self.metrics:
                return []

            metrics = list(self.metrics[name])

            if since:
                metrics = [m for m in metrics if m.timestamp >= since]

            return metrics

    async def get_latest(self, name: str) -> Metric | None:
        """获取最新指标"""
        async with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return None

            return self.metrics[name][-1]

    async def get_average(self, name: str, duration: timedelta | None = None) -> float | None:
        """获取平均值"""
        metrics = await self.get_metrics(name)

        if not metrics:
            return None

        if duration:
            since = datetime.now() - duration
            metrics = [m for m in metrics if m.timestamp >= since]

        if not metrics:
            return None

        return sum(m.value for m in metrics) / len(metrics)

    async def get_percentile(
        self, name: str, percentile: float, duration: timedelta | None = None
    ) -> float | None:
        """获取百分位数"""
        metrics = await self.get_metrics(name, duration)

        if not metrics:
            return None

        values = sorted([m.value for m in metrics])
        index = int(len(values) * percentile / 100)
        return values[min(index, len(values) - 1)]

    async def get_rate(self, name: str, window: timedelta = timedelta(minutes=1)) -> float | None:
        """获取速率（每分钟）"""
        since = datetime.now() - window
        metrics = await self.get_metrics(name, since)

        if not metrics:
            return None

        # 计算时间跨度
        if len(metrics) < 2:
            return 0.0

        time_span = (metrics[-1].timestamp - metrics[0].timestamp).total_seconds()

        if time_span == 0:
            return 0.0

        # 计算速率
        return len(metrics) / (time_span / 60)

    async def clear(self, name: str | None = None) -> None:
        """清除指标"""
        async with self._lock:
            if name:
                if name in self.metrics:
                    self.metrics[name].clear()
            else:
                self.metrics.clear()

    async def export_json(self) -> str:
        """导出为 JSON"""
        async with self._lock:
            data = {}
            for name, metrics in self.metrics.items():
                data[name] = [
                    {
                        "value": m.value,
                        "type": m.metric_type.value,
                        "timestamp": m.timestamp.isoformat(),
                        "tags": m.tags,
                        "unit": m.unit,
                    }
                    for m in metrics
                ]

            return json.dumps(data, indent=2)


class SystemMonitor:
    """系统监控"""

    def __init__(self, interval_seconds: float = 5.0):
        self.interval_seconds = interval_seconds
        self._running = False
        self._task: asyncio.Task | None = None
        self._callbacks: list[Callable] = []

        # 初始值
        self._cpu_percent = 0.0
        self._memory_percent = 0.0
        self._disk_percent = 0.0

    async def start(self) -> None:
        """启动监控"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("System monitor started")

    async def stop(self) -> None:
        """停止监控"""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("System monitor stopped")

    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                metrics = await self._collect_metrics()

                # 存储最新值
                self._cpu_percent = metrics.cpu_percent
                self._memory_percent = metrics.memory_percent
                self._disk_percent = metrics.disk_percent

                # 触发回调
                for callback in self._callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(metrics)
                        else:
                            callback(metrics)
                    except Exception as e:
                        logger.error(f"Monitor callback error: {e}")

                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(self.interval_seconds)

    async def _collect_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 内存
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)

        # 磁盘
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent

        # 网络
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / (1024 * 1024)
        network_recv_mb = network.bytes_recv / (1024 * 1024)

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_percent=disk_percent,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
        )

    def add_callback(self, callback: Callable) -> None:
        """添加监控回调"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> None:
        """移除监控回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def get_current_metrics(self) -> SystemMetrics:
        """获取当前系统指标"""
        return await self._collect_metrics()

    @property
    def cpu_percent(self) -> float:
        """CPU 使用率"""
        return self._cpu_percent

    @property
    def memory_percent(self) -> float:
        """内存使用率"""
        return self._memory_percent

    @property
    def disk_percent(self) -> float:
        """磁盘使用率"""
        return self._disk_percent


class AgentMonitor:
    """Agent 监控"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._start_time = time.time()
        self._conversation_count = 0
        self._message_count = 0
        self._token_count = 0
        self._error_count = 0
        self._response_times: deque = deque(maxlen=1000)
        self._lock = asyncio.Lock()

    async def record_conversation(self) -> None:
        """记录对话"""
        async with self._lock:
            self._conversation_count += 1

    async def record_message(self, tokens: int = 0) -> None:
        """记录消息"""
        async with self._lock:
            self._message_count += 1
            self._token_count += tokens

    async def record_response_time(self, duration_ms: float) -> None:
        """记录响应时间"""
        async with self._lock:
            self._response_times.append(duration_ms)

    async def record_error(self) -> None:
        """记录错误"""
        async with self._lock:
            self._error_count += 1

    async def get_metrics(self) -> AgentMetrics:
        """获取指标"""
        async with self._lock:
            uptime = time.time() - self._start_time

            avg_response_time = 0.0
            if self._response_times:
                avg_response_time = sum(self._response_times) / len(self._response_times)

            total_requests = self._message_count
            success_rate = 1.0
            if total_requests > 0:
                success_rate = (total_requests - self._error_count) / total_requests

            return AgentMetrics(
                agent_id=self.agent_id,
                total_conversations=self._conversation_count,
                total_messages=self._message_count,
                total_tokens=self._token_count,
                avg_response_time_ms=avg_response_time,
                error_count=self._error_count,
                success_rate=success_rate,
                uptime_seconds=uptime,
            )

    async def reset(self) -> None:
        """重置统计"""
        async with self._lock:
            self._start_time = time.time()
            self._conversation_count = 0
            self._message_count = 0
            self._token_count = 0
            self._error_count = 0
            self._response_times.clear()


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: dict[str, AlertRule] = {}
        self.alerts: list[dict] = []
        self._lock = asyncio.Lock()

    def add_rule(self, rule: "AlertRule") -> None:
        """添加告警规则"""
        self.rules[rule.name] = rule

    def remove_rule(self, name: str) -> None:
        """移除告警规则"""
        if name in self.rules:
            del self.rules[name]

    async def check(self, metrics: MetricsCollector, system_metrics: SystemMetrics) -> list[dict]:
        """检查告警"""
        async with self._lock:
            triggered = []

            for name, rule in self.rules.items():
                if await rule.evaluate(metrics, system_metrics):
                    alert = {
                        "rule": name,
                        "message": rule.message,
                        "severity": rule.severity,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.alerts.append(alert)
                    triggered.append(alert)

            return triggered

    async def get_alerts(
        self, since: datetime | None = None, severity: str | None = None
    ) -> list[dict]:
        """获取告警"""
        async with self._lock:
            alerts = self.alerts

            if since:
                alerts = [a for a in alerts if datetime.fromisoformat(a["timestamp"]) >= since]

            if severity:
                alerts = [a for a in alerts if a["severity"] == severity]

            return alerts

    async def clear_alerts(self) -> None:
        """清除告警"""
        async with self._lock:
            self.alerts.clear()


@dataclass
class AlertRule:
    """告警规则"""

    name: str
    message: str
    severity: str  # critical, warning, info
    condition: Callable[[MetricsCollector, SystemMetrics], bool]
    cooldown_seconds: int = 60


# 内置告警规则
class AlertRules:
    """预定义告警规则"""

    @staticmethod
    def cpu_high(threshold: float = 90.0) -> AlertRule:
        return AlertRule(
            name="cpu_high",
            message=f"CPU 使用率超过 {threshold}%",
            severity="warning",
            condition=lambda m, s: s.cpu_percent > threshold,
        )

    @staticmethod
    def memory_high(threshold: float = 90.0) -> AlertRule:
        return AlertRule(
            name="memory_high",
            message=f"内存使用率超过 {threshold}%",
            severity="warning",
            condition=lambda m, s: s.memory_percent > threshold,
        )

    @staticmethod
    def disk_high(threshold: float = 90.0) -> AlertRule:
        return AlertRule(
            name="disk_high",
            message=f"磁盘使用率超过 {threshold}%",
            severity="critical",
            condition=lambda m, s: s.disk_percent > threshold,
        )

    @staticmethod
    def error_rate_high(threshold: float = 0.1) -> AlertRule:
        async def condition(metrics: MetricsCollector, system_metrics: SystemMetrics) -> bool:
            error_rate = await metrics.get_percentile("error_rate", 95)
            return error_rate is not None and error_rate > threshold

        return AlertRule(
            name="error_rate_high",
            message=f"错误率超过 {threshold * 100}%",
            severity="critical",
            condition=condition,
        )


# 全局实例
_metrics_collector: MetricsCollector | None = None
_system_monitor: SystemMonitor | None = None
_alert_manager: AlertManager | None = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_system_monitor() -> SystemMonitor:
    """获取全局系统监控"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor


def get_alert_manager() -> AlertManager:
    """获取全局告警管理器"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
