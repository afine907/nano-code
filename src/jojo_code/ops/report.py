"""AgentOps 评估报告生成器"""

from datetime import datetime

from .evaluator import EvaluationResult, EvaluationScore
from .metrics import MetricsSummary
from .models import SpanStatus, Trace


class ReportGenerator:
    """评估报告生成器"""

    @staticmethod
    def generate_evaluation_report(
        trace: Trace,
        score: EvaluationScore,
        output_path: str | None = None,
    ) -> str:
        """生成单个 Trace 的评估报告"""
        report = f"""# AgentOps 评估报告

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📋 任务信息

| 项目 | 值 |
|------|-----|
| Trace ID | {trace.id} |
| 任务 | {trace.task} |
| 状态 | {trace.status.value} |
| 耗时 | {trace.duration_ms}ms |

## 📊 评估结果

| 指标 | 值 |
|------|-----|
| **结果** | {score.result.value.upper()} |
| **得分** | {score.score:.2%} |
| **原因** | {score.reason} |

## 📈 执行统计

| 指标 | 值 |
|------|-----|
| 思考轮数 | {trace.thinking_count} |
| 工具调用 | {trace.tool_call_count} |
| 错误次数 | {trace.error_count} |
| 工具成功率 | {trace.tool_success_rate:.2%} |

## 🔧 工具使用

"""
        # 工具使用详情
        tools_used = [s for s in trace.spans if s.type.name == "TOOL_CALL"]
        if tools_used:
            report += "| 工具 | 状态 | 耗时 |\n|------|------|------|\n"
            for tool in tools_used:
                status_icon = "✅" if tool.status == SpanStatus.COMPLETED else "❌"
                report += f"| {tool.name} | {status_icon} | {tool.duration_ms}ms |\n"
        else:
            report += "无工具调用\n"

        # 错误详情
        errors = [s for s in trace.spans if s.error]
        if errors:
            report += "\n## ❌ 错误详情\n\n"
            for error in errors:
                report += f"- **{error.name}**: {error.error}\n"

        # 评估详情
        if score.details:
            report += "\n## 📝 评估详情\n\n```json\n"
            import json

            report += json.dumps(score.details, indent=2, ensure_ascii=False)
            report += "\n```\n"

        # 改进建议
        report += "\n## 💡 改进建议\n\n"
        suggestions = ReportGenerator._generate_suggestions(trace, score)
        for suggestion in suggestions:
            report += f"- {suggestion}\n"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

        return report

    @staticmethod
    def generate_summary_report(
        metrics: MetricsSummary,
        evaluation_scores: list[EvaluationScore] | None = None,
        output_path: str | None = None,
    ) -> str:
        """生成汇总报告"""
        report = f"""# AgentOps 汇总报告

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 时间范围: {metrics.start_time.strftime("%Y-%m-%d %H:%M") if metrics.start_time else "N/A"} -
{metrics.end_time.strftime("%Y-%m-%d %H:%M") if metrics.end_time else "N/A"}

## 📊 总体指标

| 指标 | 值 |
|------|-----|
| 总任务数 | {metrics.total_traces} |
| 成功任务 | {metrics.completed_traces} |
| 失败任务 | {metrics.failed_traces} |
| 任务成功率 | {metrics.task_success_rate:.2%} |
| 平均思考轮数 | {metrics.avg_thinking_rounds:.1f} |
| 平均工具调用 | {metrics.avg_tool_calls:.1f} |
| 平均耗时 | {metrics.avg_duration_ms:.0f}ms |
| 工具成功率 | {metrics.tool_success_rate:.2%} |

## 🔧 工具使用统计

| 工具 | 调用次数 | 占比 |
|------|---------|------|
"""
        total_tool_calls = sum(metrics.tool_usage.values())
        for tool, count in sorted(metrics.tool_usage.items(), key=lambda x: -x[1]):
            percentage = count / total_tool_calls * 100 if total_tool_calls > 0 else 0
            report += f"| {tool} | {count} | {percentage:.1f}% |\n"

        if metrics.error_types:
            report += """
## ❌ 错误统计

| 错误 | 次数 |
|------|------|
"""
            for error, count in sorted(metrics.error_types.items(), key=lambda x: -x[1])[:10]:
                report += f"| {error} | {count} |\n"

        # 评估汇总
        if evaluation_scores:
            pass_count = sum(1 for s in evaluation_scores if s.result == EvaluationResult.PASS)
            partial_count = sum(
                1 for s in evaluation_scores if s.result == EvaluationResult.PARTIAL
            )
            fail_count = sum(1 for s in evaluation_scores if s.result == EvaluationResult.FAIL)
            avg_score = sum(s.score for s in evaluation_scores) / len(evaluation_scores)

            report += f"""
## 📈 评估汇总

| 结果 | 数量 | 占比 |
|------|------|------|
| ✅ 通过 | {pass_count} | {pass_count / len(evaluation_scores):.1%} |
| ⚠️ 部分通过 | {partial_count} | {partial_count / len(evaluation_scores):.1%} |
| ❌ 失败 | {fail_count} | {fail_count / len(evaluation_scores):.1%} |

**平均得分**: {avg_score:.2%}
"""

        # 改进建议
        report += """
## 💡 改进建议

"""
        suggestions = ReportGenerator._generate_summary_suggestions(metrics, evaluation_scores)
        for suggestion in suggestions:
            report += f"- {suggestion}\n"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

        return report

    @staticmethod
    def _generate_suggestions(trace: Trace, score: EvaluationScore) -> list[str]:
        """生成改进建议"""
        suggestions = []

        if trace.thinking_count > 5:
            suggestions.append("考虑优化任务拆解逻辑，减少思考轮数")

        if trace.tool_success_rate < 0.8:
            suggestions.append("工具调用失败率较高，检查参数传递和权限")

        if trace.error_count > 0:
            suggestions.append("存在错误，建议增加错误处理和重试机制")

        if trace.duration_ms > 10000:
            suggestions.append("耗时较长，考虑并行执行或优化工具性能")

        if score.result == EvaluationResult.FAIL:
            suggestions.append("评估未通过，建议查看详细日志定位问题")

        if not suggestions:
            suggestions.append("表现良好，继续保持")

        return suggestions

    @staticmethod
    def _generate_summary_suggestions(
        metrics: MetricsSummary, evaluation_scores: list[EvaluationScore] | None
    ) -> list[str]:
        """生成汇总改进建议"""
        suggestions = []

        if metrics.task_success_rate < 0.9:
            suggestions.append(f"任务成功率为 {metrics.task_success_rate:.1%}，建议分析失败原因")

        if metrics.avg_thinking_rounds > 3:
            suggestions.append("平均思考轮数较高，考虑优化 Agent 规划能力")

        if metrics.tool_success_rate < 0.95:
            suggestions.append("工具成功率偏低，建议检查工具实现和错误处理")

        if metrics.error_types:
            top_error = list(metrics.error_types.keys())[0]
            suggestions.append(f"最常见错误: {top_error}，建议优先解决")

        if evaluation_scores:
            fail_rate = sum(
                1 for s in evaluation_scores if s.result == EvaluationResult.FAIL
            ) / len(evaluation_scores)
            if fail_rate > 0.1:
                suggestions.append(f"评估失败率 {fail_rate:.1%}，建议优化 Agent 核心逻辑")

        if not suggestions:
            suggestions.append("整体表现良好，继续保持")

        return suggestions
