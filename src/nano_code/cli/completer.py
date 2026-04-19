"""智能补全

提供 prompt_toolkit 自动补全功能：
- 命令补全
- 文件路径补全
- 历史记录补全
- 工具名称补全
"""

from collections.abc import Callable
from pathlib import Path

from prompt_toolkit.completion import Completion
from prompt_toolkit.completion.base import Completer

from nano_code.cli.session_manager import SessionManager
from nano_code.tools.registry import ToolRegistry

CLI_COMMANDS = [
    "/help",
    "/exit",
    "/clear",
    "/reset",
    "/stats",
    "/session",
    "/mode",
]


class CommandCompleter(Completer):
    """命令补全"""

    def __init__(self, commands: list[str] | None = None, fuzzy: bool = True) -> None:
        """初始化命令补全

        Args:
            commands: 命令列表（默认使用 CLI_COMMANDS）
            fuzzy: 启用模糊匹配
        """
        self.commands = commands or CLI_COMMANDS
        self.fuzzy = fuzzy

    def get_completions(self, document, complete_event):
        """获取补全项"""
        text = document.text_before_cursor.lower()

        for cmd in self.commands:
            if self._matches(cmd, text):
                yield Completion(
                    cmd,
                    start_position=-len(document.text_before_cursor),
                    display=cmd,
                )

    def _matches(self, cmd: str, text: str) -> bool:
        """检查命令是否匹配"""
        if text.startswith(cmd):
            return True
        if self.fuzzy:
            return self._fuzzy_match(cmd, text)
        return cmd.startswith(text)

    def _fuzzy_match(self, cmd: str, text: str) -> bool:
        """模糊匹配：检查 text 中的字符是否按顺序出现在 cmd 中"""
        cmd_lower = cmd.lower()
        text_lower = text.lower()
        cmd_idx = 0
        for char in text_lower:
            if char in cmd_lower[cmd_idx:]:
                cmd_idx = cmd_lower.index(char, cmd_idx) + 1
            else:
                return False
        return True


class FilePathCompleter(Completer):
    """文件路径补全"""

    def __init__(self, root_path: str = ".", fuzzy: bool = True) -> None:
        """初始化路径补全

        Args:
            root_path: 根路径
            fuzzy: 启用模糊匹配
        """
        self.root_path = Path(root_path)
        self.fuzzy = fuzzy

    def get_completions(self, document, complete_event):
        """获取补全项"""
        text = document.text_before_cursor

        if " " in text:
            return

        if text.startswith("./") or text.startswith("@"):
            text = text[2:]

        path = Path(text)
        if path.is_dir():
            base = path
            prefix = ""
        else:
            base = path.parent
            prefix = path.name

        if not base.exists():
            return

        try:
            for item in base.iterdir():
                name = item.name
                if prefix and not self._matches(name, prefix):
                    continue
                if not prefix:
                    continue

                if item.is_dir():
                    display = f"{name}/"
                    completion = f"{name}/"
                else:
                    display = name
                    completion = name

                yield Completion(
                    completion,
                    start_position=-len(prefix),
                    display=display,
                )
        except PermissionError:
            pass

    def _matches(self, name: str, prefix: str) -> bool:
        """检查文件名是否匹配"""
        name_lower = name.lower()
        prefix_lower = prefix.lower()
        if not prefix_lower:
            return True
        if name_lower.startswith(prefix_lower):
            return True
        if self.fuzzy:
            return self._fuzzy_match(name, prefix)
        return False

    def _fuzzy_match(self, name: str, prefix: str) -> bool:
        """模糊匹配"""
        name_lower = name.lower()
        prefix_lower = prefix.lower()
        name_idx = 0
        for char in prefix_lower:
            if char in name_lower[name_idx:]:
                name_idx = name_lower.index(char, name_idx) + 1
            else:
                return False
        return True


class HistoryCompleter(Completer):
    """历史记录补全"""

    def __init__(
        self,
        get_history_callback: Callable[[], list[str]] | None = None,
        fuzzy: bool = True,
    ) -> None:
        """初始化历史补全

        Args:
            get_history_callback: 获取历史记录的回调函数
            fuzzy: 启用模糊匹配
        """
        self.get_history = get_history_callback or (lambda: [])
        self.fuzzy = fuzzy

    def get_completions(self, document, complete_event):
        """获取补全项"""
        text = document.text_before_cursor.lower()

        if not text.startswith("/"):
            return

        text = text[1:]
        history = self.get_history()

        for item in history:
            if self._matches(item, text):
                yield Completion(
                    f"/{item}",
                    start_position=-len(document.text_before_cursor),
                    display=item,
                )

    def _matches(self, item: str, text: str) -> bool:
        """检查历史记录是否匹配"""
        item_lower = item.lower()
        if item_lower.startswith(text):
            return True
        if self.fuzzy:
            return self._fuzzy_match(item, text)
        return False

    def _fuzzy_match(self, item: str, text: str) -> bool:
        """模糊匹配"""
        item_lower = item.lower()
        text_lower = text.lower()
        item_idx = 0
        for char in text_lower:
            if char in item_lower[item_idx:]:
                item_idx = item_lower.index(char, item_idx) + 1
            else:
                return False
        return True


class ToolNameCompleter(Completer):
    """工具名称补全"""

    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        """初始化工具补全

        Args:
            tool_registry: 工具注册表
        """
        self.tool_registry = tool_registry or ToolRegistry()

    def get_completions(self, document, complete_event):
        """获取补全项"""
        text = document.text_before_cursor.lower()

        if not text.startswith("@"):
            return

        tool_name = text[1:].strip()
        tools = self.tool_registry.list_tools()

        for tool in tools:
            if tool_name in tool.lower():
                yield Completion(
                    f"@{tool}",
                    start_position=-len(tool_name),
                    display=tool,
                )


class MultiCompleter(Completer):
    """组合多个补全器"""

    def __init__(self, completers: list[Completer]) -> None:
        """初始化组合补全器

        Args:
            completers: 补全器列表
        """
        self.completers = completers

    def get_completions(self, document, complete_event):
        """获取补全项"""
        for completer in self.completers:
            yield from completer.get_completions(document, complete_event)


class SessionCompleter(Completer):
    """会话补全"""

    def __init__(self, session_manager: SessionManager | None = None) -> None:
        """初始化会话补全

        Args:
            session_manager: 会话管理器
        """
        self.session_manager = session_manager or SessionManager()

    def get_completions(self, document, complete_event):
        """获取补全项"""
        text = document.text_before_cursor.lower()

        if not text.startswith("#"):
            return

        session_id = text[1:].strip()
        sessions = self.session_manager.list_sessions()

        for session in sessions:
            if session_id in session.id or session_id in session.name.lower():
                yield Completion(
                    f"#{session.id}",
                    start_position=-len(session_id),
                    display=f"{session.id} - {session.name}",
                )


def create_completer(
    session_manager: SessionManager | None = None,
    tool_registry: ToolRegistry | None = None,
    get_history_callback: Callable[[], list[str]] | None = None,
) -> MultiCompleter:
    """创建组合补全器

    Args:
        session_manager: 会话管理器
        tool_registry: 工具注册表
        get_history_callback: 获取历史记录的回调函数

    Returns:
        组合补全器
    """
    completers = [
        CommandCompleter(),
        FilePathCompleter(),
    ]

    if session_manager:
        completers.append(SessionCompleter(session_manager))

    if tool_registry:
        completers.append(ToolNameCompleter(tool_registry))

    if get_history_callback:
        completers.append(HistoryCompleter(get_history_callback))

    return MultiCompleter(completers)


class PathCompleter(FilePathCompleter):
    """路径补全（FilePathCompleter 的别名）"""


class NanoCompleter(Completer):
    """Nano CLI 智能补全器

    根据输入前缀自动选择合适的补全器：
    - `/` 开头: 命令补全
    - `@` 或 `./` 开头: 路径补全
    - 历史记录补全

    支持模糊匹配。
    """

    def __init__(
        self,
        commands: list[str] | None = None,
        session_manager: SessionManager | None = None,
        tool_registry: ToolRegistry | None = None,
        get_history_callback: Callable[[], list[str]] | None = None,
        fuzzy: bool = True,
    ) -> None:
        """初始化 NanoCompleter

        Args:
            commands: 命令列表
            session_manager: 会话管理器
            tool_registry: 工具注册表
            get_history_callback: 获取历史记录的回调函数
            fuzzy: 启用模糊匹配
        """
        self.command_completer = CommandCompleter(commands, fuzzy)
        self.path_completer = PathCompleter(".", fuzzy)
        self.history_completer = HistoryCompleter(get_history_callback, fuzzy)
        self.session_completer = SessionCompleter(session_manager)
        self.tool_completer = ToolNameCompleter(tool_registry)

    def get_completions(self, document, complete_event):
        """获取补全项"""
        text = document.text_before_cursor

        if not text:
            yield from self._get_all_commands()
            return

        if text.startswith("/"):
            yield from self.command_completer.get_completions(document, complete_event)
            if self.history_completer:
                yield from self.history_completer.get_completions(document, complete_event)

        elif text.startswith("@") or text.startswith("./"):
            yield from self.path_completer.get_completions(document, complete_event)

        elif text.startswith("#"):
            yield from self.session_completer.get_completions(document, complete_event)

        else:
            yield from self._get_fuzzy_matches(text)

    def _get_all_commands(self):
        """获取所有命令"""
        for cmd in CLI_COMMANDS:
            yield Completion(
                cmd,
                start_position=0,
                display=cmd,
            )

    def _get_fuzzy_matches(self, text: str):
        """获取模糊匹配结果"""
        text_lower = text.lower()

        for cmd in CLI_COMMANDS:
            if cmd.startswith(text_lower):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                )
