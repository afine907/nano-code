"""Spec Agent - 技术决策生成器

基于 PRD 生成技术规格，设计 API 接口，定义数据模型，确定技术依赖。
所有决策记录到 audit_trail 实现可追溯性。
"""

import logging
import re
from dataclasses import field
from typing import Any

from .task_spec import (
    AgentType,
    DecisionType,
    PRD,
    Spec,
    TaskSpec,
)

logger = logging.getLogger(__name__)


class SpecAgent:
    """技术决策生成器

    基于 PRD 生成技术规格，包括 API 接口设计、数据模型定义、
    技术依赖确定等。所有决策记录到 audit_trail。
    """

    def __init__(self, task_spec: TaskSpec):
        self.task_spec = task_spec

    def generate_spec(self) -> Spec:
        """基于 PRD 生成技术规格"""
        self.task_spec.add_decision(
            agent=AgentType.SPEC_AGENT,
            decision_type=DecisionType.INPUT,
            content=f"Starting spec generation for task: {self.task_spec.task}",
            reasoning="Begin technical specification generation based on PRD",
        )

        if not self.task_spec.prd:
            logger.warning("No PRD found, generating spec from task description")
            prd = self._generate_prd_from_task()
        else:
            prd = self.task_spec.prd

        api_spec = self._design_api_spec(prd)
        data_models = self._define_data_models(prd)
        interfaces = self._design_interfaces(prd)
        dependencies = self._determine_dependencies(prd)

        spec = Spec(
            api_spec=api_spec,
            data_models=data_models,
            interfaces=interfaces,
            dependencies=dependencies,
            metadata={
                "prd_title": prd.title,
                "goals_count": len(prd.goals),
                "user_stories_count": len(prd.user_stories),
            },
        )

        self.task_spec.spec = spec
        self.task_spec.update_status()

        self.task_spec.add_decision(
            agent=AgentType.SPEC_AGENT,
            decision_type=DecisionType.OUTPUT,
            content=spec.to_dict(),
            reasoning=f"Generated spec with {len(interfaces)} interfaces and {len(data_models)} data models",
            confidence=0.9,
        )

        return spec

    def _generate_prd_from_task(self) -> PRD:
        """从任务描述生成基础 PRD"""
        return PRD(
            title=f"PRD for: {self.task_spec.task}",
            background=f"Auto-generated from task: {self.task_spec.task}",
            goals=["Implement the requested feature"],
            user_stories=[{"story": f"As a user, I want {self.task_spec.task}"}],
            acceptance_criteria=["Feature is implemented correctly"],
        )

    def _design_api_spec(self, prd: PRD) -> str:
        """设计 API 规范"""
        api_lines = ["openapi: 3.0.0", "info:", f"  title: {prd.title}", "paths:"]

        for story in prd.user_stories:
            story_text = story.get("story", "") if isinstance(story, dict) else str(story)
            resources = self._extract_resources_from_story(story_text)
            for resource in resources:
                api_lines.append(f"  /api/{resource}:")
                api_lines.append("    get:")
                api_lines.append("      summary: Get " + resource)
                api_lines.append("    post:")
                api_lines.append("      summary: Create " + resource)

        return "\n".join(api_lines)

    def _extract_resources_from_story(self, story: str) -> list[str]:
        """从用户故事中提取资源名"""
        words = re.findall(r"\b([A-Z][a-z]+|[a-z]{4,})\b", story)
        common_words = {"the", "and", "for", "with", "this", "that", "from",
                       "will", "what", "when", "where", "which", "have", "has"}
        resources = [w.lower() for w in words if w.lower() not in common_words]
        return list(set(resources))[:3]

    def _define_data_models(self, prd: PRD) -> list[dict[str, Any]]:
        """定义数据模型"""
        models = []
        for goal in prd.goals[:3]:
            model_name = "".join(w.capitalize() for w in goal.split()[:3])
            if model_name:
                models.append({
                    "name": model_name,
                    "fields": [
                        {"name": "id", "type": "string"},
                        {"name": "created_at", "type": "datetime"},
                    ],
                    "description": f"Data model for {goal}",
                })
        return models

    def _design_interfaces(self, prd: PRD) -> list[dict[str, Any]]:
        """设计接口"""
        interfaces = []
        for i, story in enumerate(prd.user_stories[:5]):
            story_text = story.get("story", "") if isinstance(story, dict) else str(story)
            interface_name = f"I{story_text.split()[0].capitalize() if story_text else 'Service'}"
            interfaces.append({
                "name": interface_name,
                "methods": [
                    {"name": "execute", "params": [], "returns": "void"},
                ],
                "description": f"Interface for: {story_text[:50]}",
            })
        return interfaces

    def _determine_dependencies(self, prd: PRD) -> list[str]:
        """确定技术依赖"""
        dependencies = ["pydantic", "fastapi"]
        if any("auth" in g.lower() for g in prd.goals):
            dependencies.append("python-jose")
        if any("database" in g.lower() or "db" in g.lower() for g in prd.goals):
            dependencies.append("sqlalchemy")
        return dependencies


__all__ = ["SpecAgent"]
