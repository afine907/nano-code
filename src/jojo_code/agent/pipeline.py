"""Agent Pipeline - 串联五个 Agent 的流水线

核心功能:
1. 按顺序执行: ImpactAnalyzer → PRDAgent → SpecAgent → CodingAgent → VerificationAgent
2. 传递 TaskSpec 作为单一事实源
3. 支持中断和恢复
4. 错误处理和回滚
5. 完整的决策追踪
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .task_spec import AgentType, TaskSpec, TaskStatus

# Import agents
from .impact_analyzer import ImpactAnalyzer
from .prd_agent import PRDAgent
from .spec_agent import SpecAgent
from .coding_agent import CodingAgent
from .verification_agent import VerificationAgent


class PipelineStage(Enum):
    """Pipeline 执行阶段"""

    IMPACT_ANALYSIS = "impact_analysis"
    PRD_GENERATION = "prd_generation"
    SPEC_GENERATION = "spec_generation"
    CODING = "coding"
    VERIFICATION = "verification"


class PipelineStatus(Enum):
    """Pipeline 执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class StageResult:
    """单个阶段的执行结果"""

    stage: PipelineStage
    success: bool
    message: str = ""
    error: Optional[Exception] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage.value,
            "success": self.success,
            "message": self.message,
            "error": str(self.error) if self.error else None,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PipelineResult:
    """Pipeline 整体执行结果"""

    status: PipelineStatus
    task_spec: TaskSpec
    stage_results: list[StageResult] = field(default_factory=list)
    current_stage: Optional[PipelineStage] = None
    error: Optional[Exception] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "task_spec_id": self.task_spec.id,
            "task": self.task_spec.task,
            "stage_results": [r.to_dict() for r in self.stage_results],
            "current_stage": self.current_stage.value if self.current_stage else None,
            "error": str(self.error) if self.error else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.started_at and self.completed_at
                else None
            ),
        }

    def generate_report(self) -> str:
        """生成完整的执行报告"""
        lines = [
            "# Agent Pipeline 执行报告",
            "",
            f"## 概览",
            f"- 任务 ID: {self.task_spec.id}",
            f"- 任务描述: {self.task_spec.task}",
            f"- 最终状态: {self.status.value}",
            f"- 开始时间: {self.started_at.isoformat() if self.started_at else 'N/A'}",
            f"- 完成时间: {self.completed_at.isoformat() if self.completed_at else 'N/A'}",
            "",
            "## TaskSpec 状态",
            f"- 状态: {self.task_spec.status.value}",
            f"- Impact Analysis: {'已完成' if self.task_spec.impact_analysis else '未完成'}",
            f"- PRD: {'已完成' if self.task_spec.prd else '未完成'}",
            f"- Spec: {'已完成' if self.task_spec.spec else '未完成'}",
            f"- Code Result: {'已完成' if self.task_spec.code_result else '未完成'}",
            f"- Verification: {'已完成' if self.task_spec.verification else '未完成'}",
            "",
            "## 阶段执行详情",
        ]

        for i, result in enumerate(self.stage_results, 1):
            status_icon = "✓" if result.success else "✗"
            lines.append(f"")
            lines.append(f"### {i}. {result.stage.value} {status_icon}")
            lines.append(f"- 状态: {'成功' if result.success else '失败'}")
            lines.append(f"- 消息: {result.message}")
            if result.error:
                lines.append(f"- 错误: {str(result.error)}")
            lines.append(f"- 时间戳: {result.timestamp.isoformat()}")
            if result.metadata:
                lines.append(f"- 元数据: {result.metadata}")

        lines.append("")
        lines.append("## 决策追踪")
        lines.append(f"总计 {len(self.task_spec.audit_trail)} 条决策记录")
        lines.append("")

        for decision in self.task_spec.audit_trail:
            lines.append(
                f"- [{decision.agent.value}] {decision.decision_type.value}: "
                f"{str(decision.content)[:100]}"
            )

        return "\n".join(lines)


class AgentPipeline:
    """Agent 流水线 - 按顺序执行五个 Agent

    核心功能:
    - 按顺序执行: ImpactAnalyzer → PRDAgent → SpecAgent → CodingAgent → VerificationAgent
    - 传递 TaskSpec 作为单一事实源
    - 支持中断和恢复
    - 错误处理和回滚
    - 完整的决策追踪
    """

    # 定义阶段执行顺序和对应的 Agent 工厂
    STAGE_AGENT_MAP = {
        PipelineStage.IMPACT_ANALYSIS: (
            lambda ts, **kwargs: ImpactAnalyzer(ts, kwargs.get("code_base_path")),
            "analyze",
        ),
        PipelineStage.PRD_GENERATION: (
            lambda ts, **kwargs: PRDAgent(ts),
            "run",
        ),
        PipelineStage.SPEC_GENERATION: (
            lambda ts, **kwargs: SpecAgent(ts),
            "generate_spec",
        ),
        PipelineStage.CODING: (
            lambda ts, **kwargs: CodingAgent(ts, kwargs.get("tool_registry")),
            "run",
        ),
        PipelineStage.VERIFICATION: (
            lambda ts, **kwargs: VerificationAgent(ts),
            "run",
        ),
    }

    STAGE_ORDER = [
        PipelineStage.IMPACT_ANALYSIS,
        PipelineStage.PRD_GENERATION,
        PipelineStage.SPEC_GENERATION,
        PipelineStage.CODING,
        PipelineStage.VERIFICATION,
    ]

    def __init__(
        self,
        task_spec: TaskSpec,
        code_base_path: Optional[Path] = None,
        tool_registry: Optional[Any] = None,
    ):
        """初始化 Pipeline

        Args:
            task_spec: 任务规范，作为单一事实源在 Agent 间传递
            code_base_path: 代码库路径，用于 ImpactAnalyzer
            tool_registry: 工具注册表，用于 CodingAgent
        """
        self.task_spec = task_spec
        self.code_base_path = code_base_path
        self.tool_registry = tool_registry
        self.result = PipelineResult(
            status=PipelineStatus.PENDING,
            task_spec=task_spec,
        )
        self._rollback_state: Optional[dict] = None

    def run(
        self,
        start_from: Optional[PipelineStage] = None,
        stop_at: Optional[PipelineStage] = None,
    ) -> PipelineResult:
        """执行 Pipeline

        Args:
            start_from: 从指定阶段开始执行（用于恢复）
            stop_at: 在指定阶段后停止（用于部分执行）

        Returns:
            PipelineResult: 执行结果
        """
        self.result.status = PipelineStatus.RUNNING
        self.result.started_at = datetime.now()

        start_index = 0
        if start_from:
            start_index = self.STAGE_ORDER.index(start_from)

        stop_index = len(self.STAGE_ORDER)
        if stop_at:
            stop_index = self.STAGE_ORDER.index(stop_at)

        try:
            for stage in self.STAGE_ORDER[start_index:stop_index]:
                self.result.current_stage = stage

                # 保存回滚状态
                self._save_rollback_state(stage)

                stage_result = self._execute_stage(stage)

                self.result.stage_results.append(stage_result)

                if not stage_result.success:
                    self.result.status = PipelineStatus.FAILED
                    self.result.error = stage_result.error
                    break

            if self.result.status == PipelineStatus.RUNNING:
                self.result.status = PipelineStatus.COMPLETED

        except Exception as e:
            self.result.status = PipelineStatus.FAILED
            self.result.error = e
            self._rollback()

        finally:
            self.result.completed_at = datetime.now()
            self.result.current_stage = None

        return self.result

    def run_until(self, stage: PipelineStage) -> PipelineResult:
        """执行到指定阶段（不包含该阶段）

        Args:
            stage: 停止的阶段

        Returns:
            PipelineResult: 执行结果
        """
        return self.run(stop_at=stage)

    def resume_from(self, stage: PipelineStage) -> PipelineResult:
        """从指定阶段恢复执行

        Args:
            stage: 恢复执行的阶段

        Returns:
            PipelineResult: 执行结果
        """
        return self.run(start_from=stage)

    def pause(self) -> None:
        """暂停执行（设置标志，实际暂停需要在 _execute_stage 中检查）"""
        self.result.status = PipelineStatus.PAUSED

    def _execute_stage(self, stage: PipelineStage) -> StageResult:
        """执行单个阶段

        Args:
            stage: 要执行的阶段

        Returns:
            StageResult: 阶段执行结果
        """
        agent_factory, method_name = self.STAGE_AGENT_MAP[stage]

        try:
            agent = agent_factory(
                self.task_spec,
                code_base_path=self.code_base_path,
                tool_registry=self.tool_registry,
            )

            method = getattr(agent, method_name)
            result = method()

            return StageResult(
                stage=stage,
                success=True,
                message=f"Stage {stage.value} completed successfully",
                metadata={"result_type": type(result).__name__},
            )

        except Exception as e:
            return StageResult(
                stage=stage,
                success=False,
                message=f"Stage {stage.value} failed",
                error=e,
            )

    def _save_rollback_state(self, stage: PipelineStage) -> None:
        """保存回滚状态

        Args:
            stage: 当前阶段
        """
        self._rollback_state = {
            "stage": stage,
            "task_spec_status": self.task_spec.status,
            "impact_analysis": self.task_spec.impact_analysis,
            "prd": self.task_spec.prd,
            "spec": self.task_spec.spec,
            "code_result": self.task_spec.code_result,
            "verification": self.task_spec.verification,
            "audit_trail_length": len(self.task_spec.audit_trail),
        }

    def _rollback(self) -> None:
        """回滚到上一个稳定状态"""
        if not self._rollback_state:
            return

        state = self._rollback_state

        self.task_spec.status = state["task_spec_status"]
        self.task_spec.impact_analysis = state["impact_analysis"]
        self.task_spec.prd = state["prd"]
        self.task_spec.spec = state["spec"]
        self.task_spec.code_result = state["code_result"]
        self.task_spec.verification = state["verification"]

        # 回滚 audit_trail
        self.task_spec.audit_trail = self.task_spec.audit_trail[
            : state["audit_trail_length"]
        ]

        self.task_spec.add_decision(
            agent=AgentType.IMPACT_ANALYZER,
            decision_type=DecisionType.ERROR,
            content="Pipeline rolled back due to error",
            reasoning=f"Rolled back from stage {state['stage'].value}",
        )

    def get_next_stage(self) -> Optional[PipelineStage]:
        """获取下一个待执行阶段

        Returns:
            下一个阶段，如果没有则返回 None
        """
        if not self.result.stage_results:
            return self.STAGE_ORDER[0]

        last_completed = self.result.stage_results[-1]
        if not last_completed.success:
            return last_completed.stage

        current_index = self.STAGE_ORDER.index(last_completed.stage)
        if current_index + 1 < len(self.STAGE_ORDER):
            return self.STAGE_ORDER[current_index + 1]

        return None

    def is_completed(self) -> bool:
        """检查 Pipeline 是否已完成"""
        return self.result.status == PipelineStatus.COMPLETED

    def is_failed(self) -> bool:
        """检查 Pipeline 是否失败"""
        return self.result.status == PipelineStatus.FAILED


__all__ = [
    "AgentPipeline",
    "PipelineStage",
    "PipelineStatus",
    "PipelineResult",
    "StageResult",
]
