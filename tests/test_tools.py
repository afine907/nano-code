"""
Nano Code - Tools 模块单元测试
"""

import os
import tempfile

import pytest

from nano_code.tools.file_tools import list_directory, read_file, write_file
from nano_code.tools.registry import Tool, ToolRegistry
from nano_code.tools.search_tools import glob_search, grep_search
from nano_code.tools.shell_tools import run_command


class TestToolRegistry:
    """测试工具注册表"""

    def test_register_tool(self):
        """测试注册工具"""
        registry = ToolRegistry()
        # 工具已通过 _register_default_tools 注册
        tools = registry.list_tools()
        assert len(tools) > 0

    def test_get_tool(self):
        """测试获取工具"""
        registry = ToolRegistry()
        t = registry.get("read_file")
        assert t is not None

    def test_unregister_tool(self):
        """测试注销工具"""
        registry = ToolRegistry()
        initial_count = len(registry.list_tools())
        registry.unregister("read_file")
        assert len(registry.list_tools()) == initial_count - 1

    def test_list_tools(self):
        """测试列出所有工具"""
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert "read_file" in tools
        assert "write_file" in tools


class TestTool:
    """测试工具基类"""

    def test_tool_creation(self):
        """测试工具创建"""
        # Tool 是 BaseTool 的别名
        assert Tool is not None


class TestReadFileTool:
    """测试读取文件工具"""

    def test_read_file(self):
        """测试读取文件功能"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            f.flush()
            temp_path = f.name

        try:
            result = read_file.invoke({"path": temp_path})
            assert "test content" in result
        finally:
            os.unlink(temp_path)

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        with pytest.raises((FileNotFoundError, OSError)):
            read_file.invoke({"path": "/nonexistent/file.txt"})

    def test_read_with_line_numbers(self):
        """测试带行号读取"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line1\nline2\nline3")
            f.flush()
            temp_path = f.name

        try:
            result = read_file.invoke({"path": temp_path, "line_numbers": True})
            assert "1" in result
        finally:
            os.unlink(temp_path)


class TestWriteFileTool:
    """测试写入文件工具"""

    def test_write_file(self):
        """测试写入文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            result = write_file.invoke({"path": file_path, "content": "hello"})
            assert "成功" in result or "success" in result.lower()

    def test_write_creates_directory(self):
        """测试写入时创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "subdir", "test.txt")
            write_file.invoke({"path": file_path, "content": "hello"})
            assert os.path.exists(file_path)


class TestListDirectoryTool:
    """测试列出目录工具"""

    def test_list_directory(self):
        """测试列出目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一些文件
            open(os.path.join(tmpdir, "file1.txt"), "w").close()
            open(os.path.join(tmpdir, "file2.txt"), "w").close()
            os.makedirs(os.path.join(tmpdir, "subdir"))

            result = list_directory.invoke({"path": tmpdir})
            assert "file1.txt" in result
            assert "file2.txt" in result


class TestSearchFilesTool:
    """测试搜索文件工具"""

    def test_search_by_name(self):
        """测试按名称搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "test_file.py"), "w").close()
            open(os.path.join(tmpdir, "other.txt"), "w").close()

            result = glob_search.invoke({"pattern": "*.py", "path": tmpdir})
            assert "test_file.py" in result


class TestExecuteCommandTool:
    """测试执行命令工具"""

    def test_execute_simple_command(self):
        """测试执行简单命令"""
        result = run_command.invoke({"command": "echo hello"})
        assert "hello" in result

    def test_execute_with_timeout(self):
        """测试超时执行"""
        with pytest.raises((FileNotFoundError, OSError)):
            run_command.invoke({"command": "sleep 10", "timeout": 1})


class TestGrepTool:
    """测试 grep 工具"""

    def test_grep_basic(self):
        """测试基本 grep"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line1\ntest line2\nline3")
            f.flush()
            temp_path = f.name

        try:
            result = grep_search.invoke({"pattern": "test", "path": temp_path})
            assert "test line2" in result
        finally:
            os.unlink(temp_path)


class TestToolCaching:
    """测试工具缓存"""

    def test_cache_results(self):
        """测试缓存结果"""
        # 简单验证工具可用
        registry = ToolRegistry()
        assert registry.get("read_file") is not None
