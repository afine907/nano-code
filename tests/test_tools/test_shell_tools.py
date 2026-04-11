"""Shell 工具测试"""

import pytest

from nano_code.tools.shell_tools import run_command


class TestRunCommand:
    """命令执行测试"""

    def test_run_simple_command(self):
        """应该能执行简单命令"""
        result = run_command.invoke({"command": "echo Hello"})

        assert "Hello" in result

    def test_run_command_with_output(self):
        """应该返回命令输出"""
        result = run_command.invoke({"command": "echo 'test output'"})

        assert "test output" in result

    def test_command_timeout(self):
        """超时命令应该被终止"""
        with pytest.raises(TimeoutError):
            run_command.invoke({"command": "sleep 10", "timeout": 1})

    def test_failed_command_returns_error(self):
        """失败命令应该返回错误信息"""
        result = run_command.invoke({"command": "ls /nonexistent_directory_12345_xyz"})

        assert "error" in result.lower() or "失败" in result

    def test_run_command_in_directory(self, tmp_path):
        """应该能在指定目录执行命令"""
        (tmp_path / "test.txt").write_text("content")

        result = run_command.invoke(
            {
                "command": "ls",
                "cwd": str(tmp_path),
            }
        )

        assert "test.txt" in result

    def test_command_with_special_characters(self):
        """应该能处理特殊字符"""
        result = run_command.invoke({"command": "echo 'hello world'"})

        assert "hello world" in result
