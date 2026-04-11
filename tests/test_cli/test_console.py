"""CLI 控制台输出测试"""

from nano_code.cli.console import (
    format_code,
    print_assistant,
    print_code,
    print_error,
    print_thinking,
    print_tool_call,
    print_tool_result,
    print_user,
    print_welcome,
)


class TestConsoleOutput:
    """控制台输出函数测试"""

    def test_print_welcome(self, capsys):
        """应该打印欢迎信息"""
        print_welcome()
        # Rich 会输出带格式的文本
        captured = capsys.readouterr()
        assert "Nano-Code" in captured.out or len(captured.out) > 0

    def test_print_user(self, capsys):
        """应该打印用户消息"""
        print_user("Hello, world!")
        captured = capsys.readouterr()
        assert "Hello, world!" in captured.out

    def test_print_assistant(self, capsys):
        """应该打印助手消息"""
        print_assistant("This is a response")
        captured = capsys.readouterr()
        assert "Assistant" in captured.out

    def test_print_tool_call(self, capsys):
        """应该打印工具调用信息"""
        print_tool_call("read_file", {"path": "test.py"})
        captured = capsys.readouterr()
        assert "read_file" in captured.out
        assert "path" in captured.out

    def test_print_tool_result(self, capsys):
        """应该打印工具结果"""
        print_tool_result("Success")
        captured = capsys.readouterr()
        assert "Success" in captured.out

    def test_print_tool_result_truncates_long_output(self, capsys):
        """应该截断过长的输出"""
        long_result = "x" * 600
        print_tool_result(long_result)
        captured = capsys.readouterr()
        assert "..." in captured.out

    def test_print_error(self, capsys):
        """应该打印错误信息"""
        print_error("Something went wrong")
        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "Something went wrong" in captured.out

    def test_print_thinking(self, capsys):
        """应该打印思考状态"""
        print_thinking()
        captured = capsys.readouterr()
        assert "Thinking" in captured.out

    def test_format_code(self):
        """应该格式化代码"""
        code = "def hello():\n    print('world')"
        result = format_code(code, language="python")
        # format_code 返回带 ANSI 转义码的格式化代码
        assert len(result) > 0

    def test_print_code(self, capsys):
        """应该打印高亮代码"""
        code = "def hello():\n    print('world')"
        print_code(code, language="python")
        captured = capsys.readouterr()
        assert len(captured.out) > 0
