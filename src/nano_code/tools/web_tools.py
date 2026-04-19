"""Web 搜索工具

实现一个简单的 Web 搜索接口，基于 duckduckgo-search 包，供 LangChain Tool 使用。
"""

from __future__ import annotations

from duckduckgo_search import DDGS
from langchain_core.tools import tool


@tool
def web_search(query: str, count: int = 5) -> str:
    """使用 DuckDuckGo 进行网页搜索，并返回格式化文本结果。

    Args:
        query: 搜索关键词
        count: 返回结果数量，默认为 5

    Returns:
        一段文本，包含每条结果的标题与链接，以及可选的摘要/片段。
        如果没有结果，返回空字符串。
    """

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=count))
    except Exception:
        # 兜底：任何异常都不阻塞工具的调用，返回空字符串
        return ""

    if not results:
        return ""

    # 格式化结果
    blocks: list[str] = []
    for item in results:
        title = item.get("title", "")
        link = item.get("href", "")
        snippet = item.get("body", "")

        parts: list[str] = []
        if title:
            parts.append(title)
        if link:
            parts.append(link)
        if snippet:
            parts.append(snippet[:200])  # 限制摘要长度

        if parts:
            blocks.append(" - ".join(parts))

    return "\n".join(blocks)
