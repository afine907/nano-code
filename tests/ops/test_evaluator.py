"""Evaluator 单元测试"""

from datetime import datetime

import pytest

from jojo_code.ops import Span, SpanStatus, SpanType, Trace
from jojo_code.ops.evaluator import (
    CompositeEvaluator,
    EvaluationResult,
    EvaluationScore,
    PerformanceEvaluator,
    PlanningEvaluator,
    TestCaseEvaluator,
)


class TestEvaluationScore:
    """EvaluationScore 测试"""

    def test_score_creation(self):
        """测试创建评分"""
        score = EvaluationScore(
            result=EvaluationResult.PASS,
            score=0.95,
            reason="表现良好",
            details={"issues": []},
        )

        assert score.result == EvaluationResult.PASS
        assert score.score == 0.95
        assert score.reason == "表现良好"

    def test_score_to_dict(self):
        """测试序列化"""
        score = EvaluationScore(
            result=EvaluationResult.PASS,
            score=0.95,
            reason="表现良好",
        )

        data = score.to_dict()

        assert data["result"] == "pass"
        assert data["score"] == 0.95


class TestPlanningEvaluator:
    """PlanningEvaluator 测试"""

    @pytest.fixture
    def good_trace(self):
        """创建一个良好的 Trace"""
        trace = Trace(task="测试任务")
        trace.spans.append(
            Span(type=SpanType.TOOL_CALL, name="read_file", status=SpanStatus.COMPLETED)
        )
        trace.spans.append(Span(type=SpanType.THINKING, name="thinking"))
        trace.end_time = datetime.now()
        trace.status = SpanStatus.COMPLETED
        return trace

    @pytest.fixture
    def bad_trace(self):
        """创建一个有问题的 Trace"""
        trace = Trace(task="测试任务")
        # 多次思考（超过默认 10 次）
        for _ in range(12):
            trace.spans.append(Span(type=SpanType.THINKING, name="thinking"))
        # 工具失败
        trace.spans.append(
            Span(
                type=SpanType.TOOL_CALL,
                name="read_file",
                status=SpanStatus.FAILED,
                error="文件不存在",
            )
        )
        trace.end_time = datetime.now()
        trace.status = SpanStatus.FAILED
        return trace

    def test_evaluate_good_trace(self, good_trace):
        """测试评估良好的 Trace"""
        evaluator = PlanningEvaluator()
        score = evaluator.evaluate(good_trace)

        assert score.result == EvaluationResult.PASS
        assert score.score >= 0.8

    def test_evaluate_bad_trace(self, bad_trace):
        """测试评估有问题的 Trace"""
        evaluator = PlanningEvaluator()
        score = evaluator.evaluate(bad_trace)

        # 思考过多 + 工具失败 + 任务失败
        assert score.result == EvaluationResult.FAIL
        assert score.score < 0.6

    def test_custom_thresholds(self, good_trace):
        """测试自定义阈值"""
        evaluator = PlanningEvaluator(max_thinking_rounds=0)
        score = evaluator.evaluate(good_trace)

        # 1 次思考就超过了 0
        assert "思考轮数过多" in score.reason


class TestTestCaseEvaluator:
    """TestCaseEvaluator 测试"""

    @pytest.fixture
    def trace(self):
        """创建测试 Trace"""
        trace = Trace(task="读取 README.md")
        trace.spans.append(
            Span(
                type=SpanType.TOOL_CALL,
                name="read_file",
                status=SpanStatus.COMPLETED,
                output="# README\n这是一个项目说明",
            )
        )
        trace.end_time = datetime.now()
        trace.status = SpanStatus.COMPLETED
        return trace

    def test_evaluate_matching_test_case(self, trace):
        """测试匹配的 test case"""
        test_cases = [
            {
                "task": "读取 README.md",
                "expected_tools": ["read_file"],
                "expected_output_contains": ["README"],
                "max_rounds": 3,
            }
        ]
        evaluator = TestCaseEvaluator(test_cases)
        score = evaluator.evaluate(trace)

        assert score.result == EvaluationResult.PASS
        assert score.score >= 0.8

    def test_evaluate_missing_tool(self, trace):
        """测试缺少预期工具"""
        test_cases = [
            {
                "task": "读取",
                "expected_tools": ["read_file", "write_file"],
            }
        ]
        evaluator = TestCaseEvaluator(test_cases)
        score = evaluator.evaluate(trace)

        assert "缺少预期工具: write_file" in score.reason

    def test_evaluate_forbidden_tool(self, trace):
        """测试使用禁止的工具"""
        test_cases = [
            {
                "task": "读取",
                "expected_tools": ["read_file"],
                "forbidden_tools": ["read_file"],
            }
        ]
        evaluator = TestCaseEvaluator(test_cases)
        score = evaluator.evaluate(trace)

        assert score.score < 0.8

    def test_evaluate_no_matching_test_case(self, trace):
        """测试无匹配的 test case"""
        test_cases = [{"task": "写入文件", "expected_tools": ["write_file"]}]
        evaluator = TestCaseEvaluator(test_cases)
        score = evaluator.evaluate(trace)

        assert score.result == EvaluationResult.PARTIAL
        assert "未找到匹配" in score.reason


class TestPerformanceEvaluator:
    """PerformanceEvaluator 测试"""

    @pytest.fixture
    def fast_trace(self):
        """创建快速 Trace"""
        trace = Trace(task="测试")
        trace.spans.append(
            Span(type=SpanType.TOOL_CALL, name="read_file", status=SpanStatus.COMPLETED)
        )
        trace.start_time = datetime.now()
        trace.end_time = datetime.fromtimestamp(trace.start_time.timestamp() + 0.1)
        trace.status = SpanStatus.COMPLETED
        return trace

    @pytest.fixture
    def slow_trace(self):
        """创建慢速 Trace"""
        trace = Trace(task="测试")
        trace.start_time = datetime.now()
        trace.end_time = datetime.fromtimestamp(trace.start_time.timestamp() + 60)
        trace.status = SpanStatus.COMPLETED
        return trace

    def test_evaluate_fast_trace(self, fast_trace):
        """测试快速 Trace"""
        evaluator = PerformanceEvaluator(max_duration_ms=60000)
        score = evaluator.evaluate(fast_trace)

        assert score.result == EvaluationResult.PASS

    def test_evaluate_slow_trace(self, slow_trace):
        """测试慢速 Trace"""
        evaluator = PerformanceEvaluator(max_duration_ms=1000)
        score = evaluator.evaluate(slow_trace)

        assert "耗时过长" in score.reason

    def test_evaluate_too_many_tools(self):
        """测试工具调用过多"""
        trace = Trace(task="测试")
        for i in range(15):
            trace.spans.append(
                Span(type=SpanType.TOOL_CALL, name=f"tool_{i}", status=SpanStatus.COMPLETED)
            )
        trace.status = SpanStatus.COMPLETED

        evaluator = PerformanceEvaluator(max_tool_calls=10)
        score = evaluator.evaluate(trace)

        assert "工具调用过多" in score.reason


class TestCompositeEvaluator:
    """CompositeEvaluator 测试"""

    @pytest.fixture
    def trace(self):
        """创建测试 Trace"""
        trace = Trace(task="读取 README.md")
        trace.spans.append(
            Span(type=SpanType.TOOL_CALL, name="read_file", status=SpanStatus.COMPLETED)
        )
        trace.start_time = datetime.now()
        trace.end_time = datetime.fromtimestamp(trace.start_time.timestamp() + 0.5)
        trace.status = SpanStatus.COMPLETED
        return trace

    def test_composite_equal_weights(self, trace):
        """测试等权重组合"""
        evaluators = [
            PlanningEvaluator(),
            PerformanceEvaluator(),
        ]
        composite = CompositeEvaluator(evaluators)

        score = composite.evaluate(trace)

        assert score.score >= 0
        assert "evaluator_0_PlanningEvaluator" in score.details
        assert "evaluator_1_PerformanceEvaluator" in score.details

    def test_composite_custom_weights(self, trace):
        """测试自定义权重"""
        evaluators = [
            PlanningEvaluator(),
            PerformanceEvaluator(),
        ]
        weights = [0.7, 0.3]
        composite = CompositeEvaluator(evaluators, weights)

        score = composite.evaluate(trace)

        assert score.score >= 0

    def test_composite_fail_propagates(self):
        """测试 FAIL 状态传播"""
        bad_trace = Trace(task="测试")
        for _ in range(15):
            bad_trace.spans.append(Span(type=SpanType.THINKING, name="thinking"))
        bad_trace.status = SpanStatus.FAILED

        evaluators = [
            PlanningEvaluator(max_thinking_rounds=5),
            PerformanceEvaluator(max_thinking_rounds=5),
        ]
        composite = CompositeEvaluator(evaluators)

        score = composite.evaluate(bad_trace)

        assert score.result == EvaluationResult.FAIL
