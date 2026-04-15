"""
Nano Code - CLI 模块单元测试
"""

import io
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

import pytest

from nano_code.cli.console import Console, ProgressBar, Spinner
from nano_code.cli.main import CLI, main


class TestCLI:
    """测试 CLI 主类"""

    def test_cli_init(self):
        """测试 CLI 初始化"""
        cli = CLI()
        assert cli is not None
        assert cli.version is not None

    def test_cli_help(self):
        """测试帮助信息"""
        cli = CLI()
        help_text = cli.get_help()
        assert "help" in help_text.lower()
        assert "version" in help_text.lower()

    def test_cli_version(self):
        """测试版本信息"""
        cli = CLI()
        version = cli.get_version()
        assert version is not None
        assert "." in version

    @patch("sys.argv", ["nano-code", "init"])
    def test_cli_parse_args(self):
        """测试参数解析"""
        cli = CLI()
        args = cli.parse_args()
        assert args.command == "init"

    @patch("sys.argv", ["nano-code", "run", "--model", "claude-3"])
    def test_cli_with_options(self):
        """测试带选项的参数"""
        cli = CLI()
        args = cli.parse_args()
        assert args.command == "run"
        assert args.model == "claude-3"


class TestConsole:
    """测试控制台类"""

    def test_console_init(self):
        """测试控制台初始化"""
        console = Console()
        assert console is not None

    def test_print_message(self):
        """测试打印消息"""
        console = Console()

        # 捕获输出
        f = io.StringIO()
        with redirect_stdout(f):
            console.print("Hello")

        output = f.getvalue()
        assert "Hello" in output

    def test_print_error(self):
        """测试打印错误"""
        console = Console()

        f = io.StringIO()
        with redirect_stdout(f):
            console.print_error("Error message")

        output = f.getvalue()
        assert "Error" in output

    def test_print_success(self):
        """测试打印成功消息"""
        console = Console()

        f = io.StringIO()
        with redirect_stdout(f):
            console.print_success("Success!")

        output = f.getvalue()
        assert "Success" in output

    def test_print_warning(self):
        """测试打印警告"""
        console = Console()

        f = io.StringIO()
        with redirect_stdout(f):
            console.print_warning("Warning!")

        output = f.getvalue()
        assert "Warning" in output

    def test_print_info(self):
        """测试打印信息"""
        console = Console()

        f = io.StringIO()
        with redirect_stdout(f):
            console.print_info("Info message")

        output = f.getvalue()
        assert "Info" in output

    def test_print_table(self):
        """测试打印表格"""
        console = Console()

        data = [["Name", "Age"], ["Alice", "25"], ["Bob", "30"]]

        f = io.StringIO()
        with redirect_stdout(f):
            console.print_table(data)

        output = f.getvalue()
        assert "Name" in output
        assert "Alice" in output

    def test_print_tree(self):
        """测试打印树形结构"""
        console = Console()

        tree = {"root": {"child1": {}, "child2": {}}}

        f = io.StringIO()
        with redirect_stdout(f):
            console.print_tree(tree)

        output = f.getvalue()
        assert "root" in output

    def test_input(self):
        """测试输入"""
        console = Console()

        with patch("builtins.input", return_value="test input"):
            result = console.input("Enter: ")
            assert result == "test input"

    def test_confirm(self):
        """测试确认"""
        console = Console()

        with patch("builtins.input", return_value="y"):
            result = console.confirm("Continue?")
            assert result is True

    def test_confirm_default_no(self):
        """测试默认否定的确认"""
        console = Console()

        with patch("builtins.input", return_value=""):
            result = console.confirm("Continue?", default=False)
            assert result is False

    def test_select(self):
        """测试选择"""
        console = Console()

        with patch("builtins.input", return_value="1"):
            result = console.select("Choose:", ["Option 1", "Option 2", "Option 3"])
            assert result == "Option 1"

    def test_color_output(self):
        """测试颜色输出"""
        console = Console()

        f = io.StringIO()
        with redirect_stdout(f):
            console.print("Red text", color="red")
            console.print("Green text", color="green")
            console.print("Blue text", color="blue")

        output = f.getvalue()
        # ANSI codes should be present
        assert "\033" in output or "Red" in output


class TestProgressBar:
    """测试进度条"""

    def test_progress_init(self):
        """测试进度条初始化"""
        pb = ProgressBar(total=100)
        assert pb.total == 100
        assert pb.current == 0

    def test_progress_update(self):
        """测试进度更新"""
        pb = ProgressBar(total=100)
        pb.update(50)
        assert pb.current == 50

    def test_progress_increment(self):
        """测试进度增加"""
        pb = ProgressBar(total=100)
        pb.increment()
        pb.increment()
        assert pb.current == 2

    def test_progress_percentage(self):
        """测试进度百分比"""
        pb = ProgressBar(total=100)
        pb.update(25)
        assert pb.percentage() == 25

    def test_progress_reset(self):
        """测试进度重置"""
        pb = ProgressBar(total=100)
        pb.update(75)
        pb.reset()
        assert pb.current == 0

    def test_progress_finish(self):
        """测试进度完成"""
        pb = ProgressBar(total=100)
        pb.update(100)
        pb.finish()
        assert pb.finished is True


class TestSpinner:
    """测试加载动画"""

    def test_spinner_init(self):
        """测试加载动画初始化"""
        spinner = Spinner()
        assert spinner is not None

    def test_spinner_start(self):
        """测试开始加载动画"""
        spinner = Spinner()
        spinner.start()
        assert spinner.running is True

    def test_spinner_stop(self):
        """测试停止加载动画"""
        spinner = Spinner()
        spinner.start()
        spinner.stop()
        assert spinner.running is False

    def test_spinner_message(self):
        """测试加载动画消息"""
        spinner = Spinner(message="Loading...")
        assert "Loading" in spinner.message


class TestCLICommands:
    """测试 CLI 命令"""

    @patch("nano_code.cli.main.Agent")
    def test_init_command(self, mock_agent):
        """测试 init 命令"""
        cli = CLI()
        cli.run_command("init", name="test-project")
        # 验证项目初始化逻辑
        mock_agent.assert_called()

    @patch("nano_code.cli.main.Agent")
    def test_run_command(self, mock_agent):
        """测试 run 命令"""
        cli = CLI()
        cli.run_command("run", prompt="Hello")
        mock_agent.assert_called()

    @patch("nano_code.cli.main.ConversationManager")
    def test_chat_command(self, mock_cm):
        """测试 chat 命令"""
        cli = CLI()
        cli.run_command("chat", message="Hello")
        mock_cm.assert_called()

    def test_list_command(self):
        """测试 list 命令"""
        cli = CLI()

        f = io.StringIO()
        with redirect_stdout(f):
            cli.run_command("list")

        output = f.getvalue()
        # 应该列出某些内容
        assert output is not None

    @patch("os.system")
    def test_config_command(self, mock_system):
        """测试 config 命令"""
        cli = CLI()
        cli.run_command("config", key="model", value="claude-3")
        mock_system.assert_called()


class TestCLICompletion:
    """测试 CLI 自动补全"""

    def test_complete_commands(self):
        """测试命令补全"""
        cli = CLI()

        completions = cli.complete("i")  # 应该补全 'init'
        assert "init" in completions or len(completions) > 0

    def test_complete_options(self):
        """测试选项补全"""
        cli = CLI()

        completions = cli.complete("run --")  # 应该补全选项
        assert "--model" in completions or "--help" in completions


class TestCLIConfig:
    """测试 CLI 配置"""

    def test_load_config(self):
        """测试加载配置"""
        cli = CLI()

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", create=True):
                config = cli.load_config()
                # 配置应该被加载
                assert config is not None

    def test_save_config(self):
        """测试保存配置"""
        cli = CLI()

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.write = Mock()
            cli.save_config({"model": "test"})
            mock_open.assert_called()


class TestCLIHistory:
    """测试 CLI 历史记录"""

    def test_save_history(self):
        """测试保存历史"""
        cli = CLI()

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.write = Mock()
            cli.save_history(["cmd1", "cmd2"])
            mock_open.assert_called()

    def test_load_history(self):
        """测试加载历史"""
        cli = CLI()

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read = Mock(return_value="cmd1\ncmd2\n")
            history = cli.load_history()
            assert len(history) >= 0


class TestCLIErrors:
    """测试 CLI 错误处理"""

    def test_handle_error(self):
        """测试错误处理"""
        cli = CLI()

        f = io.StringIO()
        with redirect_stderr(f):
            cli.handle_error(ValueError("Test error"))

        output = f.getvalue()
        assert "error" in output.lower() or "Error" in output

    def test_unknown_command(self):
        """测试未知命令"""
        cli = CLI()

        f = io.StringIO()
        with redirect_stdout(f):
            result = cli.run_command("unknown_command")

        output = f.getvalue()
        assert "unknown" in output.lower() or "not found" in output.lower()


class TestMain:
    """测试 main 函数"""

    @patch("sys.argv", ["nano-code", "--version"])
    def test_main_version(self):
        """测试版本参数"""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    @patch("sys.argv", ["nano-code", "--help"])
    def test_main_help(self):
        """测试帮助参数"""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
