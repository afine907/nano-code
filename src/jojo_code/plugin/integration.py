"""Plugin integration for jojo-code agent

Wires the plugin system into the agent execution pipeline:
- Hooks are dispatched at lifecycle events
- Plugin tools are registered with the tool registry
- Plugin discovery and loading on app startup
"""

import logging
from typing import Any

from jojo_code.plugin.discovery import PluginDiscovery
from jojo_code.plugin.hooks import HookDispatcher
from jojo_code.plugin.registry import PluginRegistry
from jojo_code.plugins.code_review import CodeReviewPlugin
from jojo_code.plugins.git_plugin import GitPlugin
from jojo_code.plugins.test_generator import TestGeneratorPlugin

logger = logging.getLogger(__name__)

# Global hook dispatcher (singleton)
_hook_dispatcher: HookDispatcher | None = None

# Global registry (singleton)
_registry: PluginRegistry | None = None


def get_hook_dispatcher() -> HookDispatcher:
    """Get the global hook dispatcher instance (singleton)"""
    global _hook_dispatcher
    if _hook_dispatcher is None:
        _hook_dispatcher = HookDispatcher()
    return _hook_dispatcher


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance (singleton)"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry.get_instance()
    return _registry


def init_plugins(plugins_dir: str | None = None) -> list[str]:
    """Initialize and load all plugins

    Args:
        plugins_dir: Optional path to plugins directory

    Returns:
        List of loaded plugin names
    """
    from jojo_code.plugin.config import get_plugin_config

    dispatcher = get_hook_dispatcher()
    registry = get_plugin_registry()
    registry.set_dispatcher(dispatcher)

    # Get plugin config for enable/disable
    config = get_plugin_config()

    # Register official plugins
    official_plugins = [
        CodeReviewPlugin(),
        TestGeneratorPlugin(),
        GitPlugin(),
    ]

    loaded = []
    for plugin in official_plugins:
        # Check if plugin is enabled in config
        if not config.is_plugin_enabled(plugin.metadata.name):
            logger.info(f"Skipping disabled plugin: {plugin.metadata.name}")
            continue

        try:
            registry.register(plugin.metadata.name, plugin)
            loaded.append(plugin.metadata.name)
            logger.info(f"Loaded official plugin: {plugin.metadata.name}")
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin.metadata.name}: {e}")

    # Discover and load community plugins from plugins_dir
    if plugins_dir:
        from pathlib import Path

        discovery = PluginDiscovery()
        discovered = discovery.discover(Path(plugins_dir))
        for plugin in discovered:
            # Check if plugin is enabled in config
            if not config.is_plugin_enabled(plugin.metadata.name):
                logger.info(f"Skipping disabled plugin: {plugin.metadata.name}")
                continue

            try:
                registry.register(plugin.metadata.name, plugin)
                loaded.append(plugin.metadata.name)
                logger.info(f"Loaded community plugin: {plugin.metadata.name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin.metadata.name}: {e}")

    # Discover from entry points
    discovered_eps = discovery.discover_entry_points()
    for plugin in discovered_eps:
        # Check if plugin is enabled in config
        if not config.is_plugin_enabled(plugin.metadata.name):
            logger.info(f"Skipping disabled plugin: {plugin.metadata.name}")
            continue

        try:
            registry.register(plugin.metadata.name, plugin)
            loaded.append(plugin.metadata.name)
            logger.info(f"Loaded entry point plugin: {plugin.metadata.name}")
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin.metadata.name}: {e}")

    return loaded


def register_plugin_tools() -> None:
    """Register all plugin tools with the tool registry

    Call this after init_plugins() to make plugin tools available.
    """
    from jojo_code.tools.registry import get_tool_registry

    registry = get_plugin_registry()
    tool_registry = get_tool_registry()

    for plugin in registry.get_all():
        try:
            tools = plugin.get_tools()
            for tool in tools:
                tool_registry.register(tool)
                logger.debug(f"Registered tool: {tool.name} from plugin {plugin.metadata.name}")
        except Exception as e:
            logger.error(f"Failed to register tools from plugin {plugin.metadata.name}: {e}")


def dispatch_hook(hook_name: str, *args: Any, **kwargs: Any) -> list[Any]:
    """Dispatch a hook event to all registered handlers

    Args:
        hook_name: Name of the hook
        *args: Positional args to pass to handlers
        **kwargs: Keyword args to pass to handlers

    Returns:
        List of handler return values
    """
    dispatcher = get_hook_dispatcher()
    return dispatcher.dispatch(hook_name, *args, **kwargs)
