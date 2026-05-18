"""文档操作工具"""

from pathlib import Path
from typing import Any

from langchain_core.tools import tool


@tool("read_pdf")
def read_pdf(path: str, pages: str = "all") -> str:
    """读取 PDF 文件

    Args:
        path: PDF 文件路径
        pages: 页码范围，如 "1-10" 或 "all"

    Returns:
        PDF 文本内容
    """
    try:
        import pypdf
    except ImportError:
        return "需要安装 pypdf: pip install pypdf"

    try:
        reader = pypdf.PdfReader(path)
        num_pages = len(reader.pages)

        if pages == "all":
            page_range = range(num_pages)
        elif "-" in pages:
            start, end = map(int, pages.split("-"))
            page_range = range(start - 1, min(end, num_pages))
        else:
            page_range = [int(pages) - 1]

        text = []
        for i in page_range:
            if 0 <= i < num_pages:
                text.append(reader.pages[i].extract_text())

        return f"共 {num_pages} 页\n\n" + "\n---".join(text)
    except Exception as e:
        return f"读取失败: {str(e)}"


@tool("extract_code")
def extract_code(path: str, language: str = "") -> dict[str, Any]:
    """从文档中提取代码块

    Args:
        path: 文件路径
        language: 编程语言过滤

    Returns:
        提取的代码块列表
    """

    path = Path(path)
    if not path.exists():
        return {"error": "文件不存在"}

    content = path.read_text(encoding="utf-8", errors="ignore")

    # 简单的代码块提取（支持 Markdown）
    import re

    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)

    blocks = []
    for lang, code in matches:
        if language and lang != language:
            continue
        blocks.append({"language": lang or "text", "code": code.strip()})

    return {
        "file": str(path),
        "blocks_count": len(blocks),
        "blocks": blocks[:20],  # 限制数量
    }


@tool("count_lines")
def count_lines(path: str, pattern: str = "") -> dict[str, Any]:
    """统计文件行数

    Args:
        path: 文件或目录路径
        pattern: 文件过滤模式

    Returns:
        行数统计
    """
    import re

    path = Path(path)
    total = 0
    files = {}

    if path.is_file():
        content = path.read_text(encoding="utf-8", errors="ignore")
        lines = len(content.splitlines())
        return {"files": {str(path): lines}, "total": lines}

    # 目录
    for f in path.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            if pattern and not re.search(pattern, f.name):
                continue
            try:
                lines = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
                files[str(f)] = lines
                total += lines
            except Exception:
                pass

    return {"files": files, "total": total}


__all__ = ["read_pdf", "extract_code", "count_lines"]
