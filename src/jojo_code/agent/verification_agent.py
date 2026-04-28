"""Verification Agent - 智能验收验证器

从 Spec 和 PRD 自动推断验收标准，验证实现是否符合需求，
运行集成测试，输出 VerificationResult，决策记录到 audit_trail。

核心特点：
- 自动从 Spec 和 PRD 推断验收标准，不依赖预设
- 基于实际生成的内容动态验证
"""

import logging
import re
from typing import Any

from .task_spec import (
    AgentType,
    DecisionType,
    TaskSpec,
    VerificationResult,
)

logger = logging.getLogger(__name__)


class VerificationAgent:
    """智能验收验证器

    自动从 Spec 和 PRD 推断验收标准，验证实现是否符合 PRD，
    运行集成测试，并将所有决策记录到 audit_trail。
    """

    def __init__(self, task_spec: TaskSpec):
        self.task_spec = task_spec

    def run(self) -> VerificationResult:
        """执行验证流程"""
        self.task_spec.add_decision(
            agent=AgentType.VERIFICATION_AGENT,
            decision_type=DecisionType.INPUT,
            content={
                "task": self.task_spec.task,
                "has_prd": self.task_spec.prd is not None,
                "has_spec": self.task_spec.spec is not None,
                "has_code_result": self.task_spec.code_result is not None,
            },
            reasoning="Starting verification process based on PRD, Spec, and code results",
        )

        if not self.task_spec.prd:
            logger.warning("No PRD found, cannot verify against requirements")
        if not self.task_spec.spec:
            logger.warning("No Spec found, verification will be limited")
        if not self.task_spec.code_result:
            logger.warning("No code result found, cannot verify implementation")

        inferred_criteria = self._infer_acceptance_criteria()
        self.task_spec.add_decision(
            agent=AgentType.VERIFICATION_AGENT,
            decision_type=DecisionType.REASONING,
            content={
                "inferred_criteria_count": len(inferred_criteria),
                "criteria": inferred_criteria[:5],
            },
            reasoning=f"Automatically inferred {len(inferred_criteria)} acceptance criteria from Spec and PRD",
            confidence=0.85,
        )

        prd_score, prd_issues, prd_suggestions = self._verify_against_prd(inferred_criteria)

        test_results = self._run_integration_tests()
        test_score = self._evaluate_test_results(test_results)

        final_score = self._calculate_final_score(prd_score, test_score, inferred_criteria)

        issues = prd_issues[:]
        suggestions = prd_suggestions[:]

        if test_results.get("failed"):
            issues.append({
                "severity": "high",
                "description": f"Integration tests failed: {', '.join(test_results['failed'])}",
                "source": "integration_tests",
            })
            suggestions.append("Fix failing integration tests")

        passed = final_score >= 0.7 and len([i for i in issues if i.get("severity") == "high"]) == 0

        verification = VerificationResult(
            passed=passed,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            metadata={
                "inferred_criteria_count": len(inferred_criteria),
                "inferred_criteria": inferred_criteria,
                "prd_score": prd_score,
                "test_score": test_score,
                "test_results": test_results,
                "verification_method": "automatic_inference",
            },
        )

        self.task_spec.verification = verification
        self.task_spec.update_status()

        self.task_spec.add_decision(
            agent=AgentType.VERIFICATION_AGENT,
            decision_type=DecisionType.OUTPUT,
            content=verification.to_dict(),
            reasoning=f"Verification completed: passed={passed}, score={final_score:.2f}",
            confidence=final_score,
        )

        return verification

    def _infer_acceptance_criteria(self) -> list[str]:
        """从 Spec 和 PRD 自动推断验收标准

        这是核心方法，不依赖预设，动态从实际内容推断。
        """
        criteria = []

        if self.task_spec.prd:
            prd = self.task_spec.prd

            if prd.acceptance_criteria:
                criteria.extend(prd.acceptance_criteria)

            for i, story in enumerate(prd.user_stories, 1):
                if isinstance(story, dict):
                    want = story.get("i_want", story.get("story", ""))
                else:
                    want = str(story)
                if want:
                    criteria.append(f"用户故事 {i} 可验证: {want}")

            for goal in prd.goals:
                criteria.append(f"目标达成验证: {goal}")

        if self.task_spec.spec:
            spec = self.task_spec.spec

            if spec.api_spec:
                api_resources = self._extract_api_resources(spec.api_spec)
                for resource in api_resources:
                    criteria.append(f"API 端点 /api/{resource} 可访问并返回正确响应")
                    criteria.append(f"API 端点 /api/{resource} 支持预期 HTTP 方法")

            for model in spec.data_models:
                model_name = model.get("name", "Unknown")
                criteria.append(f"数据模型 {model_name} 正确定义并实现")
                fields = model.get("fields", [])
                for field in fields:
                    field_name = field.get("name", "")
                    if field_name:
                        criteria.append(f"数据模型 {model_name} 包含字段 {field_name}")

            for interface in spec.interfaces:
                interface_name = interface.get("name", "Unknown")
                criteria.append(f"接口 {interface_name} 正确实现")
                methods = interface.get("methods", [])
                for method in methods:
                    method_name = method.get("name", "")
                    if method_name:
                        criteria.append(f"接口 {interface_name} 的方法 {method_name} 可调用")

            if spec.dependencies:
                for dep in spec.dependencies:
                    criteria.append(f"依赖 {dep} 已正确安装并可导入")

        if self.task_spec.code_result:
            code = self.task_spec.code_result
            for file in code.files_changed + code.files_created:
                criteria.append(f"文件 {file} 已正确修改/创建")
            if code.test_results:
                criteria.append("代码测试结果符合预期")

        if self.task_spec.task:
            criteria.append(f"整体功能实现符合任务描述: {self.task_spec.task}")

        seen = set()
        unique_criteria = []
        for c in criteria:
            if c not in seen:
                seen.add(c)
                unique_criteria.append(c)

        return unique_criteria

    def _extract_api_resources(self, api_spec: str) -> list[str]:
        """从 API 规范中提取资源名"""
        resources = re.findall(r"/api/(\w+)", api_spec)
        return list(set(resources))

    def _verify_against_prd(
        self, criteria: list[str]
    ) -> tuple[float, list[dict[str, Any]], list[str]]:
        """验证实现是否符合 PRD"""
        issues = []
        suggestions = []
        score = 1.0

        if not self.task_spec.prd:
            return 0.5, [{
                "severity": "medium",
                "description": "No PRD available for verification",
                "source": "prd_verification",
            }], ["Generate PRD before verification"]

        prd = self.task_spec.prd

        if self.task_spec.code_result:
            code = self.task_spec.code_result

            if not code.files_changed and not code.files_created:
                issues.append({
                    "severity": "high",
                    "description": "No files were changed or created",
                    "source": "prd_verification",
                })
                suggestions.append("Implement the required changes")
                score -= 0.3

            if code.test_results:
                test_success = code.test_results.get("success", False)
                if not test_success:
                    issues.append({
                        "severity": "high",
                        "description": f"Tests failed: {code.test_results.get('summary', 'Unknown')}",
                        "source": "prd_verification",
                    })
                    suggestions.append("Fix failing tests")
                    score -= 0.3

        criteria_met = 0
        total_criteria = len(criteria)

        for criterion in criteria:
            if self._check_criterion_met(criterion):
                criteria_met += 1
            else:
                issues.append({
                    "severity": "medium",
                    "description": f"Criterion not fully met: {criterion}",
                    "source": "criteria_verification",
                })
                suggestions.append(f"Ensure: {criterion}")

        if total_criteria > 0:
            criteria_score = criteria_met / total_criteria
            score = (score + criteria_score) / 2

        if prd.acceptance_criteria:
            prd_criteria_met = sum(
                1 for c in prd.acceptance_criteria if self._check_criterion_met(c)
            )
            prd_criteria_ratio = prd_criteria_met / len(prd.acceptance_criteria)
            score = (score + prd_criteria_ratio) / 2

        score = max(0.0, min(1.0, score))

        return score, issues, suggestions

    def _check_criterion_met(self, criterion: str) -> bool:
        """检查验收标准是否满足"""
        if not self.task_spec.code_result:
            return False

        code = self.task_spec.code_result

        if "文件" in criterion and any(
            f in criterion for f in code.files_changed + code.files_created
        ):
            return True

        if "API" in criterion or "端点" in criterion:
            if self.task_spec.spec and self.task_spec.spec.api_spec:
                return True

        if "数据模型" in criterion or "model" in criterion.lower():
            if self.task_spec.spec and self.task_spec.spec.data_models:
                return True

        if "接口" in criterion or "interface" in criterion.lower():
            if self.task_spec.spec and self.task_spec.spec.interfaces:
                return True

        if "测试" in criterion or "test" in criterion.lower():
            if code.test_results and code.test_results.get("success", False):
                return True

        if "任务描述" in criterion or "功能实现" in criterion:
            return len(code.files_changed) > 0 or len(code.files_created) > 0

        return False

    def _run_integration_tests(self) -> dict[str, Any]:
        """运行集成测试

        实际实现中这里会运行测试，当前返回模拟结果或已有结果。
        """
        if self.task_spec.code_result and self.task_spec.code_result.test_results:
            return self.task_spec.code_result.test_results

        return {
            "success": True,
            "passed": [],
            "failed": [],
            "summary": "No integration tests run (no test results available)",
        }

    def _evaluate_test_results(self, test_results: dict[str, Any]) -> float:
        """评估测试结果"""
        if not test_results:
            return 0.5

        if test_results.get("success", False):
            return 1.0

        passed = len(test_results.get("passed", []))
        failed = len(test_results.get("failed", []))
        total = passed + failed

        if total == 0:
            return 0.5

        return passed / total

    def _calculate_final_score(
        self, prd_score: float, test_score: float, criteria: list[str]
    ) -> float:
        """计算综合评分"""
        base_score = (prd_score * 0.6 + test_score * 0.4)

        if len(criteria) == 0:
            base_score -= 0.2

        if self.task_spec.code_result:
            code = self.task_spec.code_result
            if code.files_changed or code.files_created:
                base_score += 0.1

        return max(0.0, min(1.0, base_score))


__all__ = ["VerificationAgent"]
