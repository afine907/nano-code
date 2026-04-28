"""AgentOps 自动评估器"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .models import SpanStatus, SpanType, Trace


class EvaluationResult(Enum):
    """评估结果"""

    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


@dataclass
class EvaluationScore:
    """评估得分"""

    result: EvaluationResult
    score: float  # 0.0 - 1.0
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "result": self.result.value,
            "score": round(self.score, 4),
            "reason": self.reason,
            "details": self.details,
        }


class BaseEvaluator(ABC):
    """评估器基类"""

    @abstractmethod
    def evaluate(self, trace: Trace) -> EvaluationScore:
        """评估单个 Trace"""
        pass


class PlanningEvaluator(BaseEvaluator):
    """规划质量评估器 - 基于规则的评估"""

    def __init__(
        self,
        max_thinking_rounds: int = 10,
        min_tool_success_rate: float = 0.8,
        max_errors: int = 0,
    ):
        self.max_thinking_rounds = max_thinking_rounds
        self.min_tool_success_rate = min_tool_success_rate
        self.max_errors = max_errors

    def evaluate(self, trace: Trace) -> EvaluationScore:
        """评估规划质量"""
        issues = []
        score = 1.0

        # 规则 1: 思考轮数过多（可能陷入循环）
        if trace.thinking_count > self.max_thinking_rounds:
            issues.append(f"思考轮数过多: {trace.thinking_count}")
            score -= 0.2

        # 规则 2: 工具调用失败率高
        if trace.tool_success_rate < self.min_tool_success_rate:
            issues.append(f"工具调用成功率低: {trace.tool_success_rate:.2%}")
            score -= 0.2

        # 规则 3: 有错误发生
        if trace.error_count > self.max_errors:
            issues.append(f"发生错误: {trace.error_count} 次")
            score -= 0.1 * (trace.error_count - self.max_errors)

        # 规则 4: 重复工具调用（可能没理解任务）
        tool_calls = [s.name for s in trace.spans if s.type == SpanType.TOOL_CALL]
        if len(tool_calls) != len(set(tool_calls)):
            issues.append("存在重复的工具调用")
            score -= 0.1

        # 规则 5: 任务失败
        if trace.status == SpanStatus.FAILED:
            issues.append("任务执行失败")
            score -= 0.3

        score = max(0.0, min(1.0, score))

        result = EvaluationResult.PASS
        if score < 0.6:
            result = EvaluationResult.FAIL
        elif score < 0.8:
            result = EvaluationResult.PARTIAL

        return EvaluationScore(
            result=result,
            score=score,
            reason="; ".join(issues) if issues else "规划质量良好",
            details={"issues": issues, "rules_checked": 5},
        )


class TestCaseEvaluator(BaseEvaluator):
    """Test Case 评估器 - 基于预期结果的评估"""

    def __init__(self, test_cases: list[dict[str, Any]]):
        """
        test_cases 格式:
        [
            {
                "task": "读取 README.md",
                "expected_tools": ["read_file"],
                "expected_output_contains": ["README"],
                "max_rounds": 3,
            }
        ]
        """
        self.test_cases = test_cases

    def evaluate(self, trace: Trace) -> EvaluationScore:
        """根据 test case 评估"""
        # 找到匹配的 test case
        test_case = None
        for tc in self.test_cases:
            if tc["task"] in trace.task or trace.task in tc["task"]:
                test_case = tc
                break

        if not test_case:
            return EvaluationScore(
                result=EvaluationResult.PARTIAL,
                score=0.5,
                reason="未找到匹配的 test case",
                details={"test_cases_count": len(self.test_cases)},
            )

        issues = []
        score = 1.0

        # 检查工具调用
        actual_tools = [s.name for s in trace.spans if s.type == SpanType.TOOL_CALL]
        expected_tools = test_case.get("expected_tools", [])

        for expected in expected_tools:
            if expected not in actual_tools:
                issues.append(f"缺少预期工具: {expected}")
                score -= 0.2

        # 检查轮数
        max_rounds = test_case.get("max_rounds", 10)
        if trace.thinking_count > max_rounds:
            issues.append(f"超过最大轮数: {trace.thinking_count} > {max_rounds}")
            score -= 0.2

        # 检查输出
        expected_output = test_case.get("expected_output_contains", [])
        for expected in expected_output:
            found = False
            for span in trace.spans:
                if span.output and expected in str(span.output):
                    found = True
                    break
            if not found:
                issues.append(f"输出未包含: {expected}")
                score -= 0.1

        # 检查禁止的工具
        forbidden_tools = test_case.get("forbidden_tools", [])
        for forbidden in forbidden_tools:
            if forbidden in actual_tools:
                issues.append(f"使用了禁止的工具: {forbidden}")
                score -= 0.3

        score = max(0.0, min(1.0, score))

        result = (
            EvaluationResult.PASS
            if score >= 0.8
            else EvaluationResult.PARTIAL
            if score >= 0.6
            else EvaluationResult.FAIL
        )

        return EvaluationScore(
            result=result,
            score=score,
            reason="; ".join(issues) if issues else "通过所有检查",
            details={"test_case": test_case, "issues": issues},
        )


class PerformanceEvaluator(BaseEvaluator):
    """性能评估器 - 基于性能指标的评估"""

    def __init__(
        self,
        max_duration_ms: int = 30000,
        max_thinking_rounds: int = 5,
        max_tool_calls: int = 10,
    ):
        self.max_duration_ms = max_duration_ms
        self.max_thinking_rounds = max_thinking_rounds
        self.max_tool_calls = max_tool_calls

    def evaluate(self, trace: Trace) -> EvaluationScore:
        """评估性能"""
        issues = []
        score = 1.0

        # 检查耗时
        if trace.duration_ms > self.max_duration_ms:
            issues.append(f"耗时过长: {trace.duration_ms}ms > {self.max_duration_ms}ms")
            score -= 0.2

        # 检查思考轮数
        if trace.thinking_count > self.max_thinking_rounds:
            issues.append(f"思考轮数过多: {trace.thinking_count} > {self.max_thinking_rounds}")
            score -= 0.2

        # 检查工具调用次数
        if trace.tool_call_count > self.max_tool_calls:
            issues.append(f"工具调用过多: {trace.tool_call_count} > {self.max_tool_calls}")
            score -= 0.1

        score = max(0.0, min(1.0, score))

        result = (
            EvaluationResult.PASS
            if score >= 0.8
            else EvaluationResult.PARTIAL
            if score >= 0.6
            else EvaluationResult.FAIL
        )

        return EvaluationScore(
            result=result,
            score=score,
            reason="; ".join(issues) if issues else "性能良好",
            details={
                "duration_ms": trace.duration_ms,
                "thinking_rounds": trace.thinking_count,
                "tool_calls": trace.tool_call_count,
            },
        )


class CompositeEvaluator(BaseEvaluator):
    """组合评估器 - 组合多个评估器"""

    def __init__(self, evaluators: list[BaseEvaluator], weights: list[float] | None = None):
        """
        evaluators: 评估器列表
        weights: 权重列表（和为 1.0），如果不提供则平均权重
        """
        self.evaluators = evaluators
        if weights:
            assert len(weights) == len(evaluators), "权重数量必须与评估器数量相同"
            assert abs(sum(weights) - 1.0) < 0.001, "权重和必须为 1.0"
            self.weights = weights
        else:
            self.weights = [1.0 / len(evaluators)] * len(evaluators)

    def evaluate(self, trace: Trace) -> EvaluationScore:
        """组合评估"""
        scores = []
        details = {}

        for i, evaluator in enumerate(self.evaluators):
            score = evaluator.evaluate(trace)
            scores.append((score, self.weights[i]))
            details[f"evaluator_{i}_{type(evaluator).__name__}"] = score.to_dict()

        # 加权平均
        total_score = sum(s.score * w for s, w in scores)

        # 取最差的结果状态
        results = [s.result for s, _ in scores]
        if EvaluationResult.FAIL in results:
            final_result = EvaluationResult.FAIL
        elif EvaluationResult.PARTIAL in results:
            final_result = EvaluationResult.PARTIAL
        else:
            final_result = EvaluationResult.PASS

        # 汇总原因
        reasons = [s.reason for s, _ in scores if s.result != EvaluationResult.PASS]

        return EvaluationScore(
            result=final_result,
            score=total_score,
            reason="; ".join(reasons) if reasons else "所有评估通过",
            details=details,
        )
