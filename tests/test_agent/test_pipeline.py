"""Tests for AgentPipeline

测试内容:
1. Pipeline 按顺序执行五个 Agent
2. TaskSpec 作为单一事实源在 Agent 间传递
3. 支持中断和恢复
4. 错误处理和回滚
5. 完整的决策追踪
6. 端到端流程验证
"""

import pytest
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from unittest.mock import Mock, patch

from jojo_code.agent.pipeline import (
    AgentPipeline,
    PipelineStage,
    PipelineStatus,
    PipelineResult,
    StageResult,
)
from jojo_code.agent.task_spec import (
    TaskSpec,
    TaskStatus,
    AgentType,
    DecisionType,
    ImpactAnalysis,
    PRD,
    Spec,
    CodeResult,
    VerificationResult,
    DecisionRecord,
)


@dataclass
class MockTaskSpec:
    """Mock TaskSpec for testing"""

    task: str = "Add user authentication"
    status: TaskStatus = TaskStatus.PENDING
    id: str = "test-123"
    created_at: datetime = None
    updated_at: datetime = None
    context: dict = None
    impact_analysis: Optional[ImpactAnalysis] = None
    prd: Optional[PRD] = None
    spec: Optional[Spec] = None
    code_result: Optional[CodeResult] = None
    verification: Optional[VerificationResult] = None
    audit_trail: list = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.context is None:
            self.context = {}
        if self.audit_trail is None:
            self.audit_trail = []

    def add_decision(self, **kwargs):
        record = DecisionRecord(
            agent=kwargs.get("agent", AgentType.IMPACT_ANALYZER),
            decision_type=kwargs.get("decision_type", DecisionType.REASONING),
            content=kwargs.get("content"),
            reasoning=kwargs.get("reasoning", ""),
            confidence=kwargs.get("confidence", 1.0),
        )
        self.audit_trail.append(record)
        return record

    def update_status(self):
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


class TestPipelineStage:
    """Test PipelineStage enum"""

    def test_stage_values(self):
        assert PipelineStage.IMPACT_ANALYSIS.value == "impact_analysis"
        assert PipelineStage.PRD_GENERATION.value == "prd_generation"
        assert PipelineStage.SPEC_GENERATION.value == "spec_generation"
        assert PipelineStage.CODING.value == "coding"
        assert PipelineStage.VERIFICATION.value == "verification"

    def test_all_stages_defined(self):
        expected = [
            "impact_analysis",
            "prd_generation",
            "spec_generation",
            "coding",
            "verification",
        ]
        actual = [s.value for s in PipelineStage]
        assert actual == expected


class TestPipelineStatus:
    """Test PipelineStatus enum"""

    def test_status_values(self):
        assert PipelineStatus.PENDING.value == "pending"
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.COMPLETED.value == "completed"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.PAUSED.value == "paused"


class TestStageResult:
    """Test StageResult dataclass"""

    def test_stage_result_creation(self):
        result = StageResult(
            stage=PipelineStage.IMPACT_ANALYSIS,
            success=True,
            message="Test message",
        )
        assert result.stage == PipelineStage.IMPACT_ANALYSIS
        assert result.success is True
        assert result.message == "Test message"
        assert result.error is None

    def test_stage_result_to_dict(self):
        result = StageResult(
            stage=PipelineStage.CODING,
            success=False,
            message="Failed",
            error=Exception("Test error"),
        )
        d = result.to_dict()
        assert d["stage"] == "coding"
        assert d["success"] is False
        assert d["error"] == "Test error"


class TestPipelineResult:
    """Test PipelineResult dataclass"""

    def test_pipeline_result_creation(self, mock_task_spec):
        result = PipelineResult(
            status=PipelineStatus.COMPLETED,
            task_spec=mock_task_spec,
        )
        assert result.status == PipelineStatus.COMPLETED
        assert result.task_spec == mock_task_spec
        assert len(result.stage_results) == 0

    def test_pipeline_result_to_dict(self, mock_task_spec):
        result = PipelineResult(
            status=PipelineStatus.COMPLETED,
            task_spec=mock_task_spec,
        )
        d = result.to_dict()
        assert d["status"] == "completed"
        assert d["task_spec_id"] == mock_task_spec.id
        assert d["task"] == mock_task_spec.task


class TestAgentPipelineInitialization:
    """Test AgentPipeline initialization"""

    def test_init_with_task_spec(self, mock_task_spec):
        pipeline = AgentPipeline(mock_task_spec)
        assert pipeline.task_spec == mock_task_spec
        assert pipeline.result.status == PipelineStatus.PENDING
        assert pipeline.code_base_path is None
        assert pipeline.tool_registry is None

    def test_init_with_all_params(self, mock_task_spec, tmp_path):
        tool_registry = Mock()
        pipeline = AgentPipeline(
            task_spec=mock_task_spec,
            code_base_path=tmp_path,
            tool_registry=tool_registry,
        )
        assert pipeline.code_base_path == tmp_path
        assert pipeline.tool_registry == tool_registry


class TestAgentPipelineRun:
    """Test AgentPipeline run method"""

    def test_run_completes_successfully(self, mock_task_spec, tmp_path):
        """Test full pipeline execution with mocked agents"""
        with patch("jojo_code.agent.pipeline.ImpactAnalyzer") as MockImpact:
            with patch("jojo_code.agent.pipeline.PRDAgent") as MockPRD:
                with patch("jojo_code.agent.pipeline.SpecAgent") as MockSpec:
                    with patch("jojo_code.agent.pipeline.CodingAgent") as MockCoding:
                        with patch("jojo_code.agent.pipeline.VerificationAgent") as MockVerify:
                            # Setup mocks
                            for MockAgent in [
                                MockImpact,
                                MockPRD,
                                MockSpec,
                                MockCoding,
                                MockVerify,
                            ]:
                                instance = MockAgent.return_value
                                instance.analyze = Mock(
                                    return_value=ImpactAnalysis(summary="test")
                                )
                                instance.run = Mock(
                                    return_value=PRD(title="test")
                                )
                                instance.generate_spec = Mock(
                                    return_value=Spec(api_spec="test")
                                )

                            pipeline = AgentPipeline(mock_task_spec, code_base_path=tmp_path)
                            result = pipeline.run()

                            assert result.status == PipelineStatus.COMPLETED
                            assert len(result.stage_results) == 5
                            assert all(r.success for r in result.stage_results)

    def test_run_fails_at_second_stage(self, mock_task_spec, tmp_path):
        """Test pipeline failure handling"""
        with patch("jojo_code.agent.pipeline.ImpactAnalyzer") as MockImpact:
            with patch("jojo_code.agent.pipeline.PRDAgent") as MockPRD:
                MockImpact.return_value.analyze.return_value = ImpactAnalysis(
                    summary="test"
                )
                MockPRD.return_value.run.side_effect = Exception("PRD failed")

                pipeline = AgentPipeline(mock_task_spec, code_base_path=tmp_path)
                result = pipeline.run()

                assert result.status == PipelineStatus.FAILED
                assert len(result.stage_results) == 2
                assert result.stage_results[0].success is True
                assert result.stage_results[1].success is False


class TestAgentPipelinePartialExecution:
    """Test partial execution and resume"""

    def test_run_until_stage(self, mock_task_spec, tmp_path):
        """Test running pipeline until a specific stage"""
        with patch("jojo_code.agent.pipeline.ImpactAnalyzer") as MockImpact:
            with patch("jojo_code.agent.pipeline.PRDAgent") as MockPRD:
                MockImpact.return_value.analyze.return_value = ImpactAnalysis(
                    summary="test"
                )
                MockPRD.return_value.run.return_value = PRD(title="test")

                pipeline = AgentPipeline(mock_task_spec, code_base_path=tmp_path)
                result = pipeline.run_until(PipelineStage.SPEC_GENERATION)

                assert len(result.stage_results) == 2
                assert result.stage_results[0].stage == PipelineStage.IMPACT_ANALYSIS
                assert result.stage_results[1].stage == PipelineStage.PRD_GENERATION

    def test_resume_from_stage(self, mock_task_spec, tmp_path):
        """Test resuming pipeline from a specific stage"""
        with patch("jojo_code.agent.pipeline.SpecAgent") as MockSpec:
            with patch("jojo_code.agent.pipeline.CodingAgent") as MockCoding:
                with patch("jojo_code.agent.pipeline.VerificationAgent") as MockVerify:
                    MockSpec.return_value.generate_spec.return_value = Spec(
                        api_spec="test"
                    )
                    MockCoding.return_value.run.return_value = CodeResult()
                    MockVerify.return_value.run.return_value = VerificationResult(
                        passed=True
                    )

                    pipeline = AgentPipeline(mock_task_spec, code_base_path=tmp_path)
                    result = pipeline.resume_from(PipelineStage.SPEC_GENERATION)

                    assert len(result.stage_results) == 3
                    assert result.stage_results[0].stage == PipelineStage.SPEC_GENERATION


class TestAgentPipelineRollback:
    """Test rollback functionality"""

    def test_rollback_on_failure(self, mock_task_spec, tmp_path):
        """Test that state is rolled back on failure"""
        original_status = mock_task_spec.status

        with patch("jojo_code.agent.pipeline.ImpactAnalyzer") as MockImpact:
            MockImpact.return_value.analyze.side_effect = Exception("Analysis failed")

            pipeline = AgentPipeline(mock_task_spec, code_base_path=tmp_path)
            result = pipeline.run()

            assert result.status == PipelineStatus.FAILED
            assert mock_task_spec.status == original_status


class TestAgentPipelineReport:
    """Test report generation"""

    def test_generate_report(self, mock_task_spec, tmp_path):
        """Test report generation with all stages completed"""
        with patch("jojo_code.agent.pipeline.ImpactAnalyzer") as MockImpact:
            with patch("jojo_code.agent.pipeline.PRDAgent") as MockPRD:
                with patch("jojo_code.agent.pipeline.SpecAgent") as MockSpec:
                    with patch("jojo_code.agent.pipeline.CodingAgent") as MockCoding:
                        with patch("jojo_code.agent.pipeline.VerificationAgent") as MockVerify:
                            # Setup mocks
                            MockImpact.return_value.analyze.return_value = ImpactAnalysis(
                                summary="test"
                            )
                            MockPRD.return_value.run.return_value = PRD(title="test")
                            MockSpec.return_value.generate_spec.return_value = Spec(
                                api_spec="test"
                            )
                            MockCoding.return_value.run.return_value = CodeResult()
                            MockVerify.return_value.run.return_value = VerificationResult(
                                passed=True, score=0.9
                            )

                            pipeline = AgentPipeline(
                                mock_task_spec, code_base_path=tmp_path
                            )
                            result = pipeline.run()

                            report = result.generate_report()
                            assert "# Agent Pipeline 执行报告" in report
                            # 报告使用小写格式
                            assert "impact_analysis" in report
                            assert "prd_generation" in report or "PRD" in report
                            assert "spec_generation" in report or "Spec" in report


class TestAgentPipelineHelpers:
    """Test helper methods"""

    def test_get_next_stage_empty(self, mock_task_spec):
        pipeline = AgentPipeline(mock_task_spec)
        assert pipeline.get_next_stage() == PipelineStage.IMPACT_ANALYSIS

    def test_get_next_stage_after_first(self, mock_task_spec):
        pipeline = AgentPipeline(mock_task_spec)
        pipeline.result.stage_results.append(
            StageResult(stage=PipelineStage.IMPACT_ANALYSIS, success=True)
        )
        assert pipeline.get_next_stage() == PipelineStage.PRD_GENERATION

    def test_is_completed(self, mock_task_spec):
        pipeline = AgentPipeline(mock_task_spec)
        pipeline.result.status = PipelineStatus.COMPLETED
        assert pipeline.is_completed() is True
        assert pipeline.is_failed() is False

    def test_is_failed(self, mock_task_spec):
        pipeline = AgentPipeline(mock_task_spec)
        pipeline.result.status = PipelineStatus.FAILED
        assert pipeline.is_failed() is True
        assert pipeline.is_completed() is False


@pytest.fixture
def mock_task_spec():
    """Create a mock TaskSpec for testing"""
    return MockTaskSpec()


@pytest.fixture
def sample_pipeline(mock_task_spec, tmp_path):
    """Create a sample pipeline for testing"""
    return AgentPipeline(mock_task_spec, code_base_path=tmp_path)
