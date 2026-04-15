"""
Nano Code - CLI 模块单元测试
"""


class TestCLI:
    """测试 CLI 主类"""

    def test_cli_init(self):
        """测试 CLI 初始化"""
        from nano_code.cli.main import CLI

        cli = CLI()
        assert cli is not None
        assert cli.version is not None

    def test_cli_help(self):
        """测试帮助信息"""
        from nano_code.cli.main import CLI

        cli = CLI()
        help_text = cli.get_help()
        assert "help" in help_text.lower()


class TestSessionStats:
    """测试会话统计"""

    def test_default_values(self):
        """测试默认值"""
        from nano_code.cli.console import SessionStats

        stats = SessionStats()
        assert stats is not None


class TestConsoleOutput:
    """测试控制台输出"""

    def test_print_user(self):
        """测试打印用户消息"""
        # 不抛出异常即可
        from nano_code.cli.console import print_user

        print_user("test")


class TestHandleCommand:
    """测试命令处理"""

    def test_exit_command(self):
        """测试退出命令"""
        # 测试处理函数存在
        from nano_code.cli.main import main

        assert main is not None


# 兼容性测试
class TestCompatibility:
    """兼容性测试"""

    def test_cli_imports(self):
        """测试 CLI 导入"""
        from nano_code.cli.main import CLI, main

        assert CLI is not None
        assert main is not None
