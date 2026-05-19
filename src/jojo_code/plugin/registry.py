"""Plugin registry - manages all loaded plugins"""

from typing import TYPE_CHECKING

from jojo_code.plugin.base import BasePlugin

if TYPE_CHECKING:
    from jojo_code.plugin.hooks import HookDispatcher


class PluginRegistry:
    """Plugin registry - singleton managing all plugins

    Plugin registry provides:
    - Plugin registration/unregistration
    - Plugin lookup by name
    - Lifecycle management (load/unload)
    - Hook dispatching
    """

    _instance: "PluginRegistry | None" = None

    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._dispatcher: HookDispatcher | None = None

    @classmethod
    def get_instance(cls) -> "PluginRegistry":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_dispatcher(self, dispatcher: "HookDispatcher") -> None:
        """Set the hook dispatcher"""
        self._dispatcher = dispatcher

    def register(self, name: str, plugin: BasePlugin) -> None:
        """Register a plugin

        Args:
            name: Plugin name
            plugin: Plugin instance
        """
        if name in self._plugins:
            raise ValueError(f"Plugin already registered: {name}")
        self._plugins[name] = plugin
        plugin.on_load()

        # Register plugin hooks
        if self._dispatcher:
            for hook_name, handler in plugin.get_hooks().items():
                self._dispatcher.register(hook_name, handler)

    def unregister(self, name: str) -> None:
        """Unregister a plugin

        Args:
            name: Plugin name
        """
        if name not in self._plugins:
            return
        plugin = self._plugins.pop(name)
        plugin.on_unload()

    def get(self, name: str) -> BasePlugin | None:
        """Get plugin by name"""
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        """List all registered plugin names"""
        return list(self._plugins.keys())

    def get_all(self) -> list[BasePlugin]:
        """Get all plugins"""
        return list(self._plugins.values())

    def clear(self) -> None:
        """Clear all plugins (for testing)"""
        self._plugins.clear()
