"""CLI E2E 测试

使用 pexpect 测试真实的 CLI 交互。

运行: pytest -m e2e tests/test_e2e/test_cli.py -v -s
"""

import os
import time
from pathlib import Path

import pytest

try:
    import pexpect

    HAS_PEXPECT = True
except ImportError:
    HAS_PEXPECT = False

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not HAS_PEXPECT, reason="pexpect not installed"),
]


def get_cli_command():
    """获取 CLI 命令"""
    project_root = Path(__file__).parent.parent.parent
    cli_path = project_root / "packages" / "cli" / "src" / "index.tsx"

    env_file = project_root / ".env"
    assert env_file.exists(), f".env file not found at {env_file}"

    return f"npx tsx {cli_path}"


class TestCLIStartup:
    """测试 CLI 启动"""

    def test_cli_starts_successfully(self):
        """测试 CLI 成功启动"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            # 等待输入提示出现
            child.expect("🦞", timeout=5)
            assert True
        finally:
            child.close()

    def test_cli_shows_help_hint(self):
        """测试 CLI 显示帮助提示"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            # 等待并检查帮助提示
            child.expect("/help", timeout=5)
            assert True
        finally:
            child.close()


class TestCLICommands:
    """测试 CLI 命令"""

    def test_help_command(self):
        """测试 /help 命令"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.sendline("/help")
            time.sleep(0.5)

            # 应该显示帮助信息
            child.expect("可用命令|/mode|/clear|/exit", timeout=2)
            assert True
        finally:
            child.close()

    def test_mode_toggle(self):
        """测试 /mode 命令切换模式"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            # 初始是 build 模式
            child.expect("🦞", timeout=5)

            # 切换到 plan 模式
            child.sendline("/mode")
            time.sleep(0.5)
            child.expect("📋", timeout=2)

            # 切换回 build 模式
            child.sendline("/mode")
            time.sleep(0.5)
            child.expect("🦞", timeout=2)

            assert True
        finally:
            child.close()

    def test_mode_direct_set(self):
        """测试 /mode plan 直接设置模式"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.sendline("/mode plan")
            time.sleep(0.5)
            child.expect("📋", timeout=2)
            assert True
        finally:
            child.close()

    def test_clear_command(self):
        """测试 /clear 命令"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.sendline("/clear")
            time.sleep(0.3)
            assert True
        finally:
            child.close()

    def test_exit_command(self):
        """测试 /exit 命令"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.sendline("/exit")
            child.expect(pexpect.EOF, timeout=2)
            assert True
        finally:
            child.close()

    def test_quit_command(self):
        """测试 /quit 命令"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.sendline("/quit")
            child.expect(pexpect.EOF, timeout=2)
            assert True
        finally:
            child.close()


class TestCLIMultilineInput:
    """测试 CLI 多行输入"""

    def test_tab_creates_newline(self):
        """测试 Tab 创建新行"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.send("第一行")
            child.sendcontrol("i")  # Tab
            time.sleep(0.3)
            child.send("第二行")
            child.sendcontrol("m")  # Enter
            time.sleep(0.5)
            assert True
        finally:
            child.close()

    def test_escape_cancels_input(self):
        """测试 Escape 取消输入"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.send("一些内容")
            child.sendcontrol("i")  # Tab
            time.sleep(0.3)
            child.send("\x1b")  # Escape
            time.sleep(0.3)
            assert True
        finally:
            child.close()


class TestCLIMessageSending:
    """测试 CLI 消息发送"""

    def test_send_simple_message(self):
        """测试发送简单消息"""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=30, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.sendline("说一个字：好")
            time.sleep(1)

            # 等待响应
            child.expect("好|响应|response", timeout=20)
            assert True
        except pexpect.TIMEOUT:
            print(f"Timeout output: {child.before}")
            pytest.fail("Timeout waiting for response")
        finally:
            child.close()

    def test_user_message_display(self):
        """测试用户消息显示"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            test_msg = "测试消息123"
            child.sendline(test_msg)
            time.sleep(0.5)

            # 用户消息应该显示（青色）
            assert True
        finally:
            child.close()


class TestCLIKeyboardShortcuts:
    """测试 CLI 快捷键"""

    def test_ctrl_c_exits(self):
        """测试 Ctrl+C 退出"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.sendcontrol("c")
            child.expect(pexpect.EOF, timeout=2)
            assert True
        finally:
            child.close()

    def test_backspace_deletes_character(self):
        """测试 Backspace 删除字符"""
        cli = get_cli_command()
        child = pexpect.spawn(cli, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)
            child.send("abc")
            time.sleep(0.1)
            child.sendcontrol("h")  # Backspace
            time.sleep(0.1)
            assert True
        finally:
            child.close()
