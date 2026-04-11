"""CLI 控制台输出"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def print_welcome() -> None:
    """打印欢迎信息"""
    console.print(
        Panel.fit(
            "[bold blue]Nano-Code[/bold blue] - 迷你版编码助手\n输入你的问题，Ctrl+D 退出",
            title="Welcome",
            border_style="blue",
        )
    )


def print_user(message: str) -> None:
    """打印用户消息"""
    console.print(f"\n[bold green]You:[/bold green] {message}")


def print_assistant(message: str) -> None:
    """打印助手消息"""
    console.print("\n[bold blue]Assistant:[/bold blue]")
    console.print(message)


def print_tool_call(tool_name: str, args: dict[str, Any]) -> None:
    """打印工具调用信息"""
    args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
    console.print(f"\n[yellow]🔧 Tool:[/yellow] {tool_name}({args_str})")


def print_tool_result(result: str) -> None:
    """打印工具执行结果"""
    # 截断过长的结果
    if len(result) > 500:
        result = result[:500] + "..."

    console.print(f"[dim]Result:[/dim] {result}")


def print_error(message: str) -> None:
    """打印错误信息"""
    console.print(f"\n[bold red]Error:[/bold red] {message}")


def print_thinking() -> None:
    """打印思考状态"""
    console.print("\n[dim]Thinking...[/dim]")


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
