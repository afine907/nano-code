"""CLI 控制台输出

提供丰富的终端输出功能，包括：
- 进度动画和状态显示
- 工具调用可视化
- 会话统计信息
- 语法高亮代码输出
"""

import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table

console = Console()

# 为了向后兼容，提供别名
Console = console.__class__
Spinner = Spinner
ProgressBar = None  # 占位符，实际未实现


@dataclass
class SessionStats:
    """会话统计信息"""

    message_count: int = 0
    tool_calls: int = 0
    total_tokens: int = 0
    start_time: float = field(default_factory=time.time)

    def elapsed_time(self) -> str:
        """返回格式化的已用时间"""
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{elapsed:.0f}s"
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes}m {seconds}s"

    def reset(self) -> None:
        """重置统计"""
        self.message_count = 0
        self.tool_calls = 0
        self.total_tokens = 0
        self.start_time = time.time()


# 全局会话统计
session_stats = SessionStats()


def print_welcome() -> None:
    """打印欢迎信息"""
    console.print(
        Panel.fit(
            "[bold blue]Nano-Code[/bold blue] - 迷你版编码助手\n"
            "输入你的问题，[dim]/help[/dim] 查看命令，Ctrl+D 退出",
            title="🤖 Welcome",
            border_style="blue",
        )
    )


def print_user(message: str) -> None:
    """打印用户消息"""
    console.print(f"\n[bold green]👤 You:[/bold green] {message}")
    session_stats.message_count += 1


def print_assistant(message: str) -> None:
    """打印助手消息"""
    console.print("\n[bold blue]🤖 Assistant:[/bold blue]")
    console.print(message)


def print_tool_call(tool_name: str, args: dict[str, Any]) -> None:
    """打印工具调用信息"""
    session_stats.tool_calls += 1

    # 格式化参数，截断过长的值
    formatted_args = []
    for k, v in args.items():
        v_str = str(v)
        if len(v_str) > 50:
            v_str = v_str[:47] + "..."
        formatted_args.append(f"{k}=[cyan]{v_str}[/cyan]")

    args_str = ", ".join(formatted_args)
    console.print(
        f"\n[yellow]🔧 Tool #{session_stats.tool_calls}:[/yellow] "
        f"[bold]{tool_name}[/bold]({args_str})"
    )


def print_tool_result(result: str, duration: float | None = None) -> None:
    """打印工具执行结果

    Args:
        result: 执行结果
        duration: 执行耗时（秒）
    """
    # 截断过长的结果
    display_result = result
    truncated = False
    if len(result) > 500:
        display_result = result[:500] + "..."
        truncated = True

    # 构建输出
    parts = []
    if duration is not None:
        parts.append(f"[dim]⏱ {duration:.2f}s[/dim]")
    if truncated:
        parts.append(f"[dim]({len(result)} chars)[/dim]")

    if parts:
        console.print(f"[dim]Result:[/dim] {display_result} " + " ".join(parts))
    else:
        console.print(f"[dim]Result:[/dim] {display_result}")


def print_error(message: str) -> None:
    """打印错误信息"""
    console.print(f"\n[bold red]❌ Error:[/bold red] {message}")


def print_thinking() -> Status:
    """返回思考状态（用于 with 语句）"""
    return console.status("[dim yellow]💭 Thinking...[/dim yellow]", spinner="dots")


@contextmanager
def thinking_animation(message: str = "Thinking") -> Generator[None, None, None]:
    """思考动画上下文管理器

    Args:
        message: 显示的消息

    Usage:
        with thinking_animation("Analyzing code"):
            # 执行耗时操作
            pass
    """
    spinner = Spinner("dots", text=f"[dim yellow]💭 {message}...[/dim yellow]")
    with Live(spinner, console=console, refresh_per_second=10):
        yield


def print_status_bar(model: str = "unknown", stats: SessionStats | None = None) -> None:
    """打印状态栏

    Args:
        model: 当前模型名称
        stats: 会话统计（默认使用全局统计）
    """
    if stats is None:
        stats = session_stats

    # 创建状态信息
    info_parts = [
        f"[bold]Model:[/bold] [cyan]{model}[/cyan]",
        f"[bold]Msgs:[/bold] {stats.message_count}",
        f"[bold]Tools:[/bold] {stats.tool_calls}",
        f"[bold]Time:[/bold] {stats.elapsed_time()}",
    ]

    if stats.total_tokens > 0:
        info_parts.append(f"[bold]Tokens:[/bold] {stats.total_tokens:,}")

    console.print("\n" + " │ ".join(info_parts))


def print_session_stats(model: str = "unknown") -> None:
    """打印详细的会话统计"""
    stats = session_stats

    table = Table(title="📊 Session Statistics", show_header=False, box=None)
    table.add_column("Key", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Model", model)
    table.add_row("Messages", str(stats.message_count))
    table.add_row("Tool Calls", str(stats.tool_calls))
    table.add_row("Session Duration", stats.elapsed_time())
    if stats.total_tokens > 0:
        table.add_row("Total Tokens", f"{stats.total_tokens:,}")

    console.print(table)


def print_help() -> None:
    """打印帮助信息"""
    help_text = """
[bold]📖 Commands:[/bold]
  [cyan]/help[/cyan]     - 显示此帮助
  [cyan]/clear[/cyan]    - 清空对话记忆
  [cyan]/stats[/cyan]    - 显示会话统计
  [cyan]/model[/cyan]    - 显示当前模型
  [cyan]/history[/cyan]  - 显示最近消息历史
  [cyan]/exit[/cyan]     - 退出程序

[bold]💡 Tips:[/bold]
  • 多行输入: 按 [dim]Tab[/dim] 换行，[dim]Enter[/dim] 发送
  • 取消当前输入: [dim]Ctrl+C[/dim]
  • 退出程序: [dim]Ctrl+D[/dim] 或 [dim]/exit[/dim]
"""
    console.print(Panel(help_text, border_style="blue", title="Help"))


def print_history(messages: list[Any], limit: int = 10) -> None:
    """打印消息历史

    Args:
        messages: 消息列表
        limit: 最大显示数量
    """
    if not messages:
        console.print("[dim]No messages in history[/dim]")
        return

    console.print(f"\n[bold]📜 Recent Messages ({len(messages)} total):[/bold]\n")

    # 显示最近的 N 条消息
    display_messages = messages[-limit:] if len(messages) > limit else messages

    for msg in display_messages:
        # 获取消息类型和内容
        msg_type = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", str(msg))

        # 截断内容
        if len(content) > 100:
            content = content[:97] + "..."

        # 根据类型选择颜色
        if msg_type == "human":
            icon = "👤"
            color = "green"
        elif msg_type == "ai":
            icon = "🤖"
            color = "blue"
        else:
            icon = "📝"
            color = "dim"

        console.print(f"  {icon} [{color}]{content}[/{color}]")

    if len(messages) > limit:
        console.print(f"\n  [dim]... and {len(messages) - limit} more[/dim]")


def print_model_info(model: str) -> None:
    """打印模型信息"""
    console.print(f"\n[bold]🤖 Current Model:[/bold] [cyan]{model}[/cyan]")


def format_code(code: str, language: str = "python") -> str:
    """格式化代码块

    Args:
        code: 代码内容
        language: 语言类型

    Returns:
        格式化后的代码字符串
    """
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    with console.capture() as capture:
        console.print(syntax)
    return capture.get()


def print_code(code: str, language: str = "python") -> None:
    """打印高亮代码"""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def print_success(message: str) -> None:
    """打印成功消息"""
    console.print(f"\n[bold green]✅ {message}[/bold green]")


def print_warning(message: str) -> None:
    """打印警告消息"""
    console.print(f"\n[bold yellow]⚠️ {message}[/bold yellow]")


def print_info(message: str) -> None:
    """打印信息消息"""
    console.print(f"\n[bold blue]ℹ️ {message}[/bold blue]")
