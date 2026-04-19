"""主题系统测试"""

import tempfile
from pathlib import Path

import pytest

from nano_code.cli.theme import (
    PREDEFINED_THEMES,
    Theme,
    ThemeColors,
    ThemeManager,
    ThemeStyles,
    apply_theme_prompt_format,
    get_current_theme,
    get_theme_manager,
    handle_theme_command,
    list_themes,
    set_theme,
)


class TestThemeDataclass:
    """测试 Theme 数据类"""

    def test_theme_creation(self):
        """测试主题创建"""
        theme = Theme(
            name="test_theme",
            colors=ThemeColors(
                user="green",
                assistant="blue",
                tool="yellow",
                error="red",
                status_bar="cyan",
            ),
            styles=ThemeStyles(
                prompt_prefix="> ",
                prompt_suffix=" ",
                show_icons=True,
                show_status_bar=True,
            ),
        )
        assert theme.name == "test_theme"
        assert theme.colors.user == "green"
        assert theme.colors.assistant == "blue"
        assert theme.styles.show_icons is True

    def test_theme_default_colors(self):
        """测试主题默认颜色"""
        theme = Theme(name="default")
        assert theme.colors.user == "green"
        assert theme.colors.assistant == "blue"
        assert theme.colors.tool == "yellow"
        assert theme.colors.error == "red"
        assert theme.colors.status_bar == "cyan"

    def test_theme_default_styles(self):
        """测试主题默认样式"""
        theme = Theme(name="default")
        assert theme.styles.prompt_prefix == "🦞 "
        assert theme.styles.prompt_suffix == " > "
        assert theme.styles.show_icons is True
        assert theme.styles.show_status_bar is True


class TestPredefinedThemes:
    """测试预定义主题"""

    def test_dark_theme_exists(self):
        """测试 dark 主题存在"""
        assert "dark" in PREDEFINED_THEMES
        theme = PREDEFINED_THEMES["dark"]
        assert theme.name == "dark"
        assert theme.colors.user == "green"
        assert theme.colors.assistant == "bright_blue"

    def test_light_theme_exists(self):
        """测试 light 主题存在"""
        assert "light" in PREDEFINED_THEMES
        theme = PREDEFINED_THEMES["light"]
        assert theme.name == "light"
        assert theme.colors.user == "dark_green"
        assert theme.colors.assistant == "dark_blue"

    def test_monokai_theme_exists(self):
        """测试 monokai 主题存在"""
        assert "monokai" in PREDEFINED_THEMES
        theme = PREDEFINED_THEMES["monokai"]
        assert theme.name == "monokai"
        assert theme.colors.user == "green"
        assert theme.colors.assistant == "magenta"


class TestThemeManager:
    """测试 ThemeManager"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_manager_initialization(self, temp_dir):
        """测试管理器初始化"""
        manager = ThemeManager(themes_dir=temp_dir)
        themes = manager.list_themes()
        assert "dark" in themes
        assert "light" in themes
        assert "monokai" in themes

    def test_get_theme(self, temp_dir):
        """测试获取主题"""
        manager = ThemeManager(themes_dir=temp_dir)
        theme = manager.get_theme("dark")
        assert theme is not None
        assert theme.name == "dark"

    def test_get_nonexistent_theme(self, temp_dir):
        """测试获取不存在的主题"""
        manager = ThemeManager(themes_dir=temp_dir)
        theme = manager.get_theme("nonexistent")
        assert theme is None

    def test_set_theme(self, temp_dir):
        """测试设置主题"""
        manager = ThemeManager(themes_dir=temp_dir)
        result = manager.set_theme("light", persist=False)
        assert result is True
        assert manager.get_current_theme().name == "light"

    def test_set_invalid_theme(self, temp_dir):
        """测试设置无效主题"""
        manager = ThemeManager(themes_dir=temp_dir)
        result = manager.set_theme("invalid_theme")
        assert result is False

    def test_add_custom_theme(self, temp_dir):
        """测试添加自定义主题"""
        manager = ThemeManager(themes_dir=temp_dir)
        custom_theme = Theme(
            name="custom",
            colors=ThemeColors(
                user="white", assistant="white", tool="white", error="white", status_bar="white"
            ),
        )
        manager.add_theme(custom_theme)
        theme = manager.get_theme("custom")
        assert theme is not None
        assert theme.name == "custom"

    def test_remove_custom_theme(self, temp_dir):
        """测试移除自定义主题"""
        manager = ThemeManager(themes_dir=temp_dir)
        custom_theme = Theme(name="custom")
        manager.add_theme(custom_theme)
        result = manager.remove_theme("custom")
        assert result is True
        assert manager.get_theme("custom") is None

    def test_remove_builtin_theme_fails(self, temp_dir):
        """测试移除内置主题失败"""
        manager = ThemeManager(themes_dir=temp_dir)
        result = manager.remove_theme("dark")
        assert result is False

    def test_list_themes(self, temp_dir):
        """测试列出主题"""
        manager = ThemeManager(themes_dir=temp_dir)
        themes = manager.list_themes()
        assert "dark" in themes
        assert "light" in themes
        assert "monokai" in themes


class TestThemeFunctions:
    """测试主题相关函数"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """重置单例"""
        if hasattr(get_theme_manager, "_instance"):
            delattr(get_theme_manager, "_instance")
        yield
        if hasattr(get_theme_manager, "_instance"):
            delattr(get_theme_manager, "_instance")

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_get_theme_manager(self, temp_dir):
        """测试获取主题管理器"""
        manager = get_theme_manager()
        assert manager is not None

    def test_get_current_theme(self, temp_dir):
        """测试获取当前主题"""
        theme = get_current_theme()
        assert theme is not None

    def test_set_theme_function(self, temp_dir):
        """测试 set_theme 函数"""
        result = set_theme("monokai")
        assert result is True
        theme = get_current_theme()
        assert theme.name == "monokai"

    def test_list_themes_function(self, temp_dir):
        """测试 list_themes 函数"""
        themes = list_themes()
        assert isinstance(themes, list)
        assert len(themes) >= 3


class TestThemeColors:
    """测试颜色应用"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """重置单例"""
        if hasattr(get_theme_manager, "_instance"):
            delattr(get_theme_manager, "_instance")
        yield
        if hasattr(get_theme_manager, "_instance"):
            delattr(get_theme_manager, "_instance")

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_user_color(self, temp_dir):
        """测试用户消息颜色"""
        manager = ThemeManager(themes_dir=temp_dir)
        theme = manager.get_theme("dark")
        assert theme.colors.user == "green"

    def test_assistant_color(self, temp_dir):
        """测试 AI 消息颜色"""
        manager = ThemeManager(themes_dir=temp_dir)
        theme = manager.get_theme("dark")
        assert theme.colors.assistant == "bright_blue"

    def test_tool_color(self, temp_dir):
        """测试工具输出颜色"""
        manager = ThemeManager(themes_dir=temp_dir)
        theme = manager.get_theme("dark")
        assert theme.colors.tool == "yellow"

    def test_error_color(self, temp_dir):
        """测试错误颜色"""
        manager = ThemeManager(themes_dir=temp_dir)
        theme = manager.get_theme("dark")
        assert theme.colors.error == "red"

    def test_status_bar_color(self, temp_dir):
        """测试状态栏颜色"""
        manager = ThemeManager(themes_dir=temp_dir)
        theme = manager.get_theme("dark")
        assert theme.colors.status_bar == "cyan"

    def test_color_different_themes(self, temp_dir):
        """测试不同主题的颜色"""
        dark_theme = (
            manager.get_theme("dark") if (manager := ThemeManager(themes_dir=temp_dir)) else None
        )
        light_theme = ThemeManager(themes_dir=temp_dir).get_theme("light")
        monokai_theme = ThemeManager(themes_dir=temp_dir).get_theme("monokai")

        assert dark_theme.colors.assistant != light_theme.colors.assistant
        assert light_theme.colors.assistant != monokai_theme.colors.assistant


class TestApplyTheme:
    """测试主题应用"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """重置单例"""
        if hasattr(get_theme_manager, "_instance"):
            delattr(get_theme_manager, "_instance")
        yield
        if hasattr(get_theme_manager, "_instance"):
            delattr(get_theme_manager, "_instance")

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_apply_theme_prompt_format(self, temp_dir):
        """测试应用主题后的 prompt 格式"""
        ThemeManager(themes_dir=temp_dir)
        result = apply_theme_prompt_format("hello")
        assert "hello" in result

    def test_theme_prompt_format_dark(self, temp_dir):
        """测试 dark 主题的 prompt 格式"""
        manager = ThemeManager(themes_dir=temp_dir)
        manager.set_theme("dark", persist=False)
        result = apply_theme_prompt_format("")
        assert "🦞 " in result
        assert " > " in result

    def test_theme_prompt_format_light(self, temp_dir):
        """测试 light 主题的 prompt 格式"""
        manager = ThemeManager(themes_dir=temp_dir)
        manager.set_theme("light", persist=False)
        result = apply_theme_prompt_format("")
        assert "🦞 " in result
        assert " > " in result


class TestHandleThemeCommand:
    """测试 CLI 主题命令处理"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """重置单例"""
        if hasattr(get_theme_manager, "_instance"):
            delattr(get_theme_manager, "_instance")
        yield
        if hasattr(get_theme_manager, "_instance"):
            delattr(get_theme_manager, "_instance")

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_handle_theme_list(self, temp_dir):
        """测试 /theme list 命令"""
        result = handle_theme_command("list")
        assert "dark" in result
        assert "light" in result
        assert "monokai" in result

    def test_handle_theme_set(self, temp_dir):
        """测试 /theme set 命令"""
        result = handle_theme_command("set light")
        assert "light" in result

    def test_handle_theme_set_invalid(self, temp_dir):
        """测试 /theme set 无效主题"""
        result = handle_theme_command("set nonexistent")
        assert "not found" in result.lower() or "not found" in result

    def test_handle_theme_current(self, temp_dir):
        """测试 /theme current 命令"""
        result = handle_theme_command("current")
        assert "current theme" in result.lower()

    def test_handle_theme_empty_args(self, temp_dir):
        """测试空参数"""
        result = handle_theme_command("")
        assert "dark" in result or "light" in result or "monokai" in result

    def test_handle_theme_unknown_command(self, temp_dir):
        """测试未知命令"""
        result = handle_theme_command("unknown")
        assert "unknown" in result.lower() or "Unknown" in result


class TestConfigPersistence:
    """测试配置持久化"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_save_and_load_config(self, temp_dir):
        """测试保存和加载配置"""
        manager = ThemeManager(themes_dir=temp_dir)
        manager.set_theme("light", persist=True)

        new_manager = ThemeManager(themes_dir=temp_dir)
        assert new_manager.get_current_theme().name == "light"

    def test_load_nonexistent_config(self, temp_dir):
        """测试加载不存在的配置"""
        manager = ThemeManager(themes_dir=temp_dir)
        assert manager.get_current_theme().name in ["dark", "light", "monokai"]
