"""Task Spec - 单一事实源 (Single Source of Truth)

五个核心 Agent 通过 TaskSpec 进行上下文传递。
所有决策记录到 audit_trail 实现可追溯性。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TaskStatus(Enum):
    PENDING = "pending"
    IMPACT_ANALYZED = "impact_analyzed"
    PRD_COMPLETED = "prd_completed"
    SPEC_COMPLETED = "spec_completed"
    CODING_COMPLETED = "coding_completed"
    VERIFIED = "verified"
    FAILED = "failed"


class AgentType(Enum):
    IMPACT_ANALYZER = "impact-analyzer"
    PRD_AGENT = "prd-agent"
    SPEC_AGENT = "spec-agent"
    CODING_AGENT = "coding-agent"
    VERIFICATION_AGENT = "verification-agent"


class DecisionType(Enum):
    INPUT = "input"
    OUTPUT = "output"
    REASONING = "reasoning"
    TOOL_CALL = "tool_call"
    ERROR = "error"
    APPROVAL = "approval"


@dataclass
class DecisionRecord:
    """单个决策记录 - 实现可追溯性"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent: AgentType = AgentType.IMPACT_ANALYZER
    decision_type: DecisionType = DecisionType.REASONING
    timestamp: datetime = field(default_factory=datetime.now)

    content: Any = None
    reasoning: str = ""
    confidence: float = 1.0

    parent_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent.value,
            "type": self.decision_type.value,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }


@dataclass
class ImpactAnalysis:
    """Impact Analyzer 输出"""
    summary: str = ""
    affected_components: list[str] = field(default_factory=list)
    risk_level: str = "medium"
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "affected_components": self.affected_components,
            "risk_level": self.risk_level,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }


@dataclass
class PRD:
    """PRD Agent 输出"""
    title: str = ""
    background: str = ""
    goals: list[str] = field(default_factory=list)
    user_stories: list[dict[str, str]] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "background": self.background,
            "goals": self.goals,
            "user_stories": self.user_stories,
            "acceptance_criteria": self.acceptance_criteria,
            "out_of_scope": self.out_of_scope,
            "metadata": self.metadata,
        }


@dataclass
class Spec:
    """Spec Agent 输出"""
    api_spec: str = ""
    data_models: list[dict[str, Any]] = field(default_factory=list)
    interfaces: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "api_spec": self.api_spec,
            "data_models": self.data_models,
            "interfaces": self.interfaces,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }


@dataclass
class CodeResult:
    """Coding Agent 输出"""
    files_changed: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    diff_summary: str = ""
    test_results: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "files_changed": self.files_changed,
            "files_created": self.files_created,
            "diff_summary": self.diff_summary,
            "test_results": self.test_results,
            "metadata": self.metadata,
        }


@dataclass
class VerificationResult:
    """Verification Agent 输出"""
    passed: bool = False
    score: float = 0.0
    issues: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }


@dataclass
class TaskSpec:
    """单一事实源 - 所有 Agent 共享的状态"""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    context: dict[str, Any] = field(default_factory=dict)

    impact_analysis: Optional[ImpactAnalysis] = None
    prd: Optional[PRD] = None
    spec: Optional[Spec] = None
    code_result: Optional[CodeResult] = None
    verification: Optional[VerificationResult] = None

    audit_trail: list[DecisionRecord] = field(default_factory=list)

    def update_status(self) -> None:
        self.updated_at = datetime.now()
        if self.verification and self.verification.passed:
            self.status = TaskStatus.VERIFIED
        elif self.code_result:
            self.status = TaskStatus.CODING_COMPLETED
        elif self.spec:
            self.status = TaskStatus.SPEC_COMPLETED
        elif self.prd:
            self.status = TaskStatus.PRD_COMPLETED
        elif self.impact_analysis:
            self.status = TaskStatus.IMPACT_ANALYZED

    def add_decision(
        self,
        agent: AgentType,
        decision_type: DecisionType,
        content: Any,
        reasoning: str = "",
        confidence: float = 1.0,
        parent_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> DecisionRecord:
        record = DecisionRecord(
            agent=agent,
            decision_type=decision_type,
            content=content,
            reasoning=reasoning,
            confidence=confidence,
            parent_id=parent_id,
            metadata=metadata or {},
        )
        self.audit_trail.append(record)
        return record

    def get_decisions_by_agent(self, agent: AgentType) -> list[DecisionRecord]:
        return [d for d in self.audit_trail if d.agent == agent]

    def get_decisions_by_type(self, decision_type: DecisionType) -> list[DecisionRecord]:
        return [d for d in self.audit_trail if d.decision_type == decision_type]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "context": self.context,
            "impact_analysis": self.impact_analysis.to_dict() if self.impact_analysis else None,
            "prd": self.prd.to_dict() if self.prd else None,
            "spec": self.spec.to_dict() if self.spec else None,
            "code_result": self.code_result.to_dict() if self.code_result else None,
            "verification": self.verification.to_dict() if self.verification else None,
            "audit_trail": [d.to_dict() for d in self.audit_trail],
        }
