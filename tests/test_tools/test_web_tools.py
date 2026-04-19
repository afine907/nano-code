"""Web 搜索工具测试"""

from unittest.mock import MagicMock, patch


def test_web_search_basic():
    """测试 web_search 工具基本功能"""
    from nano_code.tools.web_tools import web_search

    # 使用 patch 模拟 DDGS
    mock_result = [
        {"title": "Example", "href": "https://example.com", "body": "An example."},
        {"title": "Test", "href": "https://test.com", "body": "A test."},
    ]

    with patch("nano_code.tools.web_tools.DDGS") as mock_ddgs:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.text.return_value = iter(mock_result)
        mock_ddgs.return_value = mock_instance

        result = web_search.invoke({"query": "test query", "count": 2})

        assert "Example" in result
        assert "https://example.com" in result


def test_web_search_empty_results():
    """测试空结果"""
    from nano_code.tools.web_tools import web_search

    with patch("nano_code.tools.web_tools.DDGS") as mock_ddgs:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.text.return_value = iter([])
        mock_ddgs.return_value = mock_instance

        result = web_search.invoke({"query": "nonexistent query", "count": 5})
        assert result == ""


def test_web_search_exception_handling():
    """测试异常处理"""
    from nano_code.tools.web_tools import web_search

    with patch("nano_code.tools.web_tools.DDGS") as mock_ddgs:
        mock_ddgs.side_effect = Exception("Network error")

        result = web_search.invoke({"query": "test", "count": 5})
        assert result == ""
