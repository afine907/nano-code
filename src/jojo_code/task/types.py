"""任务状态和类型定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")  # 输出类型


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    KILLED = "killed"  # 被终止


class TaskType(Enum):
    """任务类型

    与 Claude Code 保持一致:
    - BASH: Shell 命令执行
    - AGENT: 子 Agent 任务
    - TEAMMATE: 队友任务
    - WORKFLOW: 工作流任务
    - MCP: MCP 工具任务
    - DREAM: 梦幻任务 (后台思考)
    """

    BASH = "bash"
    AGENT = "agent"
    TEAMMATE = "teammate"
    WORKFLOW = "workflow"
    MCP = "mcp"
    DREAM = "dream"


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class TaskInput:
    """任务输入"""

    tool_name: str
    args: dict[str, Any]
    description: str = ""


@dataclass
class TaskOutput:
    """任务输出"""

    data: Any = None
    error: str | None = None
    logs: list[str] = field(default_factory=list)


@dataclass
class TaskResult(Generic[T]):
    """任务结果

    Attributes:
        success: 是否成功
        output: 输出数据
        error: 错误信息
        duration: 执行耗时 (秒)
        tokens_used: 使用的 token 数
        cost: 费用 (美元)
    """

    success: bool
    output: T | None = None
    error: str | None = None
    duration: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0


@dataclass
class TaskProgress:
    """任务进度

    Attributes:
        task_id: 任务 ID
        status: 当前状态
        progress: 进度百分比 (0-100)
        message: 进度消息
        timestamp: 更新时间
    """

    task_id: str
    status: TaskStatus
    progress: float = 0.0
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    """任务

    Attributes:
        id: 任务 ID (1位前缀 + 8位随机字符)
        type: 任务类型
        status: 任务状态
        input: 任务输入
        output: 任务输出
        result: 任务结果
        progress: 任务进度
        priority: 优先级
        created_at: 创建时间
        started_at: 开始时间
        completed_at: 完成时间
        parent_id: 父任务 ID (如果有)
        metadata: 额外元数据
    """

    id: str
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    input: TaskInput | None = None
    output: TaskOutput | None = None
    result: TaskResult | None = None
    progress: TaskProgress | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: TaskResult) -> None:
        """完成任务

        Args:
            result: 任务结果
        """
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def fail(self, error: str) -> None:
        """任务失败

        Args:
            error: 错误信息
        """
        self.status = TaskStatus.FAILED
        self.output = TaskOutput(error=error)
        self.completed_at = datetime.now()

    def kill(self) -> None:
        """终止任务"""
        self.status = TaskStatus.KILLED
        self.completed_at = datetime.now()

    @property
    def duration(self) -> float:
        """获取执行时长 (秒)"""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()

    @property
    def is_running(self) -> bool:
        """是否正在执行"""
        return self.status == TaskStatus.RUNNING

    @property
    def is_done(self) -> bool:
        """是否已完成 (成功/失败/终止)"""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.KILLED,
        )


# 任务事件回调
TaskEventCallback = Any  # Callable[[Task], None]


__all__ = [
    "TaskStatus",
    "TaskType",
    "TaskPriority",
    "TaskInput",
    "TaskOutput",
    "TaskResult",
    "TaskProgress",
    "Task",
    "TaskEventCallback",
]
