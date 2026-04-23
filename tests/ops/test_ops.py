"""AgentOps 单元测试"""

from datetime import datetime

import pytest

from jojo_code.ops import (
    Collector,
    Exporter,
    OpsConfig,
    Span,
    SpanStatus,
    SpanType,
    Trace,
)


class TestSpan:
    """Span 数据结构测试"""

    def test_span_creation(self):
        """测试创建 Span"""
        span = Span(
            type=SpanType.TOOL_CALL,
            name="read_file",
            input={"path": "README.md"},
        )

        assert span.type == SpanType.TOOL_CALL
        assert span.name == "read_file"
        assert span.status == SpanStatus.STARTED
        assert span.id != ""
        assert span.start_time is not None

    def test_span_duration(self):
        """测试 Span 时长计算"""
        span = Span(type=SpanType.THINKING, name="thinking")
        span.end_time = datetime.now()

        assert span.duration_ms >= 0

    def test_span_to_dict(self):
        """测试 Span 序列化"""
        span = Span(
            type=SpanType.TOOL_CALL,
            name="read_file",
            input={"path": "README.md"},
            output="file content",
        )
        span.end_time = datetime.now()
        span.status = SpanStatus.COMPLETED

        data = span.to_dict()

        assert data["type"] == "tool_call"
        assert data["name"] == "read_file"
        assert data["status"] == "completed"
        assert "duration_ms" in data


class TestTrace:
    """Trace 数据结构测试"""

    def test_trace_creation(self):
        """测试创建 Trace"""
        trace = Trace(task="读取 README.md")

        assert trace.task == "读取 README.md"
        assert trace.status == SpanStatus.STARTED
        assert trace.id != ""
        assert len(trace.spans) == 0

    def test_trace_spans(self):
        """测试 Trace 添加 Span"""
        trace = Trace(task="测试任务")

        span1 = Span(trace_id=trace.id, type=SpanType.THINKING, name="thinking")
        span2 = Span(trace_id=trace.id, type=SpanType.TOOL_CALL, name="read_file")

        trace.spans.append(span1)
        trace.spans.append(span2)

        assert trace.thinking_count == 1
        assert trace.tool_call_count == 1
        assert trace.error_count == 0

    def test_trace_tool_success_rate(self):
        """测试工具成功率计算"""
        trace = Trace(task="测试任务")

        # 2 成功 1 失败
        span1 = Span(
            trace_id=trace.id,
            type=SpanType.TOOL_CALL,
            name="tool1",
            status=SpanStatus.COMPLETED,
        )
        span2 = Span(
            trace_id=trace.id,
            type=SpanType.TOOL_CALL,
            name="tool2",
            status=SpanStatus.COMPLETED,
        )
        span3 = Span(
            trace_id=trace.id,
            type=SpanType.TOOL_CALL,
            name="tool3",
            status=SpanStatus.FAILED,
        )

        trace.spans = [span1, span2, span3]

        assert trace.tool_success_rate == pytest.approx(2 / 3)

    def test_trace_to_dict(self):
        """测试 Trace 序列化"""
        trace = Trace(task="测试任务", session_id="test-session")
        trace.end_time = datetime.now()
        trace.status = SpanStatus.COMPLETED

        data = trace.to_dict()

        assert data["task"] == "测试任务"
        assert data["session_id"] == "test-session"
        assert "summary" in data
        assert data["summary"]["thinking_count"] == 0


class TestCollector:
    """Collector 测试"""

    def test_collector_start_end_trace(self):
        """测试开始和结束 Trace"""
        collector = Collector(config=OpsConfig(persist_traces=False))

        trace = collector.start_trace("测试任务", "session-123")

        assert trace is not None
        assert trace.task == "测试任务"
        assert collector.current_trace == trace

        ended_trace = collector.end_trace()

        assert ended_trace is not None
        assert ended_trace.status == SpanStatus.COMPLETED
        assert collector.current_trace is None
        assert len(collector.trace_store) == 1

    def test_collector_span(self):
        """测试 Span 记录"""
        collector = Collector(config=OpsConfig(persist_traces=False))

        collector.start_trace("测试任务")

        span = collector.start_span(SpanType.TOOL_CALL, "read_file", {"path": "README.md"})

        assert span is not None
        assert span.name == "read_file"
        assert len(collector.current_trace.spans) == 1

        collector.end_span(span, output_data="file content")

        assert span.status == SpanStatus.COMPLETED
        assert span.output == "file content"

        collector.end_trace()

    def test_collector_convenience_methods(self):
        """测试便捷方法"""
        collector = Collector(config=OpsConfig(persist_traces=False))

        collector.start_trace("测试任务")

        # 记录工具调用
        tool_span = collector.record_tool_call("read_file", {"path": "README.md"}, "content")
        assert tool_span is not None
        assert tool_span.status == SpanStatus.COMPLETED

        # 记录思考
        think_span = collector.record_thinking("我需要读取文件", "决定调用 read_file")
        assert think_span is not None

        # 记录错误
        error_span = collector.record_error("文件不存在")
        assert error_span is not None
        assert error_span.status == SpanStatus.FAILED

        collector.end_trace()

        trace = collector.trace_store[0]
        assert trace.tool_call_count == 1
        assert trace.thinking_count == 1
        assert trace.error_count == 1

    def test_collector_lru_eviction(self):
        """测试 LRU 淘汰"""
        config = OpsConfig(max_traces_in_memory=3, persist_traces=False)
        collector = Collector(config=config)

        # 创建 4 个 Trace
        for i in range(4):
            collector.start_trace(f"任务 {i}")
            collector.end_trace()

        # 应该只保留 3 个
        assert len(collector.trace_store) == 3
        assert collector.trace_store[0].task == "任务 1"  # 第一个被淘汰

    def test_collector_persist_traces(self, tmp_path):
        """测试持久化"""
        trace_dir = str(tmp_path / "traces")
        config = OpsConfig(persist_traces=True, trace_dir=trace_dir)
        collector = Collector(config=config)

        collector.start_trace("测试任务")
        collector.record_tool_call("read_file", {"path": "README.md"}, "content")
        collector.end_trace()

        # 检查文件是否存在
        import os

        assert os.path.exists(trace_dir)


class TestExporter:
    """Exporter 测试"""

    def test_export_traces_json(self, tmp_path):
        """测试导出 JSON"""
        trace = Trace(task="测试任务")
        trace.spans.append(Span(type=SpanType.TOOL_CALL, name="read_file"))
        trace.end_time = datetime.now()
        trace.status = SpanStatus.COMPLETED

        output_file = str(tmp_path / "traces.json")
        Exporter.export_traces_json([trace], output_file)

        import json

        with open(output_file) as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["task"] == "测试任务"

    def test_export_summary_markdown(self, tmp_path):
        """测试导出 Markdown 报告"""
        output_file = str(tmp_path / "report.md")
        report = Exporter.export_summary_markdown(
            total_traces=10,
            completed_traces=8,
            failed_traces=2,
            avg_thinking_rounds=3.5,
            avg_tool_calls=2.1,
            avg_duration_ms=1500.0,
            tool_success_rate=0.85,
            task_success_rate=0.80,
            tool_usage={"read_file": 15, "write_file": 8},
            error_types={"文件不存在": 2},
            output_path=output_file,
        )

        assert "总任务数" in report
        assert "10" in report
        assert "read_file" in report
        assert "文件不存在" in report

        import os

        assert os.path.exists(output_file)


class TestOpsConfig:
    """配置测试"""

    def test_config_defaults(self):
        """测试默认配置"""
        config = OpsConfig()

        assert config.enabled is True
        assert config.persist_traces is True
        assert config.trace_dir == ".jojo-code/traces"
        assert config.max_traces_in_memory == 1000

    def test_config_from_env(self, monkeypatch):
        """测试从环境变量加载"""
        monkeypatch.setenv("JOJO_CODE_OPS_ENABLED", "false")
        monkeypatch.setenv("JOJO_CODE_OPS_MAX_TRACES", "500")

        config = OpsConfig.from_env()

        assert config.enabled is False
        assert config.max_traces_in_memory == 500
