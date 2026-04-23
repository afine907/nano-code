"""AgentOps 数据模型 - Span 和 Trace"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SpanType(Enum):
    """Span 类型"""

    THINKING = "thinking"  # Agent 思考
    TOOL_CALL = "tool_call"  # 工具调用
    OBSERVE = "observe"  # 观察结果
    ERROR = "error"  # 错误


class SpanStatus(Enum):
    """Span 状态"""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Span:
    """Agent 执行的一个步骤"""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trace_id: str = ""  # 所属 Trace
    parent_id: str | None = None  # 父 Span (用于嵌套)

    type: SpanType = SpanType.THINKING
    name: str = ""  # span 名称，如 "read_file"

    input: Any = None  # 输入数据
    output: Any = None  # 输出数据
    error: str | None = None  # 错误信息

    status: SpanStatus = SpanStatus.STARTED
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    metadata: dict = field(default_factory=dict)  # 额外元数据

    @property
    def duration_ms(self) -> int:
        """执行时长（毫秒）"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "type": self.type.value,
            "name": self.name,
            "input": self._serialize(self.input),
            "output": self._serialize(self.output),
            "error": self.error,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }

    def _serialize(self, value: Any) -> Any:
        """序列化值，处理不可 JSON 序列化的对象"""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool, list, dict)):
            return value
        # 对于复杂对象，转为字符串
        return str(value)


@dataclass
class Trace:
    """一次完整的 Agent 执行过程"""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""  # 会话 ID
    task: str = ""  # 用户任务描述

    spans: list[Span] = field(default_factory=list)

    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    status: SpanStatus = SpanStatus.STARTED
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        """总执行时长"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0

    @property
    def thinking_count(self) -> int:
        """思考轮数"""
        return sum(1 for s in self.spans if s.type == SpanType.THINKING)

    @property
    def tool_call_count(self) -> int:
        """工具调用次数"""
        return sum(1 for s in self.spans if s.type == SpanType.TOOL_CALL)

    @property
    def error_count(self) -> int:
        """错误次数"""
        return sum(1 for s in self.spans if s.type == SpanType.ERROR)

    @property
    def tool_success_rate(self) -> float:
        """工具调用成功率"""
        tool_spans = [s for s in self.spans if s.type == SpanType.TOOL_CALL]
        if not tool_spans:
            return 1.0
        success = sum(1 for s in tool_spans if s.status == SpanStatus.COMPLETED)
        return success / len(tool_spans)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "task": self.task,
            "spans": [s.to_dict() for s in self.spans],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "metadata": self.metadata,
            "summary": {
                "thinking_count": self.thinking_count,
                "tool_call_count": self.tool_call_count,
                "error_count": self.error_count,
                "tool_success_rate": self.tool_success_rate,
            },
        }
