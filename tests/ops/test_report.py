"""Report 单元测试"""

from datetime import datetime

import pytest

from jojo_code.ops import Span, SpanStatus, SpanType, Trace
from jojo_code.ops.evaluator import EvaluationResult, EvaluationScore
from jojo_code.ops.metrics import MetricsSummary
from jojo_code.ops.report import ReportGenerator


class TestReportGenerator:
    """ReportGenerator 测试"""

    @pytest.fixture
    def trace(self):
        """创建测试 Trace"""
        trace = Trace(task="读取 README.md")
        trace.spans.append(
            Span(
                type=SpanType.TOOL_CALL,
                name="read_file",
                status=SpanStatus.COMPLETED,
                input={"path": "README.md"},
                output="# README\n项目说明",
            )
        )
        trace.spans.append(Span(type=SpanType.THINKING, name="thinking"))
        trace.start_time = datetime.now()
        trace.end_time = datetime.fromtimestamp(trace.start_time.timestamp() + 1)
        trace.status = SpanStatus.COMPLETED
        return trace

    @pytest.fixture
    def score(self):
        """创建测试评分"""
        return EvaluationScore(
            result=EvaluationResult.PASS,
            score=0.95,
            reason="表现良好",
            details={"issues": [], "rules_checked": 5},
        )

    def test_generate_evaluation_report(self, trace, score):
        """测试生成评估报告"""
        report = ReportGenerator.generate_evaluation_report(trace, score)

        assert "AgentOps 评估报告" in report
        assert trace.id in report
        assert trace.task in report
        assert "PASS" in report
        assert "95" in report or "0.95" in report

    def test_generate_report_with_errors(self, trace):
        """测试包含错误的报告"""
        trace.spans.append(
            Span(
                type=SpanType.TOOL_CALL,
                name="write_file",
                status=SpanStatus.FAILED,
                error="权限不足",
            )
        )

        score = EvaluationScore(
            result=EvaluationResult.FAIL,
            score=0.3,
            reason="任务失败",
        )

        report = ReportGenerator.generate_evaluation_report(trace, score)

        assert "权限不足" in report
        assert "❌" in report

    def test_generate_report_to_file(self, trace, score, tmp_path):
        """测试输出到文件"""
        output_file = str(tmp_path / "report.md")
        ReportGenerator.generate_evaluation_report(trace, score, output_file)

        import os

        assert os.path.exists(output_file)
        with open(output_file) as f:
            content = f.read()
        assert "AgentOps 评估报告" in content

    def test_generate_summary_report(self):
        """测试生成汇总报告"""
        metrics = MetricsSummary(
            total_traces=100,
            completed_traces=85,
            failed_traces=15,
            avg_thinking_rounds=3.5,
            avg_tool_calls=4.2,
            avg_duration_ms=2500.0,
            tool_success_rate=0.92,
            task_success_rate=0.85,
            tool_usage={"read_file": 150, "write_file": 80, "execute": 50},
            error_types={"文件不存在": 10, "权限不足": 5},
        )

        report = ReportGenerator.generate_summary_report(metrics)

        assert "AgentOps 汇总报告" in report
        assert "100" in report
        assert "read_file" in report

    def test_generate_summary_report_with_evaluations(self):
        """测试带评估的汇总报告"""
        metrics = MetricsSummary(
            total_traces=10,
            completed_traces=8,
            failed_traces=2,
            avg_thinking_rounds=2.0,
            avg_tool_calls=3.0,
            avg_duration_ms=1000.0,
            tool_success_rate=0.95,
            task_success_rate=0.80,
            tool_usage={"read_file": 20},
            error_types={},
        )

        scores = [
            EvaluationScore(result=EvaluationResult.PASS, score=0.95, reason="良好"),
            EvaluationScore(result=EvaluationResult.PASS, score=0.88, reason="良好"),
            EvaluationScore(result=EvaluationResult.PARTIAL, score=0.72, reason="一般"),
            EvaluationScore(result=EvaluationResult.FAIL, score=0.45, reason="失败"),
        ]

        report = ReportGenerator.generate_summary_report(metrics, scores)

        assert "评估汇总" in report
        assert "平均得分" in report

    def test_generate_summary_report_to_file(self, tmp_path):
        """测试汇总报告输出到文件"""
        metrics = MetricsSummary(
            total_traces=10,
            completed_traces=8,
            failed_traces=2,
            avg_thinking_rounds=2.0,
            avg_tool_calls=3.0,
            avg_duration_ms=1000.0,
            tool_success_rate=0.95,
            task_success_rate=0.80,
            tool_usage={"read_file": 20},
            error_types={},
        )

        output_file = str(tmp_path / "summary.md")
        ReportGenerator.generate_summary_report(metrics, output_path=output_file)

        import os

        assert os.path.exists(output_file)

    def test_generate_suggestions_good_performance(self, trace, score):
        """测试良好表现的建议"""
        suggestions = ReportGenerator._generate_suggestions(trace, score)

        assert "表现良好" in suggestions[0]

    def test_generate_suggestions_too_many_thinking(self, trace):
        """测试思考过多的建议"""
        for _ in range(10):
            trace.spans.append(Span(type=SpanType.THINKING, name="thinking"))

        score = EvaluationScore(result=EvaluationResult.PARTIAL, score=0.6, reason="")

        suggestions = ReportGenerator._generate_suggestions(trace, score)

        assert any("思考轮数" in s or "优化" in s for s in suggestions)

    def test_generate_suggestions_tool_failure(self, trace):
        """测试工具失败的建议"""
        trace.spans.append(
            Span(
                type=SpanType.TOOL_CALL,
                name="bad_tool",
                status=SpanStatus.FAILED,
                error="错误",
            )
        )

        score = EvaluationScore(result=EvaluationResult.FAIL, score=0.3, reason="失败")

        suggestions = ReportGenerator._generate_suggestions(trace, score)

        assert len(suggestions) > 0

    def test_report_markdown_format(self, trace, score):
        """测试 Markdown 格式"""
        report = ReportGenerator.generate_evaluation_report(trace, score)

        # 检查 Markdown 元素
        assert report.startswith("#")  # 标题
        assert "|" in report  # 表格
        assert "---" in report or "##" in report  # 分隔线或子标题

    def test_empty_metrics_report(self):
        """测试空指标报告"""
        metrics = MetricsSummary(
            total_traces=0,
            completed_traces=0,
            failed_traces=0,
            avg_thinking_rounds=0,
            avg_tool_calls=0,
            avg_duration_ms=0,
            tool_success_rate=0,
            task_success_rate=0,
            tool_usage={},
            error_types={},
        )

        report = ReportGenerator.generate_summary_report(metrics)

        assert "AgentOps 汇总报告" in report
        assert "0" in report
