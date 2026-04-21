"""CLI 主入口测试"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from jojo_code.cli.console import session_stats
from jojo_code.cli.main import handle_command, main


class TestHandleCommand:
    """命令处理测试"""

    def setup_method(self):
        """每个测试前重置统计"""
        session_stats.reset()

    def test_exit_command(self):
        """exit 命令应该返回 False"""
        memory = MagicMock()
        result = handle_command("/exit", memory, "gpt-4")
        assert result is False

    def test_quit_command(self):
        """quit 命令应该返回 False"""
        memory = MagicMock()
        result = handle_command("/quit", memory, "gpt-4")
        assert result is False

    def test_q_command(self):
        """q 命令应该返回 False"""
        memory = MagicMock()
        result = handle_command("/q", memory, "gpt-4")
        assert result is False

    def test_clear_command(self, capsys):
        """clear 命令应该清空记忆"""
        memory = MagicMock()

        result = handle_command("/clear", memory, "gpt-4")

        memory.clear.assert_called_once()
        assert result is True
        captured = capsys.readouterr()
        assert "清空" in captured.out

    def test_help_command(self, capsys):
        """help 命令应该显示帮助"""
        memory = MagicMock()

        result = handle_command("/help", memory, "gpt-4")

        assert result is True
        captured = capsys.readouterr()
        assert "Commands" in captured.out
        assert "/help" in captured.out
        assert "/clear" in captured.out
        assert "/exit" in captured.out
        assert "/stats" in captured.out
        assert "/model" in captured.out
        assert "/history" in captured.out

    def test_stats_command(self, capsys):
        """stats 命令应该显示统计"""
        memory = MagicMock()

        result = handle_command("/stats", memory, "gpt-4")

        assert result is True
        captured = capsys.readouterr()
        assert "Statistics" in captured.out

    def test_model_command(self, capsys):
        """model 命令应该显示模型"""
        memory = MagicMock()

        result = handle_command("/model", memory, "gpt-4o-mini")

        assert result is True
        captured = capsys.readouterr()
        assert "Model" in captured.out
        assert "gpt-4o-mini" in captured.out

    def test_history_command_empty(self, capsys):
        """history 命令显示空历史"""
        memory = MagicMock()
        memory.get_context.return_value = []

        result = handle_command("/history", memory, "gpt-4")

        assert result is True
        captured = capsys.readouterr()
        assert "No messages" in captured.out

    def test_history_command_with_messages(self, capsys):
        """history 命令显示消息历史"""
        memory = MagicMock()
        memory.get_context.return_value = [
            HumanMessage(content="Hello"),
        ]

        result = handle_command("/history", memory, "gpt-4")

        assert result is True
        captured = capsys.readouterr()
        assert "Hello" in captured.out

    def test_reset_stats_command(self, capsys):
        """reset-stats 命令重置统计"""
        memory = MagicMock()
        session_stats.message_count = 10

        result = handle_command("/reset-stats", memory, "gpt-4")

        assert result is True
        assert session_stats.message_count == 0
        captured = capsys.readouterr()
        assert "重置" in captured.out

    def test_unknown_command(self, capsys):
        """未知命令应该显示提示"""
        memory = MagicMock()

        result = handle_command("/unknown", memory, "gpt-4")

        assert result is True
        captured = capsys.readouterr()
        assert "未知命令" in captured.out

    def test_commands_are_case_insensitive(self, capsys):
        """命令应该不区分大小写"""
        memory = MagicMock()

        result = handle_command("/CLEAR", memory, "gpt-4")

        memory.clear.assert_called_once()
        assert result is True

    def test_commands_ignore_whitespace(self, capsys):
        """命令应该忽略空白"""
        memory = MagicMock()

        result = handle_command("  /clear  ", memory, "gpt-4")

        memory.clear.assert_called_once()
        assert result is True


class TestMain:
    """主函数测试"""

    @patch("jojo_code.cli.main.run_interactive")
    def test_main_calls_run_interactive(self, mock_run):
        """main 应该调用 run_interactive"""
        mock_run.side_effect = SystemExit(0)

        with pytest.raises(SystemExit):
            main()

        mock_run.assert_called_once()

    @patch("jojo_code.cli.main.run_interactive")
    def test_main_handles_exception(self, mock_run, capsys):
        """main 应该处理异常"""
        mock_run.side_effect = Exception("Test error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1


class TestGetCurrentModel:
    """获取当前模型测试"""

    @patch("jojo_code.cli.main.get_settings")
    def test_get_current_model(self, mock_settings):
        """应该返回配置的模型"""
        mock_config = MagicMock()
        mock_config.model = "test-model"
        mock_settings.return_value = mock_config

        from jojo_code.cli.main import get_current_model

        result = get_current_model()
        assert result == "test-model"
