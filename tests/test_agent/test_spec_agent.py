"""Tests for SpecAgent"""

import pytest
from dataclasses import dataclass
from typing import Any, Optional

from jojo_code.agent.spec_agent import SpecAgent
from jojo_code.agent.task_spec import (
    TaskSpec,
    TaskStatus,
    PRD,
    Spec,
    DecisionRecord,
    DecisionType,
    AgentType,
)


@dataclass
class MockTaskSpec:
    """Mock TaskSpec for testing"""

    task: str = "Design API for user authentication"
    status: Any = TaskStatus.PENDING
    prd: Optional[PRD] = None
    spec: Optional[Spec] = None
    audit_trail: list[DecisionRecord] = None

    def __post_init__(self):
        if self.audit_trail is None:
            self.audit_trail = []

    def add_decision(self, **kwargs):
        record = DecisionRecord(
            agent=kwargs.get("agent", AgentType.SPEC_AGENT),
            decision_type=kwargs.get("decision_type", DecisionType.REASONING),
            content=kwargs.get("content"),
            reasoning=kwargs.get("reasoning", ""),
            confidence=kwargs.get("confidence", 1.0),
        )
        self.audit_trail.append(record)
        return record

    def update_status(self):
        if self.spec:
            self.status = TaskStatus.SPEC_COMPLETED
        elif self.prd:
            self.status = TaskStatus.PRD_COMPLETED


class TestSpecAgent:
    """Test SpecAgent"""

    def test_init(self):
        task_spec = MockTaskSpec(task="Design API for user management")
        agent = SpecAgent(task_spec)

        assert agent.task_spec.task == "Design API for user management"

    def test_generate_spec_with_prd(self):
        prd = PRD(
            title="User Authentication System",
            background="Need secure auth",
            goals=["Implement login", "Implement registration"],
            user_stories=[{"story": "As a user, I want to login"}],
            acceptance_criteria=["User can login"],
        )
        task_spec = MockTaskSpec(task="Build auth system", prd=prd)
        agent = SpecAgent(task_spec)

        spec = agent.generate_spec()

        assert isinstance(spec, Spec)
        assert spec.api_spec != ""
        assert len(spec.data_models) > 0
        assert len(spec.interfaces) > 0
        assert len(spec.dependencies) > 0
        assert task_spec.spec is not None
        assert task_spec.status == TaskStatus.SPEC_COMPLETED

    def test_generate_spec_without_prd(self):
        task_spec = MockTaskSpec(task="Add logging feature")
        agent = SpecAgent(task_spec)

        spec = agent.generate_spec()

        assert isinstance(spec, Spec)
        assert spec.api_spec != ""
        assert task_spec.spec is not None

    def test_design_api_spec(self):
        prd = PRD(
            title="User Management",
            user_stories=[{"story": "As a user, I want to manage Users"}],
        )
        task_spec = MockTaskSpec(prd=prd)
        agent = SpecAgent(task_spec)

        api_spec = agent._design_api_spec(prd)

        assert "openapi" in api_spec
        assert "paths" in api_spec
        assert "/api/" in api_spec

    def test_define_data_models(self):
        prd = PRD(
            title="Test",
            goals=["Manage users", "Track orders"],
        )
        task_spec = MockTaskSpec(prd=prd)
        agent = SpecAgent(task_spec)

        models = agent._define_data_models(prd)

        assert len(models) > 0
        assert all("name" in m and "fields" in m for m in models)

    def test_design_interfaces(self):
        prd = PRD(
            title="Test",
            user_stories=[{"story": "As a user, I want to login"}],
        )
        task_spec = MockTaskSpec(prd=prd)
        agent = SpecAgent(task_spec)

        interfaces = agent._design_interfaces(prd)

        assert len(interfaces) > 0
        assert all("name" in i and "methods" in i for i in interfaces)

    def test_determine_dependencies(self):
        prd = PRD(
            title="Test",
            goals=["Implement authentication"],
        )
        task_spec = MockTaskSpec(prd=prd)
        agent = SpecAgent(task_spec)

        deps = agent._determine_dependencies(prd)

        assert "fastapi" in deps
        assert "pydantic" in deps

    def test_determine_dependencies_with_auth(self):
        prd = PRD(
            title="Auth System",
            goals=["Implement authentication", "Add JWT support"],
        )
        task_spec = MockTaskSpec(prd=prd)
        agent = SpecAgent(task_spec)

        deps = agent._determine_dependencies(prd)

        assert "python-jose" in deps

    def test_determine_dependencies_with_database(self):
        prd = PRD(
            title="Data System",
            goals=["Setup database", "Add DB models"],
        )
        task_spec = MockTaskSpec(prd=prd)
        agent = SpecAgent(task_spec)

        deps = agent._determine_dependencies(prd)

        assert "sqlalchemy" in deps

    def test_audit_trail_recording(self):
        task_spec = MockTaskSpec()
        agent = SpecAgent(task_spec)

        assert len(task_spec.audit_trail) == 0

        spec = agent.generate_spec()

        assert len(task_spec.audit_trail) >= 2
        input_decisions = [d for d in task_spec.audit_trail if d.decision_type == DecisionType.INPUT]
        output_decisions = [d for d in task_spec.audit_trail if d.decision_type == DecisionType.OUTPUT]
        assert len(input_decisions) >= 1
        assert len(output_decisions) >= 1

    def test_extract_resources_from_story(self):
        task_spec = MockTaskSpec()
        agent = SpecAgent(task_spec)

        resources = agent._extract_resources_from_story("As a user, I want to manage Users and Orders")

        assert "users" in resources or "orders" in resources

    def test_spec_metadata(self):
        prd = PRD(
            title="Test PRD",
            goals=["Goal 1", "Goal 2"],
            user_stories=[{"story": "Story 1"}, {"story": "Story 2"}],
        )
        task_spec = MockTaskSpec(prd=prd)
        agent = SpecAgent(task_spec)

        spec = agent.generate_spec()

        assert spec.metadata["prd_title"] == "Test PRD"
        assert spec.metadata["goals_count"] == 2
        assert spec.metadata["user_stories_count"] == 2


class TestIntegration:
    """Integration tests"""

    def test_full_workflow_with_prd(self):
        prd = PRD(
            title="E-commerce User Management",
            background="Need to manage users for e-commerce platform",
            goals=["User registration", "User login", "User profile management"],
            user_stories=[
                {"story": "As a user, I want to register"},
                {"story": "As a user, I want to login"},
            ],
            acceptance_criteria=["User can register", "User can login"],
        )
        task_spec = TaskSpec(task="Build user management system")
        task_spec.prd = prd

        agent = SpecAgent(task_spec)
        spec = agent.generate_spec()

        assert task_spec.status == TaskStatus.SPEC_COMPLETED
        assert task_spec.spec is not None
        assert spec.api_spec != ""
        assert len(spec.data_models) >= 1
        assert len(spec.interfaces) >= 1
        assert len(task_spec.audit_trail) >= 2
        assert "fastapi" in spec.dependencies

    def test_generate_spec_from_task_description(self):
        task_spec = TaskSpec(task="Add user authentication with JWT")

        agent = SpecAgent(task_spec)
        spec = agent.generate_spec()

        assert task_spec.status == TaskStatus.SPEC_COMPLETED
        assert spec is not None
        assert len(spec.dependencies) >= 2
