"""AgentOps 数据导出"""

import json
from datetime import datetime

from .models import Trace


class Exporter:
    """数据导出器"""

    @staticmethod
    def export_traces_json(traces: list[Trace], output_path: str) -> None:
        """导出 Traces 为 JSON"""
        data = [t.to_dict() for t in traces]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def export_trace_json(trace: Trace, output_path: str) -> None:
        """导出单个 Trace 为 JSON"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(trace.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def export_summary_markdown(
        total_traces: int,
        completed_traces: int,
        failed_traces: int,
        avg_thinking_rounds: float,
        avg_tool_calls: float,
        avg_duration_ms: float,
        tool_success_rate: float,
        task_success_rate: float,
        tool_usage: dict[str, int],
        error_types: dict[str, int] | None = None,
        output_path: str | None = None,
    ) -> str:
        """导出指标为 Markdown 报告"""
        report = f"""# AgentOps 报告

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 指标概览

| 指标 | 值 |
|------|-----|
| 总任务数 | {total_traces} |
| 成功任务 | {completed_traces} |
| 失败任务 | {failed_traces} |
| 任务成功率 | {task_success_rate:.2%} |
| 平均思考轮数 | {avg_thinking_rounds:.1f} |
| 平均工具调用 | {avg_tool_calls:.1f} |
| 工具成功率 | {tool_success_rate:.2%} |
| 平均耗时 | {avg_duration_ms:.0f}ms |

## 🔧 工具使用统计

| 工具 | 调用次数 |
|------|---------|
"""
        for tool, count in sorted(tool_usage.items(), key=lambda x: -x[1]):
            report += f"| {tool} | {count} |\n"

        if error_types:
            report += """
## ❌ 错误统计

| 错误 | 次数 |
|------|------|
"""
            for error, count in sorted(error_types.items(), key=lambda x: -x[1]):
                report += f"| {error} | {count} |\n"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

        return report
