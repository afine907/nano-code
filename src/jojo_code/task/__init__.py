"""任务模块 - 任务管理与执行"""

from jojo_code.task.executor import (
    ExecutorFactory,
    TaskExecutor,
    TaskExecutorConfig,
    TaskFunc,
)
from jojo_code.task.id import (
    TASK_PREFIXES,
    generate_task_id,
    parse_task_id,
    validate_task_id,
)
from jojo_code.task.types import (
    Task,
    TaskEventCallback,
    TaskInput,
    TaskOutput,
    TaskPriority,
    TaskProgress,
    TaskResult,
    TaskStatus,
    TaskType,
)

__all__ = [
    # 类型定义
    "Task",
    "TaskType",
    "TaskStatus",
    "TaskPriority",
    "TaskInput",
    "TaskOutput",
    "TaskResult",
    "TaskProgress",
    "TaskEventCallback",
    # ID 管理
    "generate_task_id",
    "parse_task_id",
    "validate_task_id",
    "TASK_PREFIXES",
    # 执行器
    "TaskExecutor",
    "TaskExecutorConfig",
    "TaskFunc",
    "ExecutorFactory",
]
