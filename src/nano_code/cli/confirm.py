"""CLI 权限确认交互"""

from collections import OrderedDict
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from nano_code.security.permission import PermissionResult

console = Console()


def format_args(args: dict[str, Any], max_length: int = 50) -> str:
    """格式化参数显示

    Args:
        args: 参数字典
        max_length: 单个值的最大长度

    Returns:
        格式化后的参数字符串
    """
    parts = []
    for key, value in args.items():
        value_str = str(value)
        if len(value_str) > max_length:
            value_str = value_str[: max_length - 3] + "..."
        parts.append(f"{key}=[cyan]{value_str}[/cyan]")
    return ", ".join(parts)


def request_user_confirmation(result: PermissionResult) -> bool:
    """请求用户确认

    Args:
        result: 权限检查结果

    Returns:
        用户是否批准
    """
    # 创建参数表格
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("工具", f"[cyan]{result.tool_name}[/cyan]")
    table.add_row("参数", format_args(result.args))
    if result.reason:
        table.add_row("原因", f"[dim]{result.reason}[/dim]")

    # 显示确认面板
    console.print(
        Panel(
            table,
            title="[bold yellow]⚠️  操作需要确认[/bold yellow]",
            border_style="yellow",
        )
    )

    # 请求用户输入
    while True:
        try:
            response = console.input("\n[bold]允许执行? [Y/n/a(始终允许)]: [/bold]").strip().lower()

            if response in ("y", "yes", ""):
                console.print("[green]✓ 已批准[/green]\n")
                return True
            elif response in ("n", "no"):
                console.print("[red]✗ 已拒绝[/red]\n")
                return False
            elif response == "a":
                # TODO: 实现始终允许的记忆功能
                console.print("[green]✓ 已批准（始终允许）[/green]\n")
                return True
            else:
                console.print("[dim]请输入 Y (允许), N (拒绝) 或 A (始终允许)[/dim]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]✗ 已取消[/red]\n")
            return False


class ApprovalMemory:
    """批准记忆

    记住用户批准过的操作，避免重复确认。
    使用 OrderedDict 实现 FIFO 淘汰策略。
    """

    def __init__(self, max_entries: int = 100):
        """初始化

        Args:
            max_entries: 最大记忆条目数
        """
        self._approved: OrderedDict[tuple[str, str], None] = OrderedDict()
        self._max_entries = max_entries

    def is_approved(self, tool_name: str, pattern: str) -> bool:
        """检查是否已被批准过

        Args:
            tool_name: 工具名称
            pattern: 操作模式（如文件路径、命令前缀）

        Returns:
            是否已被批准
        """
        key = (tool_name, pattern)
        if key in self._approved:
            # 移动到末尾，表示最近使用
            self._approved.move_to_end(key)
            return True
        return False

    def add_approval(self, tool_name: str, pattern: str) -> None:
        """添加批准记录

        Args:
            tool_name: 工具名称
            pattern: 操作模式
        """
        key = (tool_name, pattern)
        # 如果已存在，先删除再添加（移到末尾）
        if key in self._approved:
            del self._approved[key]
        elif len(self._approved) >= self._max_entries:
            # FIFO 淘汰最早的条目
            self._approved.popitem(last=False)

        self._approved[key] = None

    def clear(self) -> None:
        """清空记忆"""
        self._approved.clear()


# 全局批准记忆
_approval_memory = ApprovalMemory()


def get_approval_memory() -> ApprovalMemory:
    """获取全局批准记忆"""
    return _approval_memory


def request_user_confirmation_with_memory(result: PermissionResult) -> bool:
    """带记忆的用户确认

    如果用户之前批准过相同模式的操作，自动批准。

    Args:
        result: 权限检查结果

    Returns:
        用户是否批准
    """
    memory = get_approval_memory()

    # 提取操作模式
    pattern = _extract_pattern(result.tool_name, result.args)

    # 检查是否已被批准
    if pattern and memory.is_approved(result.tool_name, pattern):
        console.print(f"[dim]✓ 自动批准: {result.tool_name}({pattern})[/dim]")
        return True

    # 请求用户确认
    approved = request_user_confirmation(result)

    # 如果用户选择始终允许，记录下来
    if approved and pattern:
        memory.add_approval(result.tool_name, pattern)

    return approved


def _extract_pattern(tool_name: str, args: dict[str, Any]) -> str | None:
    """提取操作模式

    Args:
        tool_name: 工具名称
        args: 工具参数

    Returns:
        操作模式字符串
    """
    if tool_name in ("read_file", "write_file", "edit_file", "list_directory"):
        path = args.get("path", "")
        # 提取目录模式
        if "/" in path:
            return path.rsplit("/", 1)[0] + "/*"
        return path

    if tool_name == "run_command":
        command = args.get("command", "")
        # 提取命令前缀
        parts = command.strip().split()
        if parts:
            return parts[0] + " *"
        return command

    return None
