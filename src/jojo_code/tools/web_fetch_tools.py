"""网页抓取工具"""

from langchain_core.tools import tool


@tool("web_fetch")
def web_fetch(url: str, max_chars: int = 5000) -> str:
    """获取网页内容

    Args:
        url: 网页 URL
        max_chars: 最大字符数

    Returns:
        网页文本内容
    """
    import httpx

    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        content = response.text[:max_chars]
        return f"URL: {url}\n\n内容:\n{content}"
    except Exception as e:
        return f"获取失败: {str(e)}"


@tool("web_scrape")
def web_scrape(url: str, selector: str = "") -> str:
    """抓取网页指定元素

    Args:
        url: 网页 URL
        selector: CSS 选择器

    Returns:
        抓取的内容
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "需要安装 beautifulsoup4: pip install beautifulsoup4"

    import httpx

    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        if selector:
            elements = soup.select(selector)
            return "\n".join(e.get_text(strip=True) for e in elements[:10])

        # 返回标题和主要段落
        title = soup.title.string if soup.title else "无标题"
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs[:5])

        return f"标题: {title}\n\n内容:\n{text[:2000]}"
    except Exception as e:
        return f"抓取失败: {str(e)}"


__all__ = ["web_fetch", "web_scrape"]
