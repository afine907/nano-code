"""
Nano Code - 命令行增强模块
提供更丰富的 CLI 交互体验
"""

import asyncio
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cmd2 import Cmd

from .core.config import get_settings
from .memory.conversation import ConversationManager


@dataclass
class Command:
    """命令定义"""

    name: str
    description: str
    aliases: list[str]
    handler: Callable


class EnhancedCLI(Cmd):
    """增强版 CLI"""

    # 设置
    Cmd.short_help = "Nano Code CLI"
    Cmd.help_for = "显示帮助"

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.conversation_manager = ConversationManager()
        self.prompt = "🦞 nano-code > "
        self.continuation_prompt = "🦞 ... "

        # 历史记录
        self.history_file = Path.home() / ".nano-code" / "history.json"
        self.load_history()

        # 彩色输出
        self.colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "purple": "\033[95m",
            "reset": "\033[0m",
        }

    def load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []

    def save_history(self):
        """保存历史记录"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w") as f:
            json.dump(self.history[-1000:], f)

    def colored(self, text: str, color: str) -> str:
        """彩色输出"""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    # ==================== 基础命令 ====================

    def do_hello(self, args):
        """测试命令 - hello [name]"""
        name = args.strip() or "World"
        self.poutput(f"👋 你好, {name}!")

    def do_time(self, args):
        """显示当前时间"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.poutput(f"🕐 当前时间: {self.colored(now, 'blue')}")

    def do_whoami(self, args):
        """显示当前用户"""
        import getpass

        self.poutput(f"👤 用户: {getpass.getuser()}")

    def do_pwd(self, args):
        """显示当前目录"""
        self.poutput(f"📁 {os.getcwd()}")

    def do_clear(self, args):
        """清屏"""
        os.system("cls" if os.name == "nt" else "clear")

    # ==================== 对话命令 ====================

    def do_chat(self, args):
        """开始聊天 - chat [message]"""
        if not args.strip():
            self.poutput("用法: chat <消息>")
            return

        self.poutput("🤔 处理中...")

        # 这里调用 AI 处理
        response = f"收到: {args}"

        self.poutput(f"🤖 {response}")

        # 保存到历史
        self.history.append({"role": "user", "content": args})
        self.history.append({"role": "assistant", "content": response})
        self.save_history()

    def do_history(self, args):
        """显示对话历史 - history [数量]"""
        try:
            limit = int(args.strip()) if args.strip() else 10
        except:
            limit = 10

        history = self.history[-limit * 2 :]

        for i, msg in enumerate(history):
            role = "👤" if msg["role"] == "user" else "🤖"
            self.poutput(f"{role} {msg['content'][:50]}...")

    def do_clear_history(self, args):
        """清空对话历史"""
        self.history = []
        self.save_history()
        self.poutput("✅ 历史已清空")

    # ==================== 文件命令 ====================

    def do_ls(self, args):
        """列出文件 - ls [路径]"""
        path = args.strip() or "."

        try:
            files = list(Path(path).iterdir())
            for f in files:
                icon = "📁" if f.is_dir() else "📄"
                color = "blue" if f.is_dir() else "reset"
                self.poutput(f"{icon} {self.colored(f.name, color)}")
        except Exception as e:
            self.poutput(f"❌ 错误: {e}")

    def do_cat(self, args):
        """查看文件 - cat <文件路径>"""
        if not args.strip():
            self.poutput("用法: cat <文件路径>")
            return

        path = Path(args.strip())

        if not path.exists():
            self.poutput(f"❌ 文件不存在: {path}")
            return

        try:
            with open(path) as f:
                content = f.read()
                self.poutput(content[:1000])  # 限制显示
        except Exception as e:
            self.poutput(f"❌ 错误: {e}")

    def do_find(self, args):
        """查找文件 - find <模式>"""
        if not args.strip():
            self.poutput("用法: find <模式>")
            return

        pattern = args.strip()
        matches = list(Path(".").rglob(pattern))[:10]

        if matches:
            for m in matches:
                self.poutput(f"📄 {m}")
        else:
            self.poutput("未找到匹配文件")

    # ==================== Git 命令 ====================

    def do_git_status(self, args):
        """显示 Git 状态"""
        os.system("git status --short")

    def do_git_log(self, args):
        """显示 Git 日志"""
        os.system("git log --oneline -10")

    def do_git_branch(self, args):
        """显示 Git 分支"""
        os.system("git branch -a")

    def do_git_pull(self, args):
        """Git 拉取"""
        os.system("git pull")

    # ==================== 系统命令 ====================

    def do_cpu(self, args):
        """显示 CPU 使用率"""
        import psutil

        cpu = psutil.cpu_percent(interval=1)
        bar = "█" * int(cpu / 5) + "░" * (20 - int(cpu / 5))
        self.poutput(f"CPU: [{bar}] {cpu}%")

    def do_memory(self, args):
        """显示内存使用"""
        import psutil

        mem = psutil.virtual_memory()
        bar = "█" * int(mem.percent / 5) + "░" * (20 - int(mem.percent / 5))
        self.poutput(f"内存: [{bar}] {mem.percent}%")

    def do_disk(self, args):
        """显示磁盘使用"""
        import psutil

        disk = psutil.disk_usage("/")
        bar = "█" * int(disk.percent / 5) + "░" * (20 - int(disk.percent / 5))
        self.poutput(f"磁盘: [{bar}] {disk.percent}%")

    def do_processes(self, args):
        """显示进程列表"""
        import psutil

        procs = sorted(
            psutil.process_iter(["pid", "name", "cpu_percent"]),
            key=lambda p: p.info["cpu_percent"] or 0,
            reverse=True,
        )[:10]

        self.poutput(f"{'PID':<8} {'名称':<20} {'CPU%':<8}")
        self.poutput("-" * 40)
        for p in procs:
            self.poutput(
                f"{p.info['pid']:<8} {p.info['name']:<20} {p.info['cpu_percent'] or 0:.1f}"
            )

    # ==================== 网络命令 ====================

    def do_ping(self, args):
        """Ping 命令 - ping <主机>"""
        if not args.strip():
            self.poutput("用法: ping <主机>")
            return

        host = args.strip()
        os.system(f"ping -c 4 {host}")

    def do_curl(self, args):
        """Curl 命令 - curl <URL>"""
        if not args.strip():
            self.poutput("用法: curl <URL>")
            return

        os.system(f"curl -s {args.strip()}")

    def do_ports(self, args):
        """显示端口使用"""
        import psutil

        self.poutput(f"{'端口':<8} {'进程':<20} {'状态':<10}")
        self.poutput("-" * 50)

        for conn in psutil.net_connections():
            if conn.laddr:
                try:
                    proc = psutil.Process(conn.pid)
                    self.poutput(f"{conn.laddr.port:<8} {proc.name()[:20]:<20} LISTEN")
                except:
                    pass

    # ==================== 开发命令 ====================

    def do_run(self, args):
        """运行脚本 - run <文件>"""
        if not args.strip():
            self.poutput("用法: run <文件>")
            return

        ext = Path(args.strip()).suffix
        interpreters = {".py": "python3", ".js": "node", ".sh": "bash"}

        interpreter = interpreters.get(ext, "python3")
        os.system(f"{interpreter} {args.strip()}")

    def do_test(self, args):
        """运行测试 - test [路径]"""
        path = args.strip() or "tests/"
        os.system(f"pytest {path} -v")

    def do_lint(self, args):
        """代码检查"""
        os.system("ruff check src/")

    def do_format(self, args):
        """代码格式化"""
        os.system("ruff format src/")

    # ==================== 配置命令 ====================

    def do_config(self, args):
        """显示/修改配置 - config [key] [value]"""
        parts = args.strip().split()

        if not parts:
            # 显示所有配置
            for key, value in self.settings.model_dump().items():
                self.poutput(f"{key}: {value}")
        elif len(parts) == 1:
            # 显示单个配置
            key = parts[0]
            value = getattr(self.settings, key, None)
            self.poutput(f"{key}: {value}")
        else:
            # 修改配置
            key, value = parts[0], parts[1]
            setattr(self.settings, key, value)
            self.poutput(f"✅ 已设置 {key} = {value}")

    # ==================== 帮助命令 ====================

    def do_help_all(self, args):
        """显示所有命令"""
        commands = [
            ("hello", "测试命令"),
            ("time", "显示时间"),
            ("chat", "开始聊天"),
            ("history", "查看历史"),
            ("ls", "列出文件"),
            ("cat", "查看文件"),
            ("find", "查找文件"),
            ("git_status", "Git 状态"),
            ("cpu", "CPU 使用率"),
            ("memory", "内存使用"),
            ("disk", "磁盘使用"),
            ("ping", "Ping 测试"),
            ("curl", "HTTP 请求"),
            ("run", "运行脚本"),
            ("test", "运行测试"),
            ("config", "配置管理"),
        ]

        self.poutput("📚 可用命令:")
        for name, desc in commands:
            self.poutput(f"  {name:<15} - {desc}")

    # ==================== 退出命令 ====================

    def do_exit(self, args):
        """退出程序"""
        self.poutput("👋 再见!")
        return True

    def do_quit(self, args):
        """退出程序"""
        return self.do_exit(args)

    # 别名
    def do_q(self, args):
        return self.do_exit(args)


class InteractiveShell:
    """交互式 shell 启动器"""

    def __init__(self):
        self.cli = EnhancedCLI()

    def run(self):
        """运行 CLI"""
        self.cli.cmdloop()


def start_interactive_shell():
    """启动交互式 shell"""
    shell = InteractiveShell()
    shell.run()


# 异步 CLI
class AsyncEnhancedCLI(EnhancedCLI):
    """异步版 CLI"""

    async def do_achat(self, args):
        """异步聊天"""
        if not args.strip():
            return

        self.poutput("🤔 思考中...")

        # 异步处理
        await asyncio.sleep(0.5)  # 模拟

        response = f"收到: {args}"
        self.poutput(f"🤖 {response}")

    async def do_afetch(self, args):
        """异步获取 URL"""
        if not args.strip():
            return

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(args.strip()) as resp:
                    text = await resp.text()
                    self.poutput(text[:500])
        except Exception as e:
            self.poutput(f"❌ 错误: {e}")
