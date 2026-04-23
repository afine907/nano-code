# AgentOps 系统设计文档

> 版本: 1.0  
> 日期: 2026-04-23  
> 作者: jojo  
> 依赖: 功能设计文档 v1.0

---

## 1. 架构概览

### 1.1 模块划分

```
src/jojo_code/ops/
├── __init__.py           # 模块入口
├── trace.py              # Trace/Span 数据结构
├── collector.py          # 数据收集器
├── metrics.py            # 指标计算引擎
├── evaluator.py          # 评估引擎
├── exporter.py           # 数据导出
├── dashboard.py          # 监控面板
└── config.py             # 配置管理
```

### 1.2 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Loop (LangGraph)                   │
│                                                             │
│   thinking ────▶ execute ────▶ observe ────▶ thinking       │
│       │              │             │                        │
└───────┼──────────────┼─────────────┼────────────────────────┘
        │              │             │
        ▼              ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Collector (收集器)                      │
│                                                             │
│   记录每个 Span: 类型、输入、输出、时间、状态               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Trace Store (存储)                     │
│                                                             │
│   内存缓存 + 可选持久化 (.jojo-code/traces/*.json)          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Metrics Engine  │ │ Evaluator Engine │ │    Exporter      │
│   (指标计算)      │ │    (评估)        │ │    (导出)        │
└──────────────────┘ └──────────────────┘ └──────────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Dashboard (展示)                        │
│                                                             │
│   CLI 表格 / Markdown 报告 / JSON 文件                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 数据结构设计

### 2.1 Span（跨度）

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum
import uuid

class SpanType(Enum):
    THINKING = "thinking"      # Agent 思考
    TOOL_CALL = "tool_call"    # 工具调用
    OBSERVE = "observe"        # 观察结果
    ERROR = "error"            # 错误

class SpanStatus(Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Span:
    """Agent 执行的一个步骤"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trace_id: str = ""              # 所属 Trace
    parent_id: Optional[str] = None # 父 Span (用于嵌套)
    
    type: SpanType = SpanType.THINKING
    name: str = ""                  # span 名称，如 "read_file"
    
    input: Any = None               # 输入数据
    output: Any = None              # 输出数据
    error: Optional[str] = None     # 错误信息
    
    status: SpanStatus = SpanStatus.STARTED
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    metadata: dict = field(default_factory=dict)  # 额外元数据
    
    @property
    def duration_ms(self) -> int:
        """执行时长（毫秒）"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "type": self.type.value,
            "name": self.name,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }
```

### 2.2 Trace（追踪）

```python
@dataclass
class Trace:
    """一次完整的 Agent 执行过程"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""            # 会话 ID
    task: str = ""                  # 用户任务描述
    
    spans: list[Span] = field(default_factory=list)
    
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
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
            }
        }
```

---

## 3. 核心组件设计

### 3.1 Collector（收集器）

**职责**: 在 Agent 循环中收集数据

```python
class Collector:
    """数据收集器 - 在 Agent 循环中埋点"""
    
    def __init__(self, config: OpsConfig):
        self.config = config
        self.current_trace: Optional[Trace] = None
        self.trace_store: list[Trace] = []
    
    def start_trace(self, task: str, session_id: str = "") -> Trace:
        """开始一个新的 Trace"""
        trace = Trace(
            session_id=session_id,
            task=task,
        )
        self.current_trace = trace
        return trace
    
    def end_trace(self, status: SpanStatus = SpanStatus.COMPLETED) -> Optional[Trace]:
        """结束当前 Trace"""
        if self.current_trace:
            self.current_trace.end_time = datetime.now()
            self.current_trace.status = status
            self.trace_store.append(self.current_trace)
            
            # 可选：持久化
            if self.config.persist_traces:
                self._persist_trace(self.current_trace)
            
            trace = self.current_trace
            self.current_trace = None
            return trace
        return None
    
    def start_span(
        self, 
        span_type: SpanType, 
        name: str, 
        input_data: Any = None,
        parent_id: Optional[str] = None
    ) -> Optional[Span]:
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
    
    def end_span(
        self, 
        span: Span, 
        output_data: Any = None, 
        error: Optional[str] = None
    ) -> None:
        """结束一个 Span"""
        span.end_time = datetime.now()
        span.output = output_data
        span.error = error
        span.status = SpanStatus.FAILED if error else SpanStatus.COMPLETED
    
    def _persist_trace(self, trace: Trace) -> None:
        """持久化 Trace 到文件"""
        import json
        from pathlib import Path
        
        trace_dir = Path(self.config.trace_dir)
        trace_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = trace_dir / f"{trace.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(trace.to_dict(), f, ensure_ascii=False, indent=2)
```

### 3.2 Metrics Engine（指标引擎）

**职责**: 从 Trace 数据计算指标

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

@dataclass
class MetricsSummary:
    """指标汇总"""
    total_traces: int = 0
    completed_traces: int = 0
    failed_traces: int = 0
    
    avg_thinking_rounds: float = 0.0
    avg_tool_calls: float = 0.0
    avg_duration_ms: float = 0.0
    
    tool_success_rate: float = 0.0
    task_success_rate: float = 0.0
    
    tool_usage: dict[str, int] = None  # 工具使用次数统计
    error_types: dict[str, int] = None  # 错误类型统计
    
    def __post_init__(self):
        self.tool_usage = self.tool_usage or {}
        self.error_types = self.error_types or {}

class MetricsEngine:
    """指标计算引擎"""
    
    def __init__(self, traces: list[Trace]):
        self.traces = traces
    
    def calculate(self) -> MetricsSummary:
        """计算所有指标"""
        if not self.traces:
            return MetricsSummary()
        
        completed = [t for t in self.traces if t.status == SpanStatus.COMPLETED]
        failed = [t for t in self.traces if t.status == SpanStatus.FAILED]
        
        total_thinking = sum(t.thinking_count for t in self.traces)
        total_tool_calls = sum(t.tool_call_count for t in self.traces)
        total_duration = sum(t.duration_ms for t in self.traces)
        
        # 工具使用统计
        tool_usage: dict[str, int] = {}
        for trace in self.traces:
            for span in trace.spans:
                if span.type == SpanType.TOOL_CALL:
                    tool_usage[span.name] = tool_usage.get(span.name, 0) + 1
        
        # 错误类型统计
        error_types: dict[str, int] = {}
        for trace in self.traces:
            for span in trace.spans:
                if span.error:
                    # 简单分类：取错误信息前 50 字符
                    error_key = span.error[:50]
                    error_types[error_key] = error_types.get(error_key, 0) + 1
        
        return MetricsSummary(
            total_traces=len(self.traces),
            completed_traces=len(completed),
            failed_traces=len(failed),
            avg_thinking_rounds=total_thinking / len(self.traces),
            avg_tool_calls=total_tool_calls / len(self.traces),
            avg_duration_ms=total_duration / len(self.traces),
            tool_success_rate=sum(t.tool_success_rate for t in self.traces) / len(self.traces),
            task_success_rate=len(completed) / len(self.traces) if self.traces else 0,
            tool_usage=tool_usage,
            error_types=error_types,
        )
    
    def filter_by_time(
        self, 
        start: Optional[datetime] = None, 
        end: Optional[datetime] = None
    ) -> list[Trace]:
        """按时间范围过滤"""
        filtered = self.traces
        if start:
            filtered = [t for t in filtered if t.start_time >= start]
        if end:
            filtered = [t for t in filtered if t.start_time <= end]
        return filtered
    
    def filter_by_session(self, session_id: str) -> list[Trace]:
        """按会话过滤"""
        return [t for t in self.traces if t.session_id == session_id]
```

### 3.3 Evaluator（评估器）

**职责**: 评估 Agent 行为质量

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class EvaluationResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"

@dataclass
class EvaluationScore:
    """评估得分"""
    result: EvaluationResult
    score: float  # 0.0 - 1.0
    reason: str
    details: dict = None

class BaseEvaluator(ABC):
    """评估器基类"""
    
    @abstractmethod
    def evaluate(self, trace: Trace) -> EvaluationScore:
        """评估单个 Trace"""
        pass

class PlanningEvaluator(BaseEvaluator):
    """规划质量评估器"""
    
    def evaluate(self, trace: Trace) -> EvaluationScore:
        """评估规划质量"""
        issues = []
        score = 1.0
        
        # 规则 1: 思考轮数过多（可能陷入循环）
        if trace.thinking_count > 10:
            issues.append(f"思考轮数过多: {trace.thinking_count}")
            score -= 0.2
        
        # 规则 2: 工具调用失败率高
        if trace.tool_success_rate < 0.8:
            issues.append(f"工具调用成功率低: {trace.tool_success_rate:.2%}")
            score -= 0.2
        
        # 规则 3: 有错误发生
        if trace.error_count > 0:
            issues.append(f"发生错误: {trace.error_count} 次")
            score -= 0.1
        
        # 规则 4: 重复工具调用（可能没理解任务）
        tool_calls = [s.name for s in trace.spans if s.type == SpanType.TOOL_CALL]
        if len(tool_calls) != len(set(tool_calls)):
            issues.append("存在重复的工具调用")
            score -= 0.1
        
        score = max(0.0, score)
        
        result = EvaluationResult.PASS
        if score < 0.6:
            result = EvaluationResult.FAIL
        elif score < 0.8:
            result = EvaluationResult.PARTIAL
        
        return EvaluationScore(
            result=result,
            score=score,
            reason="; ".join(issues) if issues else "规划质量良好",
            details={"issues": issues}
        )

class TestCaseEvaluator(BaseEvaluator):
    """Test Case 评估器"""
    
    def __init__(self, test_cases: list[dict]):
        """
        test_cases 格式:
        [
            {
                "task": "读取 README.md",
                "expected_tools": ["read_file"],
                "expected_output_contains": ["README"],
                "max_rounds": 3,
            }
        ]
        """
        self.test_cases = test_cases
    
    def evaluate(self, trace: Trace) -> EvaluationScore:
        """根据 test case 评估"""
        # 找到匹配的 test case
        test_case = None
        for tc in self.test_cases:
            if tc["task"] in trace.task or trace.task in tc["task"]:
                test_case = tc
                break
        
        if not test_case:
            return EvaluationScore(
                result=EvaluationResult.PARTIAL,
                score=0.5,
                reason="未找到匹配的 test case"
            )
        
        issues = []
        score = 1.0
        
        # 检查工具调用
        actual_tools = [s.name for s in trace.spans if s.type == SpanType.TOOL_CALL]
        expected_tools = test_case.get("expected_tools", [])
        
        for expected in expected_tools:
            if expected not in actual_tools:
                issues.append(f"缺少预期工具: {expected}")
                score -= 0.2
        
        # 检查轮数
        max_rounds = test_case.get("max_rounds", 10)
        if trace.thinking_count > max_rounds:
            issues.append(f"超过最大轮数: {trace.thinking_count} > {max_rounds}")
            score -= 0.2
        
        # 检查输出
        expected_output = test_case.get("expected_output_contains", [])
        for expected in expected_output:
            found = False
            for span in trace.spans:
                if span.output and expected in str(span.output):
                    found = True
                    break
            if not found:
                issues.append(f"输出未包含: {expected}")
                score -= 0.1
        
        score = max(0.0, score)
        
        result = EvaluationResult.PASS if score >= 0.8 else (
            EvaluationResult.PARTIAL if score >= 0.6 else EvaluationResult.FAIL
        )
        
        return EvaluationScore(
            result=result,
            score=score,
            reason="; ".join(issues) if issues else "通过所有检查",
            details={"test_case": test_case, "issues": issues}
        )

class LLMEvaluator(BaseEvaluator):
    """LLM 评估器 - 用另一个 LLM 评估规划质量"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def evaluate(self, trace: Trace) -> EvaluationScore:
        """使用 LLM 评估"""
        prompt = f"""请评估以下 Agent 执行过程的质量：

任务: {trace.task}

执行步骤:
{self._format_spans(trace.spans)}

请从以下维度评估（每项 0-10 分）：
1. 任务理解是否准确
2. 工具选择是否合理
3. 执行顺序是否高效
4. 是否存在无效循环
5. 最终是否完成任务

请以 JSON 格式返回：
{{"scores": [s1, s2, s3, s4, s5], "reason": "简要说明", "suggestions": ["改进建议"]}}
"""
        # 调用 LLM
        response = self.llm.invoke(prompt)
        
        # 解析结果
        import json
        try:
            result = json.loads(response.content)
            avg_score = sum(result["scores"]) / 50.0  # 归一化到 0-1
            
            return EvaluationScore(
                result=EvaluationResult.PASS if avg_score >= 0.7 else EvaluationResult.FAIL,
                score=avg_score,
                reason=result["reason"],
                details=result
            )
        except:
            return EvaluationScore(
                result=EvaluationResult.PARTIAL,
                score=0.5,
                reason="LLM 评估解析失败"
            )
    
    def _format_spans(self, spans: list[Span]) -> str:
        lines = []
        for i, span in enumerate(spans, 1):
            lines.append(f"{i}. [{span.type.value}] {span.name}")
            if span.input:
                lines.append(f"   输入: {span.input}")
            if span.output:
                lines.append(f"   输出: {str(span.output)[:100]}")
        return "\n".join(lines)
```

### 3.4 Exporter（导出器）

**职责**: 导出数据和报告

```python
import json
from pathlib import Path
from datetime import datetime

class Exporter:
    """数据导出器"""
    
    @staticmethod
    def export_traces_json(traces: list[Trace], output_path: str) -> None:
        """导出 Traces 为 JSON"""
        data = [t.to_dict() for t in traces]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def export_metrics_markdown(metrics: MetricsSummary, output_path: str) -> None:
        """导出指标为 Markdown 报告"""
        report = f"""# AgentOps 报告

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 指标概览

| 指标 | 值 |
|------|-----|
| 总任务数 | {metrics.total_traces} |
| 成功任务 | {metrics.completed_traces} |
| 失败任务 | {metrics.failed_traces} |
| 任务成功率 | {metrics.task_success_rate:.2%} |
| 平均思考轮数 | {metrics.avg_thinking_rounds:.1f} |
| 平均工具调用 | {metrics.avg_tool_calls:.1f} |
| 工具成功率 | {metrics.tool_success_rate:.2%} |
| 平均耗时 | {metrics.avg_duration_ms:.0f}ms |

## 🔧 工具使用统计

| 工具 | 调用次数 |
|------|---------|
"""
        for tool, count in sorted(metrics.tool_usage.items(), key=lambda x: -x[1]):
            report += f"| {tool} | {count} |\n"
        
        if metrics.error_types:
            report += f"""
## ❌ 错误统计

| 错误 | 次数 |
|------|------|
"""
            for error, count in sorted(metrics.error_types.items(), key=lambda x: -x[1]):
                report += f"| {error} | {count} |\n"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
```

### 3.5 Dashboard（监控面板）

**职责**: CLI 实时展示

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

class Dashboard:
    """CLI 监控面板"""
    
    def __init__(self):
        self.console = Console()
    
    def show_current_trace(self, trace: Trace) -> None:
        """显示当前 Trace 状态"""
        self.console.clear()
        
        # 任务信息
        self.console.print(Panel(
            f"[bold]{trace.task}[/bold]",
            title="📋 当前任务",
            border_style="blue"
        ))
        
        # 执行步骤
        table = Table(title="执行步骤")
        table.add_column("#", style="dim")
        table.add_column("类型")
        table.add_column("名称")
        table.add_column("状态")
        table.add_column("耗时")
        
        for i, span in enumerate(trace.spans, 1):
            status_style = {
                SpanStatus.COMPLETED: "green",
                SpanStatus.FAILED: "red",
                SpanStatus.STARTED: "yellow",
            }.get(span.status, "white")
            
            table.add_row(
                str(i),
                span.type.value,
                span.name or "-",
                f"[{status_style}]{span.status.value}[/{status_style}]",
                f"{span.duration_ms}ms"
            )
        
        self.console.print(table)
    
    def show_metrics(self, metrics: MetricsSummary) -> None:
        """显示指标汇总"""
        # 成功率进度条
        self.console.print(Panel(
            f"""
[bold green]任务成功率[/bold green]: {metrics.task_success_rate:.1%}
[bold blue]工具成功率[/bold blue]: {metrics.tool_success_rate:.1%}
[bold yellow]平均思考轮数[/bold yellow]: {metrics.avg_thinking_rounds:.1f}
[bold cyan]平均耗时[/bold cyan]: {metrics.avg_duration_ms:.0f}ms
""",
            title="📊 指标汇总",
            border_style="green"
        ))
        
        # 工具使用表格
        if metrics.tool_usage:
            table = Table(title="🔧 工具使用")
            table.add_column("工具")
            table.add_column("次数", justify="right")
            
            for tool, count in sorted(metrics.tool_usage.items(), key=lambda x: -x[1]):
                table.add_row(tool, str(count))
            
            self.console.print(table)
```

---

## 4. 集成方案

### 4.1 在 Agent 循环中埋点

修改 `src/jojo_code/agent/nodes.py`:

```python
from jojo_code.ops import Collector, SpanType

# 在 AgentState 中添加 collector
class AgentState(TypedDict):
    messages: list[BaseMessage]
    # ... 其他字段
    ops_collector: Optional[Collector]

# 在 thinking 节点
def thinking_node(state: AgentState) -> dict:
    collector = state.get("ops_collector")
    
    # 开始 thinking span
    span = None
    if collector:
        span = collector.start_span(SpanType.THINKING, "thinking", state["messages"][-1].content)
    
    # ... 原有逻辑
    
    # 结束 span
    if collector and span:
        collector.end_span(span, output_data=response.content)
    
    return {"messages": [response]}

# 在 tool 节点
def tool_node(state: AgentState) -> dict:
    collector = state.get("ops_collector")
    
    for tool_call in tool_calls:
        # 开始 tool span
        span = None
        if collector:
            span = collector.start_span(SpanType.TOOL_CALL, tool_call["name"], tool_call["args"])
        
        # 执行工具
        try:
            result = execute_tool(tool_call)
            if collector and span:
                collector.end_span(span, output_data=result)
        except Exception as e:
            if collector and span:
                collector.end_span(span, error=str(e))
```

### 4.2 配置选项

在 `pyproject.toml` 或 `.env` 中配置:

```toml
[tool.jojo_code.ops]
enabled = true
persist_traces = true
trace_dir = ".jojo-code/traces"
```

或环境变量:

```bash
JOJO_CODE_OPS_ENABLED=true
JOJO_CODE_OPS_TRACE_DIR=.jojo-code/traces
```

---

## 5. 测试策略

### 5.1 单元测试

- 测试 Span/Trace 数据结构
- 测试 Collector 的 span 管理
- 测试 MetricsEngine 的计算逻辑
- 测试各 Evaluator 的评估规则

### 5.2 集成测试

- 测试 Agent 循环埋点
- 测试完整 Trace 收集
- 测试指标计算准确性

### 5.3 评估测试

- 准备 test case 数据集
- 运行自动化评估
- 对比预期 vs 实际

---

## 6. 性能考量

### 6.1 内存管理

- Trace 存储在内存中，限制最大数量（如 1000 条）
- 超过限制时，LRU 淘汰旧 Trace
- 可选：异步持久化到磁盘

### 6.2 延迟优化

- Collector 操作异步化
- 批量写入文件
- 避免在 span 中存储大对象

### 6.3 存储优化

- Trace 文件按日期分目录
- 定期清理过期文件
- 压缩历史数据

---

## 7. 扩展性

### 7.1 自定义指标

用户可以注册自定义指标计算函数:

```python
from jojo_code.ops import MetricsEngine, register_metric

@register_metric("custom_token_efficiency")
def calculate_token_efficiency(traces: list[Trace]) -> float:
    # 自定义计算逻辑
    pass
```

### 7.2 自定义评估器

用户可以实现自己的评估器:

```python
from jojo_code.ops import BaseEvaluator, EvaluationScore

class MyCustomEvaluator(BaseEvaluator):
    def evaluate(self, trace: Trace) -> EvaluationScore:
        # 自定义评估逻辑
        pass
```

### 7.3 导出格式扩展

支持注册新的导出格式:

```python
from jojo_code.ops import Exporter, register_exporter

@register_exporter("csv")
def export_csv(traces, output_path):
    # CSV 导出逻辑
    pass
```

---

## 8. 实现优先级

### Phase 1 (MVP) - 1 周

1. ✅ 数据结构（Span/Trace）
2. ✅ Collector 实现
3. ✅ Agent 埋点
4. ✅ JSON 导出

### Phase 2 - 1 周

1. ✅ MetricsEngine 实现
2. ✅ CLI 指标展示
3. ✅ Markdown 报告

### Phase 3 - 2 周

1. ✅ PlanningEvaluator
2. ✅ TestCaseEvaluator
3. ✅ LLMEvaluator
4. ✅ 评估报告

### Phase 4 (可选)

1. Web Dashboard
2. Prometheus 集成
3. 实时告警

---

## 9. 文件清单

实现完成后的文件结构:

```
src/jojo_code/ops/
├── __init__.py           # 导出主要类
├── models.py             # Span, Trace 数据结构
├── collector.py          # Collector 实现
├── metrics.py            # MetricsEngine 实现
├── evaluator.py          # 评估器实现
├── exporter.py           # 导出器实现
├── dashboard.py          # Dashboard 实现
├── config.py             # 配置管理
└── utils.py              # 工具函数

tests/ops/
├── test_models.py        # 数据结构测试
├── test_collector.py     # Collector 测试
├── test_metrics.py       # Metrics 测试
├── test_evaluator.py     # Evaluator 测试
└── test_integration.py   # 集成测试
```
