"""CLI 快捷键系统测试"""

import pytest

from nano_code.cli.keybindings import (
    KeyBinding,
    KeyBindingGroup,
    KeyBindingManager,
    format_keybinding,
    get_keybindings,
    is_matching,
)


class TestKeyBinding:
    """测试 KeyBinding 数据类"""

    def test_basic_creation(self):
        """测试基本创建"""
        binding = KeyBinding("ctrl+c", "Interrupt")
        assert binding.keys == "ctrl+c"
        assert binding.description == "Interrupt"
        assert binding.handler is None
        assert binding.category == "general"
        assert binding.hidden is False

    def test_full_creation(self):
        """测试完整创建"""

        def dummy_handler():
            pass

        binding = KeyBinding(
            keys="ctrl+d",
            description="Exit",
            handler=dummy_handler,
            category="quit",
            hidden=True,
        )
        assert binding.keys == "ctrl+d"
        assert binding.description == "Exit"
        assert binding.handler is dummy_handler
        assert binding.category == "quit"
        assert binding.hidden is True

    def test_default_values(self):
        """测试默认值"""
        binding = KeyBinding("ctrl+x", "Cut")
        assert binding.category == "general"
        assert binding.hidden is False


class TestKeyBindingGroup:
    """测试 KeyBindingGroup 数据类"""

    def test_basic_creation(self):
        """测试基本创建"""
        group = KeyBindingGroup(
            name="Test",
            description="Test group",
        )
        assert group.name == "Test"
        assert group.description == "Test group"
        assert group.bindings == []

    def test_with_bindings(self):
        """测试带绑定"""
        bindings = [
            KeyBinding("ctrl+a", "Select all"),
            KeyBinding("ctrl+c", "Copy"),
        ]
        group = KeyBindingGroup(
            name="Edit",
            description="Edit commands",
            bindings=bindings,
        )
        assert len(group.bindings) == 2


class TestKeyBindingManager:
    """测试 KeyBindingManager 类"""

    @pytest.fixture
    def manager(self):
        """创建 KeyBindingManager 实例"""
        return KeyBindingManager()

    def test_default_initialization(self, manager):
        """测试默认初始化"""
        assert len(manager._bindings) > 0
        assert len(manager._groups) > 0

    def test_register_binding(self, manager):
        """测试注册快捷键"""
        initial_count = len(manager._bindings)
        binding = KeyBinding("ctrl+test", "Test action")
        manager.register(binding)
        assert len(manager._bindings) == initial_count + 1

    def test_register_duplicate(self, manager):
        """测试重复注册"""
        binding1 = KeyBinding("ctrl+t", "Test 1")
        binding2 = KeyBinding("ctrl+t", "Test 2")
        manager.register(binding1)
        manager.register(binding2)
        assert manager.get("ctrl+t").description == "Test 2"

    def test_unregister_binding(self, manager):
        """测试注销快捷键"""
        manager.unregister("ctrl+d")
        assert manager.get("ctrl+d") is None

    def test_unregister_nonexistent(self, manager):
        """测试注销不存在的快捷键"""
        initial_count = len(manager._bindings)
        manager.unregister("nonexistent")
        assert len(manager._bindings) == initial_count

    def test_get_existing_binding(self, manager):
        """测试获取存在的绑定"""
        binding = manager.get("ctrl+c")
        assert binding is not None
        assert binding.keys == "ctrl+c"

    def test_get_nonexistent_binding(self, manager):
        """测试获取不存在的绑定"""
        assert manager.get("nonexistent") is None

    def test_get_bindings_all(self, manager):
        """测试获取所有绑定"""
        bindings = manager.get_bindings()
        assert len(bindings) > 0

    def test_get_bindings_by_category(self, manager):
        """测试按分类获取绑定"""
        bindings = manager.get_bindings(category="general")
        assert all(b.category == "general" for b in bindings)

    def test_get_groups(self, manager):
        """测试获取分组"""
        groups = manager.get_groups()
        assert len(groups) > 0


class TestRequiredKeybindings:
    """测试需求的快捷键列表"""

    @pytest.fixture
    def manager(self):
        """创建 KeyBindingManager 实例"""
        return KeyBindingManager()

    def test_ctrl_c_interrupt(self, manager):
        """测试 Ctrl+C 中断操作"""
        binding = manager.get("ctrl+c")
        assert binding is not None
        assert "interrupt" in binding.description.lower()

    def test_ctrl_d_exit(self, manager):
        """测试 Ctrl+D 退出"""
        binding = manager.get("ctrl+d")
        assert binding is not None
        assert "exit" in binding.description.lower()

    def test_ctrl_l_clear_screen(self, manager):
        """测试 Ctrl+L 清屏"""
        binding = manager.get("ctrl+l")
        assert binding is not None
        assert "clear" in binding.description.lower()

    def test_ctrl_r_reset_session(self, manager):
        """测试 Ctrl+R 重置会话"""
        binding = manager.get("ctrl+r")
        assert binding is not None
        assert "reset" in binding.description.lower()

    def test_f1_show_help(self, manager):
        """测试 F1 显示帮助"""
        binding = manager.get("f1")
        assert binding is not None
        assert "help" in binding.description.lower()

    def test_f2_toggle_mode(self, manager):
        """测试 F2 切换模式"""
        binding = manager.get("f2")
        assert binding is not None
        assert "mode" in binding.description.lower()

    def test_f3_toggle_layout(self, manager):
        """测试 F3 切换布局"""
        binding = manager.get("f3")
        assert binding is not None
        assert "layout" in binding.description.lower()

    def test_tab_complete(self, manager):
        """测试 Tab 换行/补全"""
        binding = manager.get("tab")
        assert binding is not None

    def test_ctrl_s_save_session(self, manager):
        """测试 Ctrl+S 保存会话"""
        binding = manager.get("ctrl+s")
        assert binding is not None
        assert "save" in binding.description.lower()

    def test_question_mark_help(self, manager):
        """测试 ? 显示帮助"""
        binding = manager.get("?")
        assert binding is not None
        assert "help" in binding.description.lower()


class TestFormatKeybinding:
    """测试 format_keybinding 函数"""

    def test_format_ctrl(self):
        """测试 Ctrl 格式化"""
        assert format_keybinding("ctrl+c") == "^c"

    def test_format_shift(self):
        """测试 Shift 格式化"""
        result = format_keybinding("ctrl+shift+d")
        assert "Shift+" in result

    def test_format_alt(self):
        """测试 Alt 格式化"""
        result = format_keybinding("alt+f1")
        assert "Alt+" in result

    def test_format_normal_key(self):
        """测试普通键"""
        assert format_keybinding("enter") == "enter"

    def test_format_case_insensitive(self):
        """测试大小写不敏感"""
        assert format_keybinding("CTRL+C") == "^c"


class TestIsMatching:
    """测试 is_matching 函数"""

    def test_exact_match(self):
        """测试精确匹配"""
        assert is_matching("ctrl+c", "ctrl+c") is True

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        assert is_matching("CTRL+C", "ctrl+c") is True
        assert is_matching("ctrl+c", "CTRL+C") is True

    def test_no_match(self):
        """测试不匹配"""
        assert is_matching("ctrl+d", "ctrl+c") is False


class TestGetKeybindings:
    """测试 get_keybindings 函数"""

    def test_returns_manager(self):
        """测试返回管理器"""
        manager = get_keybindings()
        assert isinstance(manager, KeyBindingManager)

    def test_singleton(self):
        """测试单例"""
        manager1 = get_keybindings()
        manager2 = get_keybindings()
        assert manager1 is manager2
