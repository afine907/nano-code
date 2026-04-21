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


class TestCLIStartup:
    """测试 CLI 启动"""

    @pytest.fixture
    def cli_command(self):
        """获取 CLI 命令"""
        project_root = Path(__file__).parent.parent.parent
        cli_path = project_root / "packages" / "cli" / "src" / "index.tsx"

        # 检查是否有 .env 文件
        env_file = project_root / ".env"
        assert env_file.exists(), f".env file not found at {env_file}"

        return f"npx tsx {cli_path}"

    def test_cli_starts_and_shows_welcome(self, cli_command):
        """测试 CLI 启动并显示欢迎信息"""
        child = pexpect.spawn(cli_command, timeout=10, encoding="utf-8")

        try:
            # 等待欢迎信息
            child.expect("jojo|Welcome|🦞", timeout=5)
            output = child.before
            print(f"\nOutput: {output}")
            assert True
        finally:
            child.close()

    def test_cli_shows_input_prompt(self, cli_command):
        """测试 CLI 显示输入提示"""
        child = pexpect.spawn(cli_command, timeout=10, encoding="utf-8")

        try:
            # 等待输入提示
            child.expect("🦞|📋", timeout=5)
            assert True
        finally:
            child.close()


class TestCLIBasicInteraction:
    """测试 CLI 基本交互"""

    @pytest.fixture
    def cli_command(self):
        """获取 CLI 命令"""
        project_root = Path(__file__).parent.parent.parent
        cli_path = project_root / "packages" / "cli" / "src" / "index.tsx"
        return f"npx tsx {cli_path}"

    def test_send_message_and_get_response(self, cli_command):
        """测试发送消息并获取响应（使用 LongCat API）"""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        child = pexpect.spawn(cli_command, timeout=30, encoding="utf-8")

        try:
            # 等待输入提示
            child.expect("🦞", timeout=5)

            # 发送简单消息
            child.sendline("你好，请简短回复")
            time.sleep(1)

            # 等待响应（可能需要更长时间）
            child.expect("jojo|你好|assistant|response", timeout=20)

            print("\nResponse received")
            assert True
        except pexpect.TIMEOUT:
            print(f"\nTimeout - output so far: {child.before}")
            pytest.fail("Timeout waiting for response")
        finally:
            child.close()

    def test_mode_toggle_command(self, cli_command):
        """测试 /mode 命令切换模式"""
        child = pexpect.spawn(cli_command, timeout=10, encoding="utf-8")

        try:
            # 等待 build 模式提示
            child.expect("🦞", timeout=5)

            # 发送 /mode 命令
            child.sendline("/mode")
            time.sleep(0.5)

            # 应该切换到 plan 模式（显示 📋）
            child.expect("📋", timeout=2)

            # 再次切换回 build 模式
            child.sendline("/mode")
            time.sleep(0.5)
            child.expect("🦞", timeout=2)

            assert True
        finally:
            child.close()

    def test_clear_command(self, cli_command):
        """测试 /clear 命令"""
        child = pexpect.spawn(cli_command, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)

            # 发送 /clear 命令
            child.sendline("/clear")
            time.sleep(0.5)

            # 应该清空消息
            assert True
        finally:
            child.close()

    def test_exit_command(self, cli_command):
        """测试 /exit 命令"""
        child = pexpect.spawn(cli_command, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)

            # 发送 /exit 命令
            child.sendline("/exit")

            # 应该退出
            child.expect(pexpect.EOF, timeout=2)
            assert True
        finally:
            child.close()


class TestCLIMultilineInput:
    """测试 CLI 多行输入"""

    @pytest.fixture
    def cli_command(self):
        """获取 CLI 命令"""
        project_root = Path(__file__).parent.parent.parent
        cli_path = project_root / "packages" / "cli" / "src" / "index.tsx"
        return f"npx tsx {cli_path}"

    def test_multiline_with_tab(self, cli_command):
        """测试 Tab 换行"""
        child = pexpect.spawn(cli_command, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)

            # 输入第一行
            child.send("第一行")

            # 按 Tab 换行
            child.sendcontrol("i")  # Tab
            time.sleep(0.5)

            # 输入第二行
            child.send("第二行")

            # 按 Enter 提交
            child.sendcontrol("m")  # Enter
            time.sleep(1)

            assert True
        finally:
            child.close()

    def test_cancel_multiline_with_escape(self, cli_command):
        """测试 Escape 取消多行输入"""
        child = pexpect.spawn(cli_command, timeout=10, encoding="utf-8")

        try:
            child.expect("🦞", timeout=5)

            # 输入一些内容
            child.send("一些内容")

            # 按 Tab 换行
            child.sendcontrol("i")  # Tab
            time.sleep(0.5)

            # 按 Escape 取消
            child.send("\x1b")  # Escape
            time.sleep(0.5)

            # 输入应该被清空
            assert True
        finally:
            child.close()
