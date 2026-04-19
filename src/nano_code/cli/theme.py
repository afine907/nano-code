"""主题系统

提供终端 UI 主题功能：
- 预设主题
- 自定义主题
- 主题切换
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ColorPalette:
    """调色板"""

    primary: str = "blue"
    secondary: str = "cyan"
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"
    info: str = "dim"
    user: str = "green"
    assistant: str = "blue"
    tool: str = "yellow"
    system: str = "dim"


@dataclass
class ThemeColors:
    """主题颜色方案"""

    user: str = "green"
    assistant: str = "blue"
    tool: str = "yellow"
    error: str = "red"
    status_bar: str = "cyan"


@dataclass
class ThemeStyles:
    """主题样式"""

    prompt_prefix: str = "🦞 "
    prompt_suffix: str = " > "
    continuation_prefix: str = "🦞 "
    continuation_suffix: str = " ... "
    show_icons: bool = True
    show_status_bar: bool = True


@dataclass
class Theme:
    """主题数据类"""

    name: str
    colors: ThemeColors = field(default_factory=ThemeColors)
    styles: ThemeStyles = field(default_factory=ThemeStyles)


@dataclass
class ThemeConfig:
    """主题配置"""

    name: str
    prompt: str = "🦞 nano-code > "
    continuation_prompt: str = "🦞 ... "
    colors: ColorPalette = field(default_factory=ColorPalette)
    show_icons: bool = True
    show_status_bar: bool = True
    code_theme: str = "monokai"


PREDEFINED_THEMES: dict[str, Theme] = {
    "dark": Theme(
        name="dark",
        colors=ThemeColors(
            user="green",
            assistant="bright_blue",
            tool="yellow",
            error="red",
            status_bar="cyan",
        ),
        styles=ThemeStyles(
            prompt_prefix="🦞 ",
            prompt_suffix=" > ",
            continuation_prefix="🦞 ",
            continuation_suffix=" ... ",
            show_icons=True,
            show_status_bar=True,
        ),
    ),
    "light": Theme(
        name="light",
        colors=ThemeColors(
            user="dark_green",
            assistant="dark_blue",
            tool="dark_yellow",
            error="dark_red",
            status_bar="dark_cyan",
        ),
        styles=ThemeStyles(
            prompt_prefix="🦞 ",
            prompt_suffix=" > ",
            continuation_prefix="🦞 ",
            continuation_suffix=" ... ",
            show_icons=True,
            show_status_bar=True,
        ),
    ),
    "monokai": Theme(
        name="monokai",
        colors=ThemeColors(
            user="green",
            assistant="magenta",
            tool="yellow",
            error="red",
            status_bar="bright_red",
        ),
        styles=ThemeStyles(
            prompt_prefix="🦞 ",
            prompt_suffix=" > ",
            continuation_prefix="🦞 ",
            continuation_suffix=" ... ",
            show_icons=True,
            show_status_bar=True,
        ),
    ),
}

BUILTIN_THEMES: dict[str, ThemeConfig] = {
    "default": ThemeConfig(
        name="default",
        prompt="🦞 nano-code > ",
        continuation_prompt="🦞 ... ",
        colors=ColorPalette(),
        show_icons=True,
        show_status_bar=True,
        code_theme="monokai",
    ),
    "minimal": ThemeConfig(
        name="minimal",
        prompt="> ",
        continuation_prompt="... ",
        colors=ColorPalette(
            primary="white",
            secondary="white",
            success="white",
            warning="white",
            error="white",
            info="dim",
            user="white",
            assistant="white",
            tool="white",
            system="dim",
        ),
        show_icons=False,
        show_status_bar=False,
        code_theme="monokai",
    ),
    "ocean": ThemeConfig(
        name="ocean",
        prompt="🌊 nano-code > ",
        continuation_prompt="🌊 ... ",
        colors=ColorPalette(
            primary="blue",
            secondary="cyan",
            success="cyan",
            warning="yellow",
            error="red",
            info="blue",
            user="cyan",
            assistant="blue",
            tool="yellow",
            system="dim",
        ),
        show_icons=True,
        show_status_bar=True,
        code_theme="monokai",
    ),
    "sunset": ThemeConfig(
        name="sunset",
        prompt="🌅 nano-code > ",
        continuation_prompt="🌅 ... ",
        colors=ColorPalette(
            primary="yellow",
            secondary="red",
            success="green",
            warning="yellow",
            error="red",
            info="dim",
            user="yellow",
            assistant="red",
            tool="yellow",
            system="dim",
        ),
        show_icons=True,
        show_status_bar=True,
        code_theme="monokai",
    ),
    "hacker": ThemeConfig(
        name="hacker",
        prompt=">>> ",
        continuation_prompt="... ",
        colors=ColorPalette(
            primary="green",
            secondary="green",
            success="green",
            warning="yellow",
            error="red",
            info="green",
            user="green",
            assistant="green",
            tool="yellow",
            system="dim",
        ),
        show_icons=False,
        show_status_bar=True,
        code_theme="monokai",
    ),
}


class ThemeManager:
    """主题管理器"""

    def __init__(self, themes_dir: Path | None = None) -> None:
        """初始化主题管理器

        Args:
            themes_dir: 主题目录
        """
        self.themes_dir = themes_dir or Path.home() / ".nano-code" / "themes"
        self.themes_dir.mkdir(parents=True, exist_ok=True)

        self._themes: dict[str, Theme] = PREDEFINED_THEMES.copy()
        self._current_theme: Theme = PREDEFINED_THEMES["dark"]
        self._config_file = self.themes_dir.parent / "config.toml"

        self._load_config()

    def _load_config(self) -> None:
        """加载配置"""
        if not self._config_file.exists():
            if "dark" in self._themes:
                self._current_theme = self._themes["dark"]
            return

        try:
            with open(self._config_file, "rb") as f:
                config = tomllib.load(f)

            theme_name = config.get("theme", {}).get("current", "dark")
            if theme_name not in self._themes:
                theme_name = "dark"
            self._current_theme = self._themes[theme_name]
        except Exception:
            if "dark" in self._themes:
                self._current_theme = self._themes["dark"]

    def _save_config(self) -> None:
        """保存配置"""
        config_content = f'[theme]\ncurrent = "{self._current_theme.name}"\n'

        with open(self._config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

    def get_theme(self, name: str) -> Theme | None:
        """获取主题

        Args:
            name: 主题名称

        Returns:
            主题配置，如果不存在则返回 None
        """
        return self._themes.get(name)

    def set_theme(self, name: str, persist: bool = True) -> bool:
        """设置当前主题

        Args:
            name: 主题名称
            persist: 是否保存配置

        Returns:
            是否设置成功
        """
        if name not in self._themes:
            return False

        self._current_theme = self._themes[name]

        if persist:
            self._save_config()

        return True

    def get_current_theme(self) -> Theme:
        """获取当前主题

        Returns:
            当前主题配置
        """
        return self._current_theme

    def list_themes(self) -> list[str]:
        """列出所有主题

        Returns:
            主题名称列表
        """
        return list(self._themes.keys())

    def add_theme(self, theme: Theme) -> None:
        """添加自定义主题

        Args:
            theme: 主题配置
        """
        self._themes[theme.name] = theme

    def remove_theme(self, name: str) -> bool:
        """移除自定义主题（内置主题无法移除）

        Args:
            name: 主题名称

        Returns:
            是否移除成功
        """
        if name in PREDEFINED_THEMES:
            return False

        if name in self._themes:
            del self._themes[name]
            return True

        return False


def get_theme_manager() -> ThemeManager:
    """获取主题管理器单例

    Returns:
        主题管理器
    """
    if not hasattr(get_theme_manager, "_instance"):
        get_theme_manager._instance = ThemeManager()

    return get_theme_manager._instance


def get_current_theme() -> Theme:
    """获取当前主题

    Returns:
        当前主题配置
    """
    return get_theme_manager().get_current_theme()


def set_theme(name: str) -> bool:
    """设置当前主题

    Args:
        name: 主题名称

    Returns:
        是否设置成功
    """
    return get_theme_manager().set_theme(name)


def list_themes() -> list[str]:
    """列出所有主题

    Returns:
        主题名称列表
    """
    return get_theme_manager().list_themes()


def apply_theme_prompt_format(prompt: str) -> str:
    """应用主题后的 prompt

    Args:
        prompt: 原始 prompt

    Returns:
        应用主题后的 prompt
    """
    theme = get_current_theme()
    prefix = theme.styles.prompt_prefix
    suffix = theme.styles.prompt_suffix
    return f"{prefix}{prompt}{suffix}"


def apply_theme_to_console() -> None:
    """将主题应用到控制台"""
    get_current_theme()


def handle_theme_command(args: str) -> str:
    """处理主题命令

    Args:
        args: 命令参数

    Returns:
        输出信息
    """
    parts = args.strip().split()
    if not parts:
        return handle_theme_command("list")

    subcommand = parts[0]

    if subcommand == "list":
        themes = list_themes()
        return f"Available themes: {', '.join(themes)}"

    elif subcommand == "set":
        if len(parts) < 2:
            return "Usage: /theme set <name>"
        name = parts[1]
        if set_theme(name):
            return f"Theme set to: {name}"
        return f"Theme not found: {name}"

    elif subcommand == "current":
        theme = get_current_theme()
        return f"Current theme: {theme.name}"

    else:
        return f"Unknown command: {subcommand}. Use list, set, or current."
