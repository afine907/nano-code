"""文件操作工具 - 读写、编辑、列表目录"""
from pathlib import Path

from langchain_core.tools import tool


@tool
def read_file(path: str, line_numbers: bool = False) -> str:
    """读取指定路径的文件内容。

    Args:
        path: 文件路径
        line_numbers: 是否显示行号，默认 False

    Returns:
        文件内容字符串

    Raises:
        FileNotFoundError: 文件不存在
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    content = file_path.read_text(encoding="utf-8")

    if line_numbers:
        lines = content.splitlines()
        numbered_lines = [f"{i + 1:6}\t{line}" for i, line in enumerate(lines)]
        return "\n".join(numbered_lines)

    return content


@tool
def write_file(path: str, content: str) -> str:
    """写入内容到指定文件，会创建不存在的父目录。

    Args:
        path: 文件路径
        content: 要写入的内容

    Returns:
        操作结果信息
    """
    file_path = Path(path)

    # 创建父目录（如果不存在）
    file_path.parent.mkdir(parents=True, exist_ok=True)

    file_path.write_text(content, encoding="utf-8")
    return f"成功写入文件: {path}"


@tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """编辑文件，替换指定文本（只替换第一次出现）。

    Args:
        path: 文件路径
        old_text: 要替换的文本
        new_text: 新文本

    Returns:
        操作结果信息
    """
    file_path = Path(path)
    if not file_path.exists():
        return f"错误: 文件不存在 {path}"

    content = file_path.read_text(encoding="utf-8")

    if old_text not in content:
        return f"错误: 未找到要替换的文本 '{old_text[:50]}...'"

    # 只替换第一次出现
    new_content = content.replace(old_text, new_text, 1)
    file_path.write_text(new_content, encoding="utf-8")

    return f"成功编辑文件: {path}"


@tool
def list_directory(path: str) -> str:
    """列出目录内容，区分文件和目录。

    Args:
        path: 目录路径

    Returns:
        目录内容列表，[FILE] 表示文件，[DIR] 表示目录

    Raises:
        FileNotFoundError: 目录不存在
    """
    dir_path = Path(path)
    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {path}")

    if not dir_path.is_dir():
        return f"错误: {path} 不是目录"

    items = []
    for item in sorted(dir_path.iterdir()):
        if item.is_dir():
            items.append(f"[DIR]  {item.name}/")
        else:
            items.append(f"[FILE] {item.name}")

    return "\n".join(items) if items else "(空目录)"
