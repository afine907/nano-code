"""Plugin system for jojo-code"""

from jojo_code.plugin.base import (
    BasePlugin,
    PluginMetadata,
    PluginPermission,
    PluginSandbox,
)
from jojo_code.plugin.discovery import PluginDiscovery
from jojo_code.plugin.hooks import HookDispatcher, hook
from jojo_code.plugin.loader import PluginLoader
from jojo_code.plugin.registry import PluginRegistry

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginPermission",
    "PluginSandbox",
    "PluginRegistry",
    "PluginDiscovery",
    "PluginLoader",
    "HookDispatcher",
    "hook",
]
