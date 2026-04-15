"""
Nano Code - Tools 模块单元测试
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from nano_code.tools.file_tools import (
    ListDirectoryTool,
    ReadFileTool,
    SearchFilesTool,
    WriteFileTool,
)
from nano_code.tools.registry import Tool, ToolRegistry, tool
from nano_code.tools.search_tools import GrepTool, WebSearchTool
from nano_code.tools.shell_tools import ExecuteCommandTool, RunScriptTool


class TestToolRegistry:
    """测试工具注册表"""

    def test_register_tool(self):
        """测试注册工具"""
        registry = ToolRegistry()
        tool = Tool(name="test", description="A test tool")
        registry.register(tool)
        assert "test" in registry.tools

    def test_get_tool(self):
        """测试获取工具"""
        registry = ToolRegistry()
        tool = Tool(name="test", description="A test tool")
        registry.register(tool)

        retrieved = registry.get("test")
        assert retrieved.name == "test"

    def test_unregister_tool(self):
        """测试注销工具"""
        registry = ToolRegistry()
        tool = Tool(name="test", description="A test tool")
        registry.register(tool)
        registry.unregister("test")
        assert "test" not in registry.tools

    def test_list_tools(self):
        """测试列出工具"""
        registry = ToolRegistry()
        registry.register(Tool(name="tool1", description="Tool 1"))
        registry.register(Tool(name="tool2", description="Tool 2"))

        tools = registry.list_tools()
        assert len(tools) == 2

    def test_search_tools(self):
        """测试搜索工具"""
        registry = ToolRegistry()
        registry.register(Tool(name="read_file", description="Read a file"))
        registry.register(Tool(name="write_file", description="Write a file"))

        results = registry.search("read")
        assert len(results) == 1
        assert results[0].name == "read_file"


class TestTool:
    """测试工具基类"""

    def test_tool_creation(self):
        """测试创建工具"""
        tool = Tool(name="test", description="A test tool")
        assert tool.name == "test"
        assert tool.description == "A test tool"

    def test_tool_decorator(self):
        """测试装饰器"""

        @tool(name="decorated", description="A decorated tool")
        def my_func():
            pass

        assert my_func.tool_name == "decorated"


class TestReadFileTool:
    """测试读取文件工具"""

    def test_read_file(self):
        """测试读取文件"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            tool = ReadFileTool()
            result = tool.execute(path=temp_path)
            assert result == "test content"
        finally:
            os.unlink(temp_path)

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        tool = ReadFileTool()
        with pytest.raises(FileNotFoundError):
            tool.execute(path="/nonexistent/file.txt")

    def test_read_with_encoding(self):
        """测试指定编码读取"""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write("中文内容")
            temp_path = f.name

        try:
            tool = ReadFileTool()
            result = tool.execute(path=temp_path, encoding="utf-8")
            assert result == "中文内容"
        finally:
            os.unlink(temp_path)

    def test_read_binary_file(self):
        """测试读取二进制文件"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
            f.write(b"\x00\x01\x02\x03")
            temp_path = f.name

        try:
            tool = ReadFileTool()
            with pytest.raises(Exception):
                tool.execute(path=temp_path)
        finally:
            os.unlink(temp_path)


class TestWriteFileTool:
    """测试写入文件工具"""

    def test_write_file(self):
        """测试写入文件"""
        tool = WriteFileTool()
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "test.txt")

        try:
            tool.execute(path=temp_path, content="test content")
            with open(temp_path) as f:
                assert f.read() == "test content"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            os.rmdir(temp_dir)

    def test_write_creates_directory(self):
        """测试写入时创建目录"""
        tool = WriteFileTool()
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "subdir", "test.txt")

        try:
            tool.execute(path=temp_path, content="test")
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(os.path.dirname(temp_path)):
                os.rmdir(os.path.dirname(temp_path))
            os.rmdir(temp_dir)

    def test_write_overwrite(self):
        """测试覆盖写入"""
        tool = WriteFileTool()
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("old content")
            temp_path = f.name

        try:
            tool.execute(path=temp_path, content="new content", overwrite=True)
            with open(temp_path) as f:
                assert f.read() == "new content"
        finally:
            os.unlink(temp_path)

    def test_write_without_overwrite(self):
        """测试不覆盖写入"""
        tool = WriteFileTool()
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("existing")
            temp_path = f.name

        try:
            tool.execute(path=temp_path, content="new", overwrite=False)
            # 应该保留原内容
            with open(temp_path) as f:
                assert f.read() == "existing"
        finally:
            os.unlink(temp_path)


class TestListDirectoryTool:
    """测试列目录工具"""

    def test_list_directory(self):
        """测试列目录"""
        tool = ListDirectoryTool()
        temp_dir = tempfile.mkdtemp()

        try:
            # 创建一些测试文件
            open(os.path.join(temp_dir, "file1.txt"), "w").close()
            open(os.path.join(temp_dir, "file2.txt"), "w").close()

            result = tool.execute(path=temp_dir)
            assert len(result) >= 2
        finally:
            os.rmdir(temp_dir)

    def test_list_with_filter(self):
        """测试过滤列目录"""
        tool = ListDirectoryTool()
        temp_dir = tempfile.mkdtemp()

        try:
            open(os.path.join(temp_dir, "test.txt"), "w").close()
            open(os.path.join(temp_dir, "test.py"), "w").close()

            result = tool.execute(path=temp_dir, pattern="*.txt")
            assert len(result) == 1
        finally:
            os.rmdir(temp_dir)

    def test_list_recursive(self):
        """测试递归列目录"""
        tool = ListDirectoryTool()
        temp_dir = tempfile.mkdtemp()

        try:
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)
            open(os.path.join(temp_dir, "file1.txt"), "w").close()
            open(os.path.join(subdir, "file2.txt"), "w").close()

            result = tool.execute(path=temp_dir, recursive=True)
            assert len(result) == 2
        finally:
            import shutil

            shutil.rmtree(temp_dir)


class TestSearchFilesTool:
    """测试搜索文件工具"""

    def test_search_by_name(self):
        """测试按名称搜索"""
        tool = SearchFilesTool()
        temp_dir = tempfile.mkdtemp()

        try:
            open(os.path.join(temp_dir, "test_file.txt"), "w").close()
            open(os.path.join(temp_dir, "other.txt"), "w").close()

            result = tool.execute(path=temp_dir, name_pattern="test*")
            assert len(result) == 1
        finally:
            import shutil

            shutil.rmtree(temp_dir)


class TestExecuteCommandTool:
    """测试执行命令工具"""

    def test_execute_simple_command(self):
        """测试执行简单命令"""
        tool = ExecuteCommandTool()
        result = tool.execute(command="echo hello")
        assert result.strip() == "hello"

    def test_execute_with_env(self):
        """测试带环境变量执行"""
        tool = ExecuteCommandTool()
        result = tool.execute(command="echo $TEST_VAR", env={"TEST_VAR": "test_value"})
        assert "test_value" in result

    def test_execute_with_timeout(self):
        """测试超时执行"""
        tool = ExecuteCommandTool()
        with pytest.raises(Exception):
            tool.execute(command="sleep 10", timeout=1)

    def test_execute_with_cwd(self):
        """测试指定工作目录"""
        tool = ExecuteCommandTool()
        result = tool.execute(command="pwd", cwd="/tmp")
        assert "/tmp" in result or "tmp" in result.lower()

    def test_execute_shell(self):
        """测试执行 shell 命令"""
        tool = ExecuteCommandTool()
        result = tool.execute(command="ls -la | head -5")
        assert result is not None


class TestRunScriptTool:
    """测试运行脚本工具"""

    def test_run_python_script(self):
        """测试运行 Python 脚本"""
        tool = RunScriptTool()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("print('hello from script')")
            script_path = f.name

        try:
            result = tool.execute(script_path=script_path, interpreter="python3")
            assert "hello from script" in result
        finally:
            os.unlink(script_path)

    def test_run_with_args(self):
        """测试带参数运行"""
        tool = RunScriptTool()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("import sys; print(sys.argv[1])")
            script_path = f.name

        try:
            result = tool.execute(script_path=script_path, args=["test_arg"])
            assert "test_arg" in result
        finally:
            os.unlink(script_path)


class TestWebSearchTool:
    """测试网络搜索工具"""

    @pytest.mark.asyncio
    async def test_search(self):
        """测试搜索"""
        tool = WebSearchTool()

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"results": [{"title": "Test Result", "url": "http://test.com"}]}
            )
            mock_session.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            results = await tool.search("test query")
            assert len(results) > 0


class TestGrepTool:
    """测试 grep 工具"""

    def test_grep_basic(self):
        """测试基本 grep"""
        tool = GrepTool()
        temp_dir = tempfile.mkdtemp()

        try:
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("line 1: hello\nline 2: world\nline 3: hello again")

            results = tool.execute(pattern="hello", path=temp_dir)
            assert len(results) == 2
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_grep_regex(self):
        """测试正则 grep"""
        tool = GrepTool()
        temp_dir = tempfile.mkdtemp()

        try:
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("email: test@example.com\nphone: 1234567890")

            results = tool.execute(pattern=r"[\w.-]+@[\w.-]+", path=temp_dir, regex=True)
            assert "test@example.com" in results[0]
        finally:
            import shutil

            shutil.rmtree(temp_dir)


class TestToolCaching:
    """测试工具缓存"""

    def test_cache_results(self):
        """测试缓存结果"""
        tool = ReadFileTool()
        tool.enable_cache = True

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("cached content")
            temp_path = f.name

        try:
            # 第一次读取
            result1 = tool.execute(path=temp_path)
            # 第二次读取应该从缓存
            result2 = tool.execute(path=temp_path)
            assert result1 == result2
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
