"""Tests for PRDAgent"""

import pytest
from dataclasses import dataclass
from typing import Any, Optional

from jojo_code.agent.prd_agent import PRDAgent
from jojo_code.agent.task_spec import (
    TaskSpec,
    TaskStatus,
    PRD,
    ImpactAnalysis,
    DecisionRecord,
    DecisionType,
    AgentType,
)


@dataclass
class MockTaskSpec:
    """Mock TaskSpec for testing"""

    task: str = "Add user authentication with logging"
    status: Any = TaskStatus.PENDING
    impact_analysis: Optional[ImpactAnalysis] = None
    prd: Optional[PRD] = None
    audit_trail: list[DecisionRecord] = None

    def __post_init__(self):
        if self.audit_trail is None:
            self.audit_trail = []

    def add_decision(self, **kwargs):
        record = DecisionRecord(
            agent=kwargs.get("agent", AgentType.PRD_AGENT),
            decision_type=kwargs.get("decision_type", DecisionType.REASONING),
            content=kwargs.get("content"),
            reasoning=kwargs.get("reasoning", ""),
            confidence=kwargs.get("confidence", 1.0),
        )
        self.audit_trail.append(record)
        return record

    def update_status(self):
        if self.prd:
            self.status = TaskStatus.PRD_COMPLETED
        elif self.impact_analysis:
            self.status = TaskStatus.IMPACT_ANALYZED


class TestPRDAgent:
    """Test PRDAgent"""

    def test_init(self):
        task_spec = MockTaskSpec(task="Add new feature")
        agent = PRDAgent(task_spec)

        assert agent.task_spec.task == "Add new feature"
        assert agent.task_spec.impact_analysis is None

    def test_init_with_impact_analysis(self):
        impact = ImpactAnalysis(
            summary="Test impact",
            affected_components=["auth.py"],
            risk_level="medium",
        )
        task_spec = MockTaskSpec(
            task="Update auth module",
            impact_analysis=impact,
        )
        agent = PRDAgent(task_spec)

        assert agent.task_spec.impact_analysis is not None
        assert agent.task_spec.impact_analysis.summary == "Test impact"

    def test_run_generates_prd(self):
        task_spec = MockTaskSpec(task="Add logging to user authentication")
        agent = PRDAgent(task_spec)
        prd = agent.run()

        assert isinstance(prd, PRD)
        assert prd.title != ""
        assert prd.background != ""
        assert len(prd.goals) > 0
        assert len(prd.user_stories) > 0
        assert len(prd.acceptance_criteria) > 0

    def test_run_with_impact_analysis(self):
        impact = ImpactAnalysis(
            summary="Authentication module will be affected",
            affected_components=["src/auth.py", "src/user.py"],
            risk_level="high",
            suggestions=["Review auth logic", "Add tests"],
        )
        task_spec = MockTaskSpec(
            task="Add logging to authentication",
            impact_analysis=impact,
        )
        agent = PRDAgent(task_spec)
        prd = agent.run()

        assert "Authentication module" in prd.background
        assert "src/auth.py" in prd.background
        assert any("logging" in goal.lower() or "authentication" in goal.lower() for goal in prd.goals)

    def test_run_updates_task_spec(self):
        task_spec = MockTaskSpec(task="Add feature")
        agent = PRDAgent(task_spec)
        prd = agent.run()

        assert task_spec.prd is not None
        assert task_spec.prd.title == prd.title
        assert task_spec.status == TaskStatus.PRD_COMPLETED

    def test_run_records_audit_trail(self):
        task_spec = MockTaskSpec(task="Add feature")
        agent = PRDAgent(task_spec)
        agent.run()

        assert len(task_spec.audit_trail) >= 2
        input_decisions = [d for d in task_spec.audit_trail if d.decision_type == DecisionType.INPUT]
        output_decisions = [d for d in task_spec.audit_trail if d.decision_type == DecisionType.OUTPUT]
        assert len(input_decisions) >= 1
        assert len(output_decisions) >= 1
        assert input_decisions[0].agent == AgentType.PRD_AGENT
        assert output_decisions[0].agent == AgentType.PRD_AGENT

    def test_generate_title(self):
        task_spec = MockTaskSpec(task="Add user authentication system")
        agent = PRDAgent(task_spec)
        title = agent._generate_title(task_spec.task)

        assert title == "Add user authentication system"

    def test_generate_title_truncates_long_task(self):
        long_task = "Add " + "very " * 10 + "long feature description"
        task_spec = MockTaskSpec(task=long_task)
        agent = PRDAgent(task_spec)
        title = agent._generate_title(long_task)

        assert len(title.split()) <= 9
        assert title.endswith("...")

    def test_generate_background(self):
        task_spec = MockTaskSpec(task="Add logging")
        agent = PRDAgent(task_spec)
        background = agent._generate_background(task_spec.task, None)

        assert "Add logging" in background
        assert "## 背景" in background

    def test_generate_background_with_impact(self):
        impact = ImpactAnalysis(
            summary="Will affect logging module",
            affected_components=["logger.py"],
        )
        task_spec = MockTaskSpec(task="Add logging", impact_analysis=impact)
        agent = PRDAgent(task_spec)
        background = agent._generate_background(task_spec.task, impact)

        assert "Will affect logging module" in background
        assert "logger.py" in background

    def test_generate_goals(self):
        task_spec = MockTaskSpec(task="Add authentication")
        agent = PRDAgent(task_spec)
        goals = agent._generate_goals(task_spec.task, None)

        assert len(goals) > 0
        assert any("authentication" in g.lower() or "实现" in g for g in goals)

    def test_generate_goals_with_impact(self):
        impact = ImpactAnalysis(
            suggestions=["Add unit tests", "Update documentation"],
        )
        task_spec = MockTaskSpec(task="Add feature", impact_analysis=impact)
        agent = PRDAgent(task_spec)
        goals = agent._generate_goals(task_spec.task, impact)

        assert len(goals) >= 3
        assert any("unit tests" in g.lower() for g in goals)

    def test_generate_user_stories_add(self):
        task_spec = MockTaskSpec(task="Add user login feature")
        agent = PRDAgent(task_spec)
        stories = agent._generate_user_stories(task_spec.task, None)

        assert len(stories) > 0
        assert any("user login" in s["i_want"].lower() for s in stories)

    def test_generate_user_stories_update(self):
        task_spec = MockTaskSpec(task="Update authentication system")
        agent = PRDAgent(task_spec)
        stories = agent._generate_user_stories(task_spec.task, None)

        assert len(stories) > 0
        assert any("improved" in s["so_that"].lower() or "完善" in s["so_that"] for s in stories)

    def test_generate_user_stories_fix(self):
        task_spec = MockTaskSpec(task="Fix authentication bug")
        agent = PRDAgent(task_spec)
        stories = agent._generate_user_stories(task_spec.task, None)

        assert len(stories) > 0
        assert any("不再遇到" in s["i_want"] or "bug" in s["i_want"].lower() for s in stories)

    def test_generate_user_stories_default(self):
        task_spec = MockTaskSpec(task="Some random task")
        agent = PRDAgent(task_spec)
        stories = agent._generate_user_stories(task_spec.task, None)

        assert len(stories) >= 1
        assert "as_a" in stories[0]
        assert "i_want" in stories[0]
        assert "so_that" in stories[0]

    def test_generate_acceptance_criteria(self):
        task_spec = MockTaskSpec(task="Add feature")
        agent = PRDAgent(task_spec)
        stories = [{"as_a": "user", "i_want": "feature", "so_that": "benefit"}]
        criteria = agent._generate_acceptance_criteria(task_spec.task, stories)

        assert len(criteria) >= 3
        assert any("Add feature" in c for c in criteria)
        assert any("测试" in c or "test" in c.lower() for c in criteria)

    def test_generate_out_of_scope(self):
        task_spec = MockTaskSpec(task="Add feature")
        agent = PRDAgent(task_spec)
        out_of_scope = agent._generate_out_of_scope(task_spec.task, None)

        assert len(out_of_scope) > 0
        assert any("重构" in s or "refactor" in s.lower() for s in out_of_scope)

    def test_generate_out_of_scope_high_risk(self):
        impact = ImpactAnalysis(risk_level="high")
        task_spec = MockTaskSpec(task="Add feature", impact_analysis=impact)
        agent = PRDAgent(task_spec)
        out_of_scope = agent._generate_out_of_scope(task_spec.task, impact)

        assert any("评审" in s or "review" in s.lower() for s in out_of_scope)

    def test_prd_metadata(self):
        task_spec = MockTaskSpec(task="Add feature")
        agent = PRDAgent(task_spec)
        prd = agent.run()

        assert prd.metadata is not None
        assert prd.metadata["generated_from"] == "task_spec"


class TestIntegration:
    """Integration tests with real TaskSpec"""

    def test_full_workflow(self):
        task_spec = TaskSpec(task="Add detailed logging to authentication flow")
        impact = ImpactAnalysis(
            summary="Authentication module needs logging",
            affected_components=["src/auth.py"],
            risk_level="medium",
            suggestions=["Add logging to auth functions"],
        )
        task_spec.impact_analysis = impact

        agent = PRDAgent(task_spec)
        prd = agent.run()

        assert task_spec.status == TaskStatus.PRD_COMPLETED
        assert task_spec.prd is not None
        assert task_spec.prd.title == prd.title
        assert len(task_spec.audit_trail) >= 2
        assert prd.to_dict()["title"] == prd.title

    def test_workflow_without_impact_analysis(self):
        task_spec = TaskSpec(task="Add simple feature")

        agent = PRDAgent(task_spec)
        prd = agent.run()

        assert task_spec.prd is not None
        assert task_spec.status == TaskStatus.PRD_COMPLETED
        assert len(prd.user_stories) > 0

    def test_user_story_structure(self):
        task_spec = TaskSpec(task="Add user registration")
        agent = PRDAgent(task_spec)
        prd = agent.run()

        for story in prd.user_stories:
            assert "as_a" in story
            assert "i_want" in story
            assert "so_that" in story
