"""PRD Agent - 需求规格生成器

基于 ImpactAnalysis 生成完整的 PRD，自动拆解用户故事，
定义验收标准，并将决策记录到 audit_trail。
"""

import logging
import re
from dataclasses import field
from typing import Any, Optional

from jojo_code.agent.task_spec import (
    AgentType,
    DecisionType,
    PRD,
    TaskSpec,
)

logger = logging.getLogger(__name__)


class PRDAgent:
    """需求规格生成器

    基于 ImpactAnalysis 生成完整的 PRD，包括：
    - 标题和背景
    - 目标列表
    - 用户故事
    - 验收标准
    - 范围外内容
    """

    def __init__(self, task_spec: TaskSpec):
        self.task_spec = task_spec

    def run(self) -> PRD:
        """执行 PRD 生成"""
        self.task_spec.add_decision(
            agent=AgentType.PRD_AGENT,
            decision_type=DecisionType.INPUT,
            content={
                "task": self.task_spec.task,
                "has_impact_analysis": self.task_spec.impact_analysis is not None,
            },
            reasoning="Starting PRD generation based on task and impact analysis",
        )

        if not self.task_spec.impact_analysis:
            logger.warning("No impact analysis found, proceeding with task only")

        prd = self._generate_prd()

        self.task_spec.prd = prd
        self.task_spec.update_status()

        self.task_spec.add_decision(
            agent=AgentType.PRD_AGENT,
            decision_type=DecisionType.OUTPUT,
            content=prd.to_dict(),
            reasoning=f"PRD generated with {len(prd.user_stories)} user stories and {len(prd.acceptance_criteria)} acceptance criteria",
            confidence=0.9,
        )

        return prd

    def _generate_prd(self) -> PRD:
        """生成 PRD 内容"""
        task = self.task_spec.task
        impact = self.task_spec.impact_analysis

        title = self._generate_title(task)
        background = self._generate_background(task, impact)
        goals = self._generate_goals(task, impact)
        user_stories = self._generate_user_stories(task, impact)
        acceptance_criteria = self._generate_acceptance_criteria(task, user_stories)
        out_of_scope = self._generate_out_of_scope(task, impact)

        return PRD(
            title=title,
            background=background,
            goals=goals,
            user_stories=user_stories,
            acceptance_criteria=acceptance_criteria,
            out_of_scope=out_of_scope,
            metadata={
                "generated_from": "task_spec",
                "has_impact_analysis": impact is not None,
            },
        )

    def _generate_title(self, task: str) -> str:
        """生成 PRD 标题"""
        words = task.split()
        if len(words) > 8:
            return " ".join(words[:8]) + "..."
        return task

    def _generate_background(self, task: str, impact: Optional[Any]) -> str:
        """生成背景描述"""
        background = f"## 背景\n\n{task}\n"
        if impact:
            background += f"\n## 影响分析摘要\n\n{impact.summary}\n"
            if impact.affected_components:
                background += f"\n受影响组件: {', '.join(impact.affected_components[:5])}\n"
        return background

    def _generate_goals(self, task: str, impact: Optional[Any]) -> list[str]:
        """生成目标列表"""
        goals = [f"实现 {task}"]
        if impact:
            if impact.suggestions:
                goals.extend(impact.suggestions[:3])
        goals.append("确保代码质量和可维护性")
        return goals

    def _generate_user_stories(self, task: str, impact: Optional[Any]) -> list[dict[str, str]]:
        """生成用户故事"""
        stories = []

        task_lower = task.lower()

        if any(word in task_lower for word in ["add", "create", "implement", "build"]):
            stories.append({
                "as_a": "用户",
                "i_want": f"能够使用 {task}",
                "so_that": "可以提升使用体验",
            })

        if any(word in task_lower for word in ["update", "modify", "change", "improve"]):
            stories.append({
                "as_a": "用户",
                "i_want": f"看到改进后的 {task}",
                "so_that": "功能更加完善",
            })

        if any(word in task_lower for word in ["fix", "repair", "resolve", "bug"]):
            stories.append({
                "as_a": "用户",
                "i_want": f"不再遇到相关问题",
                "so_that": "系统运行稳定",
            })

        if not stories:
            stories.append({
                "as_a": "用户",
                "i_want": task,
                "so_that": "达成预期目标",
            })

        return stories

    def _generate_acceptance_criteria(self, task: str, user_stories: list[dict[str, str]]) -> list[str]:
        """生成验收标准"""
        criteria = []

        criteria.append(f"功能实现符合需求: {task}")

        for i, story in enumerate(user_stories, 1):
            criteria.append(f"用户故事 {i} 可验证: {story['i_want']}")

        criteria.append("代码通过所有相关测试")
        criteria.append("文档已更新（如需要）")
        criteria.append("无引入新的严重问题")

        return criteria

    def _generate_out_of_scope(self, task: str, impact: Optional[Any]) -> list[str]:
        """生成范围外内容"""
        out_of_scope = []

        out_of_scope.append("大规模重构（除非必要）")
        out_of_scope.append(" unrelated 功能变更")

        if impact and impact.risk_level == "high":
            out_of_scope.append("高风险变更需要额外评审")

        return out_of_scope


__all__ = ["PRDAgent"]
