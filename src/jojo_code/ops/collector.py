"""AgentOps 数据收集器"""

import json
from datetime import datetime
from typing import Any

from .config import OpsConfig
from .models import Span, SpanStatus, SpanType, Trace


class Collector:
    """数据收集器 - 在 Agent 循环中埋点"""

    def __init__(self, config: OpsConfig | None = None):
        self.config = config or OpsConfig.from_env()
        self.current_trace: Trace | None = None
        self.trace_store: list[Trace] = []

    def start_trace(self, task: str, session_id: str = "") -> Trace:
        """开始一个新的 Trace"""
        trace = Trace(
            session_id=session_id,
            task=task,
        )
        self.current_trace = trace
        return trace

    def end_trace(self, status: SpanStatus = SpanStatus.COMPLETED) -> Trace | None:
        """结束当前 Trace"""
        if not self.current_trace:
            return None

        self.current_trace.end_time = datetime.now()
        self.current_trace.status = status

        # 添加到存储
        self.trace_store.append(self.current_trace)

        # LRU 淘汰
        if len(self.trace_store) > self.config.max_traces_in_memory:
            self.trace_store.pop(0)

        # 持久化
        if self.config.persist_traces:
            self._persist_trace(self.current_trace)

        trace = self.current_trace
        self.current_trace = None
        return trace

    def start_span(
        self, span_type: SpanType, name: str, input_data: Any = None, parent_id: str | None = None
    ) -> Span | None:
        """开始一个 Span"""
        if not self.current_trace:
            return None

        span = Span(
            trace_id=self.current_trace.id,
            parent_id=parent_id,
            type=span_type,
            name=name,
            input=input_data,
        )
        self.current_trace.spans.append(span)
        return span

    def end_span(self, span: Span, output_data: Any = None, error: str | None = None) -> None:
        """结束一个 Span"""
        span.end_time = datetime.now()
        span.output = output_data
        span.error = error
        span.status = SpanStatus.FAILED if error else SpanStatus.COMPLETED

    def record_tool_call(
        self, tool_name: str, args: dict, result: Any = None, error: str | None = None
    ) -> Span | None:
        """记录工具调用（便捷方法）"""
        span = self.start_span(SpanType.TOOL_CALL, tool_name, args)
        if span:
            self.end_span(span, output_data=result, error=error)
        return span

    def record_thinking(self, thinking_content: str, result: Any = None) -> Span | None:
        """记录思考过程（便捷方法）"""
        span = self.start_span(SpanType.THINKING, "thinking", thinking_content)
        if span:
            self.end_span(span, output_data=result)
        return span

    def record_error(self, error_message: str) -> Span | None:
        """记录错误（便捷方法）"""
        span = self.start_span(SpanType.ERROR, "error", error_message)
        if span:
            self.end_span(span, error=error_message)
        return span

    def get_current_trace(self) -> Trace | None:
        """获取当前 Trace"""
        return self.current_trace

    def get_all_traces(self) -> list[Trace]:
        """获取所有 Trace"""
        return self.trace_store

    def clear_traces(self) -> None:
        """清空 Trace 存储"""
        self.trace_store.clear()

    def _persist_trace(self, trace: Trace) -> None:
        """持久化 Trace 到文件"""
        trace_dir = self.config.get_trace_path()
        trace_dir.mkdir(parents=True, exist_ok=True)

        # 按日期分目录
        date_dir = trace_dir / trace.start_time.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        file_path = date_dir / f"{trace.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(trace.to_dict(), f, ensure_ascii=False, indent=2)

    def load_traces_from_disk(self) -> list[Trace]:
        """从磁盘加载历史 Trace"""
        trace_dir = self.config.get_trace_path()
        if not trace_dir.exists():
            return []

        traces = []
        for json_file in trace_dir.rglob("*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    trace = self._dict_to_trace(data)
                    traces.append(trace)
            except Exception:
                continue

        return traces

    def _dict_to_trace(self, data: dict) -> Trace:
        """字典转 Trace 对象"""
        start_time_str = data.get("start_time")
        end_time_str = data.get("end_time")

        trace = Trace(
            id=data.get("id", ""),
            session_id=data.get("session_id", ""),
            task=data.get("task", ""),
            start_time=(
                datetime.fromisoformat(start_time_str) if start_time_str else datetime.now()
            ),
            end_time=(datetime.fromisoformat(end_time_str) if end_time_str else None),
            status=SpanStatus(data.get("status", "started")),
            metadata=data.get("metadata", {}),
        )

        for span_data in data.get("spans", []):
            span_start_time_str = span_data.get("start_time")
            span_end_time_str = span_data.get("end_time")

            span = Span(
                id=span_data.get("id", ""),
                trace_id=span_data.get("trace_id", ""),
                parent_id=span_data.get("parent_id"),
                type=SpanType(span_data.get("type", "thinking")),
                name=span_data.get("name", ""),
                input=span_data.get("input"),
                output=span_data.get("output"),
                error=span_data.get("error"),
                status=SpanStatus(span_data.get("status", "started")),
                start_time=(
                    datetime.fromisoformat(span_start_time_str)
                    if span_start_time_str
                    else datetime.now()
                ),
                end_time=(datetime.fromisoformat(span_end_time_str) if span_end_time_str else None),
                metadata=span_data.get("metadata", {}),
            )
            trace.spans.append(span)

        return trace
