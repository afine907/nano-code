"""会话 UI 组件

提供会话管理的终端 UI：
- 会话列表显示
- 会话切换选择器
- 会话详情面板
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from nano_code.cli.session_manager import Session

console = Console()


def print_session_list(sessions: list[Session], current_session_id: str | None = None) -> None:
    """打印会话列表

    Args:
        sessions: 会话列表
        current_session_id: 当前会话 ID
    """
    if not sessions:
        console.print("[dim]暂无会话[/dim]")
        return

    table = Table(
        title="📋 会话列表",
        show_header=True,
        header_style="bold",
        box=None,
    )
    table.add_column("状态", width=4, style="cyan")
    table.add_column("名称", style="bold")
    table.add_column("消息数", justify="right", style="dim")
    table.add_column("更新时间", style="dim")

    for session in sessions:
        is_current = session.id == current_session_id
        status = "✓" if is_current else " "
        name = f"[green]{session.name}[/green]" if is_current else session.name
        msg_count = str(session.message_count)
        updated = session.updated_at.strftime("%m-%d %H:%M")

        table.add_row(status, name, msg_count, updated)

    console.print(table)


def print_session_selector(
    sessions: list[Session],
    current_session_id: str | None = None,
    prompt: str = "选择会话",
) -> None:
    """打印会话选择器

    Args:
        sessions: 会话列表
        current_session_id: 当前会话 ID
        prompt: 提示文本
    """
    if not sessions:
        console.print("[dim]暂无会话，输入 /new 创建新会话[/dim]")
        return

    console.print(f"\n[bold]{prompt}:[/bold]")

    for i, session in enumerate(sessions, 1):
        is_current = session.id == current_session_id
        marker = "[green]*[/green]" if is_current else " "
        name = session.name

        console.print(f"  {marker} {i}. {name}")


def print_session_detail(session: Session) -> None:
    """打印会话详情

    Args:
        session: 会话
    """
    title = f"会话: {session.name}"
    content = Text()

    content.append(f"ID: {session.id}\n")
    content.append(f"创建时间: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
    content.append(f"更新时间: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
    content.append(f"消息数: {session.message_count}\n")

    if session.storage_path:
        content.append(f"存储路径: {session.storage_path}\n")

    console.print(Panel(content, title=title, border_style="blue"))


def print_session_switched(session: Session) -> None:
    """打印会话切换成功消息

    Args:
        session: 切换到的会话
    """
    console.print(f"[green]✓[/green] 已切换到会话: [bold]{session.name}[/bold]")


def print_new_session_created(session: Session) -> None:
    """打印新会话创建成功消息

    Args:
        session: 新创建的会话
    """
    console.print(f"[green]✓[/green] 已创建新会话: [bold]{session.name}[/bold]")
    console.print(f"[dim]ID: {session.id}[/dim]")


def print_session_deleted(session_name: str) -> None:
    """打印会话删除成功消息

    Args:
        session_name: 被删除的会话名称
    """
    console.print(f"[green]✓[/green] 已删除会话: [bold]{session_name}[/bold]")


def print_no_sessions_available() -> None:
    """打印无可用会话的消息"""
    console.print("[yellow]⚠️ 没有可用的会话[/yellow]")
    console.print("[dim]输入 /new 创建新会话[/dim]")


def confirm_delete_session(session_name: str) -> bool:
    """确认删除会话

    Args:
        session_name: 会话名称

    Returns:
        是否确认删除
    """
    console.print(f"[bold]确认删除会话 '{session_name}'?[/bold]")
    console.print("[dim]此操作不可撤销，输入 'y' 确认: [/dim]", end="")

    response = input().strip().lower()
    return response == "y"
