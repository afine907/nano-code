"""CLI 文件 Diff 预览模块

提供文件差异预览功能：
- 统一 diff 格式解析
- 行级别差异高亮
- 上下文展示
- 简洁摘要统计
"""

from dataclasses import dataclass
from typing import Literal

from rich.console import Console
from rich.syntax import Syntax


@dataclass
class DiffLine:
    """Diff 行"""

    type: Literal["context", "added", "removed", "header"]
    content: str
    old_line_num: int | None = None
    new_line_num: int | None = None


@dataclass
class DiffFile:
    """Diff 文件"""

    old_path: str
    new_path: str
    lines: list[DiffLine]
    additions: int = 0
    deletions: int = 0


@dataclass
class DiffStats:
    """Diff 统计"""

    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


def parse_unified_diff(diff_text: str) -> list[DiffFile]:
    """解析 unified diff 格式

    Args:
        diff_text: diff 文本

    Returns:
        DiffFile 列表
    """
    files: list[DiffFile] = []
    current_file: DiffFile | None = None
    lines: list[DiffLine] = []
    old_line = 0
    new_line = 0
    old_path = ""
    new_path = ""

    for line in diff_text.splitlines():
        if line.startswith("+++ b/") or line.startswith("+++ "):
            new_path = line[6:] or ""
        elif line.startswith("--- a/") or line.startswith("--- "):
            old_path = line[6:] or ""
        elif line.startswith("@@"):
            if current_file:
                current_file.lines = lines
                files.append(current_file)

            lines = []
            old_line, new_line = _parse_hunk_header(line)
            lines.append(
                DiffLine(
                    type="header",
                    content=line,
                    old_line_num=old_line,
                    new_line_num=new_line,
                )
            )
            current_file = DiffFile(old_path, new_path, lines)
        elif line.startswith("+"):
            lines.append(
                DiffLine(
                    type="added",
                    content=line[1:],
                    new_line_num=new_line,
                )
            )
            new_line += 1
            if current_file:
                current_file.additions += 1
        elif line.startswith("-"):
            lines.append(
                DiffLine(
                    type="removed",
                    content=line[1:],
                    old_line_num=old_line,
                )
            )
            old_line += 1
            if current_file:
                current_file.deletions += 1
        elif line.startswith(" ") or line.startswith("\n"):
            pass
        elif line.startswith("\\"):
            pass
        else:
            lines.append(
                DiffLine(
                    type="context",
                    content=line,
                    old_line_num=old_line,
                    new_line_num=new_line,
                )
            )
            old_line += 1
            new_line += 1

    if current_file:
        current_file.lines = lines
        files.append(current_file)

    return files


def _parse_hunk_header(header: str) -> tuple[int, int]:
    """解析 hunk 头

    Args:
        header: hunk 头（如 @@ -1,5 +1,6 @@）

    Returns:
        (旧行号, 新行号)
    """
    parts = header.split()
    if len(parts) >= 2:
        old = parts[1].lstrip("-")
        new = parts[2].lstrip("+")
        old_num = int(old.split(",")[0])
        new_num = int(new.split(",")[0])
        return old_num, new_num
    return 1, 1


def compute_diff_stats(diff_text: str) -> DiffStats:
    """计算 diff 统计

    Args:
        diff_text: diff 文本

    Returns:
        DiffStats 实例
    """
    stats = DiffStats()
    additions = 0
    deletions = 0

    for line in diff_text.splitlines():
        if line.startswith("+++"):
            stats.files_changed += 1
        elif line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1

    stats.insertions = additions
    stats.deletions = deletions
    return stats


class DiffPreview:
    """Diff 预览渲染器"""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render(self, diff_text: str, context: int = 3) -> str:
        """渲染 diff

        Args:
            diff_text: diff 文本
            context: 上下文行数

        Returns:
            渲染后的字符串
        """
        files = parse_unified_diff(diff_text)
        if not files:
            return diff_text

        output_lines: list[str] = []
        stats = compute_diff_stats(diff_text)
        output_lines.append(
            f"[dim]Files: {stats.files_changed}, +{stats.insertions} / -{stats.deletions}[/dim]"
        )

        for file in files:
            output_lines.append(f"\n[bold]{file.new_path or file.old_path}[/bold]")
            output_lines.append(f"[dim]+{file.additions} / -{file.deletions}[/dim]")

            for line in file.lines:  # 修复：使用当前文件的行，而非 files[0]
                prefix = self._get_line_prefix(line.type)
                num_str = self._format_line_nums(line)
                output_lines.append(f"{prefix} {num_str} {line.content}")

        return "\n".join(output_lines)

    def _get_line_prefix(self, line_type: str) -> str:
        """获取行前缀"""
        if line_type == "added":
            return "[green]+[/green]"
        elif line_type == "removed":
            return "[red]-[/red]"
        elif line_type == "header":
            return "[yellow]@@[/yellow]"
        return " "

    def _format_line_nums(self, line: DiffLine) -> str:
        """格式化行号"""
        old = line.old_line_num
        new = line.new_line_num
        if old is not None and new is not None:
            return f"{old:4d} {new:4d}"
        elif new is not None:
            return f"     {new:4d}"
        elif old is not None:
            return f"{old:4d}"
        return "        "

    def render_side_by_side(
        self,
        old_content: str,
        new_content: str,
        context: int = 3,
    ) -> str:
        """渲染并排diff

        Args:
            old_content: 旧内容
            new_content: 新内容
            context: 上下文行数

        Returns:
            渲染后的字符串
        """
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        output: list[str] = []
        output.append("[bold]Old[/bold]                    [bold]New[/bold]")
        output.append("-" * 40 + "  " + "-" * 40)

        max_lines = max(len(old_lines), len(new_lines))
        for i in range(min(max_lines, 50)):
            old = old_lines[i] if i < len(old_lines) else ""
            new = new_lines[i] if i < len(new_lines) else ""

            old_prefix = "[red]-[/red]" if old and (not new or old != new) else " "
            new_prefix = "[green]+[/green]" if new and (not old or old != new) else " "

            old_display = old[:40] if old else ""
            new_display = new[:40] if new else ""

            output.append(f"{old_prefix} {old_display:40}  {new_prefix} {new_display}")

        return "\n".join(output)


def render_diff_summary(diff_text: str) -> str:
    """渲染 diff 摘要

    Args:
        diff_text: diff 文本

    Returns:
        摘要字符串
    """
    stats = compute_diff_stats(diff_text)
    files = parse_unified_diff(diff_text)

    parts = [f"[bold]Changed:[/bold] {stats.files_changed} files"]

    if stats.insertions > 0:
        parts.append(f"[green]+{stats.insertions}[/green]")
    if stats.deletions > 0:
        parts.append(f"[red]-{stats.deletions}[/red]")

    if files:
        paths = [f.new_path or f.old_path for f in files]
        parts.append(f"[dim]({', '.join(paths[:3])})[/dim]")

    return " | ".join(parts)


def highlight_syntax(code: str, language: str = "python") -> Syntax:
    """语法高亮

    Args:
        code: 代码
        language: 语言

    Returns:
        Syntax 对象
    """
    return Syntax(code, language, theme="monokai", line_numbers=True)


def create_inline_diff(old: str, new: str) -> list[dict]:
    """创建行内diff

    Args:
        old: 旧内容
        new: 新内容

    Returns:
        diff 列表
    """
    diff: list[dict] = []
    old_lines = old.splitlines()
    new_lines = new.splitlines()

    max_len = max(len(old_lines), len(new_lines))
    for i in range(max_len):
        old_line = old_lines[i] if i < len(old_lines) else None
        new_line = new_lines[i] if i < len(new_lines) else None

        if old_line == new_line:
            diff.append({"type": "unchanged", "content": new_line})
        elif old_line is None:
            diff.append({"type": "added", "content": new_line})
        elif new_line is None:
            diff.append({"type": "removed", "content": old_line})
        else:
            diff.append({"type": "removed", "content": old_line})
            diff.append({"type": "added", "content": new_line})

    return diff


def generate_diff(
    old_content: str,
    new_content: str,
    old_path: str = "a",
    new_path: str = "b",
) -> str:
    """生成 unified diff 格式的 diff

    Args:
        old_content: 旧文件内容
        new_content: 新文件内容
        old_path: 旧文件路径
        new_path: 新文件路径

    Returns:
        unified diff 格式字符串
    """
    import difflib

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    if not old_lines and not new_lines:
        return ""

    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_path,
            tofile=new_path,
            lineterm="",
        )
    )

    if not diff:
        return ""

    return "\n".join(diff) + "\n"


def format_diff(
    diff_text: str,
    max_lines: int = 100,
    show_line_numbers: bool = True,
    colorize: bool = True,
) -> str:
    """格式化 diff 文本用于显示

    Args:
        diff_text: diff 文本
        max_lines: 最大显示行数
        show_line_numbers: 是否显示行号
        colorize: 是否着色

    Returns:
        格式化后的字符串
    """
    if not diff_text.strip():
        return "[dim]No changes[/dim]"

    lines = diff_text.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    else:
        truncated = False

    output_lines: list[str] = []
    for line in lines:
        if show_line_numbers and line.startswith("@@"):
            if colorize:
                output_lines.append(f"[yellow]{line}[/yellow]")
            else:
                output_lines.append(line)
        elif line.startswith("+") and not line.startswith("+++"):
            if colorize:
                output_lines.append(f"[green]{line}[/green]")
            else:
                output_lines.append(line)
        elif line.startswith("-") and not line.startswith("---"):
            if colorize:
                output_lines.append(f"[red]{line}[/red]")
            else:
                output_lines.append(line)
        elif line.startswith("---") or line.startswith("+++"):
            if colorize:
                output_lines.append(f"[blue]{line}[/blue]")
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)

    if truncated:
        output_lines.append(
            f"[dim]... ({len(diff_text.splitlines()) - max_lines} more lines)[/dim]"
        )

    stats = compute_diff_stats(diff_text)
    header = f"[bold]Diff:[/bold] +{stats.insertions}/-{stats.deletions}"
    return header + "\n" + "\n".join(output_lines)
