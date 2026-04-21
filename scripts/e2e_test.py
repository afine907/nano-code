#!/usr/bin/env python3
"""
jojo-code CLI E2E 测试脚本

使用 pexpect 进行交互式 CLI 测试。

安装依赖:
    pip install pexpect

运行:
    python scripts/e2e_test.py

环境变量 (需要设置在 .env 文件中):
    OPENAI_API_KEY: LongCat API Key
    OPENAI_BASE_URL: https://api.longcat.chat/openai/v1
"""

import os
import sys
import time
import signal
from pathlib import Path

try:
    import pexpect
except ImportError:
    print("Error: pexpect not installed. Run: pip install pexpect")
    sys.exit(1)


# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_test(name: str):
    print(f"\n{Colors.BLUE}▶ 测试: {name}{Colors.RESET}")


def print_pass():
    print(f"{Colors.GREEN}✓ 通过{Colors.RESET}")


def print_fail(error: str):
    print(f"{Colors.RED}✗ 失败: {error}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.YELLOW}  {msg}{Colors.RESET}")


class E2ETestRunner:
    """E2E 测试运行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.cli_path = self.project_root / "packages" / "cli" / "src" / "index.tsx"
        self.env_file = self.project_root / ".env"
        self.passed = 0
        self.failed = 0

    def get_cli_command(self) -> str:
        return f"npx tsx {self.cli_path}"

    def check_env(self) -> bool:
        """检查环境配置"""
        if not self.env_file.exists():
            print_fail(f".env 文件不存在: {self.env_file}")
            return False
        
        # 加载 .env
        from dotenv import load_dotenv
        load_dotenv(self.env_file)
        
        if not os.getenv("OPENAI_API_KEY"):
            print_fail("OPENAI_API_KEY 未设置")
            return False
        
        print_pass()
        print_info("环境配置正确")
        return True

    def test_cli_startup(self):
        """测试 CLI 启动"""
        print_test("CLI 启动")
        
        child = pexpect.spawn(self.get_cli_command(), timeout=10, encoding='utf-8')
        
        try:
            child.expect('🦞|jojo|Welcome', timeout=5)
            print_pass()
            print_info(f"输出: {child.before[:100]}...")
            self.passed += 1
        except pexpect.TIMEOUT:
            print_fail("等待欢迎信息超时")
            print_info(f"已输出: {child.before}")
            self.failed += 1
        finally:
            child.close()

    def test_mode_toggle(self):
        """测试模式切换"""
        print_test("模式切换 (/mode)")
        
        child = pexpect.spawn(self.get_cli_command(), timeout=10, encoding='utf-8')
        
        try:
            # 等待 build 模式
            child.expect('🦞', timeout=5)
            print_info("当前: Build 模式")
            
            # 切换到 plan 模式
            child.sendline('/mode')
            time.sleep(0.5)
            child.expect('📋', timeout=2)
            print_info("切换到: Plan 模式")
            
            # 切换回 build 模式
            child.sendline('/mode')
            time.sleep(0.5)
            child.expect('🦞', timeout=2)
            print_info("切换到: Build 模式")
            
            print_pass()
            self.passed += 1
        except pexpect.TIMEOUT as e:
            print_fail(f"超时: {e}")
            self.failed += 1
        finally:
            child.close()

    def test_exit_command(self):
        """测试退出命令"""
        print_test("退出命令 (/exit)")
        
        child = pexpect.spawn(self.get_cli_command(), timeout=10, encoding='utf-8')
        
        try:
            child.expect('🦞', timeout=5)
            child.sendline('/exit')
            child.expect(pexpect.EOF, timeout=2)
            
            print_pass()
            self.passed += 1
        except pexpect.TIMEOUT:
            print_fail("退出超时")
            self.failed += 1
        finally:
            child.close()

    def test_send_message(self):
        """测试发送消息（真实 API）"""
        print_test("发送消息 (LongCat API)")
        
        if not os.getenv("OPENAI_API_KEY"):
            print_info("跳过: OPENAI_API_KEY 未设置")
            return
        
        child = pexpect.spawn(self.get_cli_command(), timeout=60, encoding='utf-8')
        
        try:
            child.expect('🦞', timeout=5)
            
            # 发送简单消息
            child.sendline('你好，请用中文简短回复"测试成功"')
            print_info("已发送消息，等待响应...")
            
            # 等待响应
            child.expect('测试|成功|你好|jojo', timeout=30)
            
            print_pass()
            print_info(f"收到响应")
            self.passed += 1
        except pexpect.TIMEOUT:
            print_fail("等待响应超时")
            print_info(f"已输出: {child.before}")
            self.failed += 1
        finally:
            child.close()

    def test_multiline_input(self):
        """测试多行输入"""
        print_test("多行输入")
        
        child = pexpect.spawn(self.get_cli_command(), timeout=10, encoding='utf-8')
        
        try:
            child.expect('🦞', timeout=5)
            
            # 输入第一行
            child.send('第一行')
            time.sleep(0.2)
            
            # Tab 换行
            child.sendcontrol('i')
            time.sleep(0.5)
            
            # 检查是否进入多行模式
            child.expect('多行|1:', timeout=2)
            print_info("进入多行模式")
            
            print_pass()
            self.passed += 1
        except pexpect.TIMEOUT:
            print_fail("多行输入测试失败")
            self.failed += 1
        finally:
            child.close()

    def test_clear_command(self):
        """测试清空命令"""
        print_test("清空命令 (/clear)")
        
        child = pexpect.spawn(self.get_cli_command(), timeout=10, encoding='utf-8')
        
        try:
            child.expect('🦞', timeout=5)
            child.sendline('/clear')
            time.sleep(0.5)
            
            # 应该还能看到输入提示
            child.expect('🦞', timeout=2)
            
            print_pass()
            self.passed += 1
        except pexpect.TIMEOUT:
            print_fail("清空命令测试失败")
            self.failed += 1
        finally:
            child.close()

    def run_all(self):
        """运行所有测试"""
        print(f"\n{'=' * 50}")
        print(f"{Colors.BLUE}jojo-code CLI E2E 测试{Colors.RESET}")
        print(f"{'=' * 50}")
        
        # 检查环境
        print_test("环境检查")
        if not self.check_env():
            print("\n请先配置 .env 文件")
            return
        
        # 运行测试
        self.test_cli_startup()
        self.test_mode_toggle()
        self.test_exit_command()
        self.test_clear_command()
        self.test_multiline_input()
        self.test_send_message()  # 需要真实 API
        
        # 汇总
        print(f"\n{'=' * 50}")
        print(f"测试结果: {Colors.GREEN}{self.passed} 通过{Colors.RESET}, "
              f"{Colors.RED}{self.failed} 失败{Colors.RESET}")
        print(f"{'=' * 50}\n")


def main():
    runner = E2ETestRunner()
    runner.run_all()
    
    sys.exit(0 if runner.failed == 0 else 1)


if __name__ == "__main__":
    main()
