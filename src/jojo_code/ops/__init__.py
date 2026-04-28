"""AgentOps - Agent 运维体系

提供 Agent 执行的追踪、监控和评估能力。

Usage:
    from jojo_code.ops import Collector, SpanType, SpanStatus

    # 创建收集器
    collector = Collector()

    # 开始追踪
    trace = collector.start_trace("读取 README.md")

    # 记录工具调用
    collector.record_tool_call("read_file", {"path": "README.md"}, result="...")

    # 结束追踪
    collector.end_trace()
"""

from .collector import Collector
from .config import OpsConfig
from .dashboard import Dashboard
from .evaluator import (
    BaseEvaluator,
    CompositeEvaluator,
    EvaluationResult,
    EvaluationScore,
    PerformanceEvaluator,
    PlanningEvaluator,
    TestCaseEvaluator,
)
from .exporter import Exporter
from .metrics import MetricsEngine, MetricsSummary, TraceMetrics
from .models import Span, SpanStatus, SpanType, Trace
from .report import ReportGenerator

__all__ = [
    # 数据模型
    "Span",
    "SpanType",
    "SpanStatus",
    "Trace",
    # 配置
    "OpsConfig",
    # 收集器
    "Collector",
    # 指标
    "MetricsEngine",
    "MetricsSummary",
    "TraceMetrics",
    # 导出器
    "Exporter",
    # 面板
    "Dashboard",
    # 评估器
    "BaseEvaluator",
    "PlanningEvaluator",
    "TestCaseEvaluator",
    "PerformanceEvaluator",
    "CompositeEvaluator",
    "EvaluationResult",
    "EvaluationScore",
    # 报告
    "ReportGenerator",
]
