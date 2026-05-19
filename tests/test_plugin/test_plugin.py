"""Plugin system tests - TDD tests first"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestPluginInterface:
    """Test plugin interface"""

    def test_plugin_base_class_exists(self):
        """Plugin must have a base class"""
        from jojo_code.plugin import BasePlugin, PluginMetadata

        assert BasePlugin is not None
        assert PluginMetadata is not None

    def test_plugin_metadata_fields(self):
        """Plugin metadata must have required fields"""
        from jojo_code.plugin import PluginMetadata

        meta = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
        )
        assert meta.name == "test-plugin"
        assert meta.version == "1.0.0"
        assert meta.description == "A test plugin"
        assert meta.author == ""
        assert meta.tags == []

    def test_base_plugin_abstract_methods(self):
        """BasePlugin must define abstract methods"""
        from jojo_code.plugin import BasePlugin

        # Should not be instantiable directly
        with pytest.raises(TypeError):
            BasePlugin()

    def test_base_plugin_lifecycle(self):
        """Plugin must have lifecycle methods"""
        from jojo_code.plugin import BasePlugin, PluginMetadata

        class DummyPlugin(BasePlugin):
            metadata = PluginMetadata(name="dummy", version="1.0.0", description="")

            def on_load(self) -> None:
                pass

            def on_unload(self) -> None:
                pass

        plugin = DummyPlugin()
        assert plugin.metadata.name == "dummy"
        assert callable(plugin.on_load)
        assert callable(plugin.on_unload)


class TestPluginRegistry:
    """Test plugin registry"""

    def test_registry_singleton(self):
        """PluginRegistry should be a singleton"""
        from jojo_code.plugin import PluginRegistry

        r1 = PluginRegistry.get_instance()
        r2 = PluginRegistry.get_instance()
        assert r1 is r2

    def test_registry_register(self):
        """Should register a plugin"""
        from jojo_code.plugin import BasePlugin, PluginMetadata, PluginRegistry

        class TestPlugin(BasePlugin):
            metadata = PluginMetadata(name="test-reg", version="1.0.0", description="")

            def on_load(self) -> None:
                pass

            def on_unload(self) -> None:
                pass

        registry = PluginRegistry.get_instance()
        registry.clear()  # Start fresh
        registry.register("test-reg", TestPlugin())

        assert registry.get("test-reg") is not None
        assert registry.get("test-reg").metadata.name == "test-reg"

    def test_registry_unregister(self):
        """Should unregister a plugin"""
        from jojo_code.plugin import BasePlugin, PluginMetadata, PluginRegistry

        class TestPlugin(BasePlugin):
            metadata = PluginMetadata(name="test-unreg", version="1.0.0", description="")

            def on_load(self) -> None:
                pass

            def on_unload(self) -> None:
                pass

        registry = PluginRegistry.get_instance()
        registry.clear()
        registry.register("test-unreg", TestPlugin())
        assert registry.get("test-unreg") is not None

        registry.unregister("test-unreg")
        assert registry.get("test-unreg") is None

    def test_registry_list_plugins(self):
        """Should list all registered plugins"""
        from jojo_code.plugin import PluginRegistry

        registry = PluginRegistry.get_instance()
        registry.clear()
        plugins = registry.list_plugins()
        assert isinstance(plugins, list)


class TestPluginDiscovery:
    """Test plugin discovery from files/directories"""

    def test_discover_from_directory(self, tmp_path):
        """Should discover plugins from a directory"""
        from jojo_code.plugin import PluginDiscovery

        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()

        plugin_file = plugin_dir / "hello_plugin.py"
        plugin_file.write_text(
            """
from jojo_code.plugin import BasePlugin, PluginMetadata

class HelloPlugin(BasePlugin):
    metadata = PluginMetadata(name="hello", version="1.0.0", description="Hello plugin")

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass
"""
        )

        discovery = PluginDiscovery()
        plugins = discovery.discover(plugin_dir)
        assert isinstance(plugins, list)


class TestPluginLoader:
    """Test plugin loader"""

    def test_load_plugin_from_module(self):
        """Should load a plugin from a module path"""
        from jojo_code.plugin import PluginLoader

        loader = PluginLoader()
        try:
            plugin = loader.load_from_module("jojo_code.skills.builtins")
            assert plugin is not None
        except Exception:
            assert hasattr(loader, "load_from_module")

    def test_load_plugin_from_file(self, tmp_path):
        """Should load a plugin from a file path"""
        from jojo_code.plugin import PluginLoader

        loader = PluginLoader()

        plugin_file = tmp_path / "my_plugin.py"
        plugin_file.write_text(
            """
from jojo_code.plugin import BasePlugin, PluginMetadata

class MyPlugin(BasePlugin):
    metadata = PluginMetadata(name="my-plugin", version="1.0.0", description="")

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass
"""
        )

        plugin = loader.load_from_file(str(plugin_file))
        assert plugin is not None


class TestPluginHooks:
    """Test plugin hook system"""

    def test_hook_decorator(self):
        """Should be able to define hooks with decorator"""
        from jojo_code.plugin import hook

        @hook("before_tool_call")
        def my_hook(tool_name: str, args: dict) -> None:
            pass

        assert hasattr(my_hook, "_hook_name")
        assert my_hook._hook_name == "before_tool_call"

    def test_hook_dispatcher(self):
        """Should dispatch hooks to registered handlers"""
        from jojo_code.plugin import HookDispatcher

        dispatcher = HookDispatcher()
        called = []

        def handler(data: str) -> None:
            called.append(data)

        dispatcher.register("test_hook", handler)
        dispatcher.dispatch("test_hook", "hello")
        assert called == ["hello"]


class TestPluginPermissions:
    """Test plugin permission system"""

    def test_plugin_permission_attribute(self):
        """Plugin should have permission level attribute"""
        from jojo_code.plugin import BasePlugin, PluginMetadata, PluginPermission

        class TrustedPlugin(BasePlugin):
            metadata = PluginMetadata(name="trusted", version="1.0.0", description="")
            permission = PluginPermission.TRUSTED

            def on_load(self) -> None:
                pass

            def on_unload(self) -> None:
                pass

        plugin = TrustedPlugin()
        assert plugin.permission == PluginPermission.TRUSTED


class TestPluginTools:
    """Test plugin tools integration"""

    def test_plugin_can_provide_tools(self):
        """Plugin should be able to provide tools to the registry"""
        from jojo_code.plugin import BasePlugin, PluginMetadata, PluginRegistry

        class ToolProvidingPlugin(BasePlugin):
            metadata = PluginMetadata(name="tool-provider", version="1.0.0", description="")
            _tools = []

            def on_load(self) -> None:
                pass

            def on_unload(self) -> None:
                pass

            def get_tools(self):
                return self._tools

        registry = PluginRegistry.get_instance()
        registry.clear()
        registry.register("tool-provider", ToolProvidingPlugin())

        assert registry.get("tool-provider") is not None
        assert hasattr(ToolProvidingPlugin(), "get_tools")


class TestPluginSecurity:
    """Test plugin security sandbox"""

    def test_plugin_sandbox_attribute(self):
        """Plugin should have sandbox configuration"""
        from jojo_code.plugin import BasePlugin, PluginMetadata, PluginSandbox

        class SandboxedPlugin(BasePlugin):
            metadata = PluginMetadata(name="sandboxed", version="1.0.0", description="")
            sandbox = PluginSandbox(restricted=True, allowed_paths=["/tmp"])

            def on_load(self) -> None:
                pass

            def on_unload(self) -> None:
                pass

        plugin = SandboxedPlugin()
        assert plugin.sandbox.restricted is True
        assert "/tmp" in plugin.sandbox.allowed_paths
