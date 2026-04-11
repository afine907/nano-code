"""CLI 主入口测试"""

from unittest.mock import MagicMock, patch

import pytest

from nano_code.cli.main import handle_command, main


class TestHandleCommand:
    """命令处理测试"""

    def test_exit_command(self):
        """exit 命令应该退出程序"""
        memory = MagicMock()

        with pytest.raises(SystemExit) as exc_info:
            handle_command("/exit", memory)
        assert exc_info.value.code == 0

    def test_quit_command(self):
        """quit 命令应该退出程序"""
        memory = MagicMock()

        with pytest.raises(SystemExit) as exc_info:
            handle_command("/quit", memory)
        assert exc_info.value.code == 0

    def test_q_command(self):
        """q 命令应该退出程序"""
        memory = MagicMock()

        with pytest.raises(SystemExit) as exc_info:
            handle_command("/q", memory)
        assert exc_info.value.code == 0

    def test_clear_command(self, capsys):
        """clear 命令应该清空记忆"""
        memory = MagicMock()

        handle_command("/clear", memory)

        memory.clear.assert_called_once()
        captured = capsys.readouterr()
        assert "清空记忆" in captured.out

    def test_help_command(self, capsys):
        """help 命令应该显示帮助"""
        memory = MagicMock()

        handle_command("/help", memory)

        captured = capsys.readouterr()
        assert "命令列表" in captured.out
        assert "/help" in captured.out
        assert "/clear" in captured.out
        assert "/exit" in captured.out

    def test_unknown_command(self, capsys):
        """未知命令应该显示提示"""
        memory = MagicMock()

        handle_command("/unknown", memory)

        captured = capsys.readouterr()
        assert "未知命令" in captured.out

    def test_commands_are_case_insensitive(self, capsys):
        """命令应该不区分大小写"""
        memory = MagicMock()

        handle_command("/CLEAR", memory)

        memory.clear.assert_called_once()

    def test_commands_ignore_whitespace(self, capsys):
        """命令应该忽略空白"""
        memory = MagicMock()

        handle_command("  /clear  ", memory)

        memory.clear.assert_called_once()


class TestMain:
    """主函数测试"""

    @patch("nano_code.cli.main.run_interactive")
    def test_main_calls_run_interactive(self, mock_run):
        """main 应该调用 run_interactive"""
        mock_run.side_effect = SystemExit(0)

        with pytest.raises(SystemExit):
            main()

        mock_run.assert_called_once()

    @patch("nano_code.cli.main.run_interactive")
    def test_main_handles_exception(self, mock_run, capsys):
        """main 应该处理异常"""
        mock_run.side_effect = Exception("Test error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
