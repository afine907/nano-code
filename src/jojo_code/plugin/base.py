"""Plugin base classes and types"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from jojo_code.tools.registry import BaseTool


class PluginPermission(Enum):
    """Plugin permission level (mirrors Claude Code's permission system)"""

    UNTRUSTED = "untrusted"  # No file system or network access
    RESTRICTED = "restricted"  # Limited file system, no network
    TRUSTED = "trusted"  # Full access


@dataclass
class PluginMetadata:
    """Plugin metadata"""

    name: str
    version: str
    description: str
    author: str = ""
    tags: list[str] = field(default_factory=list)
    license: str = ""
    home_url: str = ""


@dataclass
class PluginSandbox:
    """Plugin sandbox configuration"""

    restricted: bool = False  # Run in restricted mode
    allowed_paths: list[str] = field(default_factory=list)  # Allowed FS paths
    allowed_urls: list[str] = field(default_factory=list)  # Allowed network URLs
    max_memory_mb: int = 0  # Memory limit (0 = unlimited)


class BasePlugin(ABC):
    """Plugin base class

    All jojo-code plugins must inherit from this class and implement
    the required lifecycle methods.
    """

    # Plugin metadata (must be set by subclass)
    metadata: PluginMetadata

    # Permission level (default: UNTRUSTED)
    permission: PluginPermission = PluginPermission.UNTRUSTED

    # Sandbox configuration (default: no sandbox)
    sandbox: PluginSandbox = field(default_factory=PluginSandbox)

    @abstractmethod
    def on_load(self) -> None:
        """Called when plugin is loaded"""

    @abstractmethod
    def on_unload(self) -> None:
        """Called when plugin is unloaded"""

    def get_tools(self) -> list[BaseTool]:
        """Return list of tools provided by this plugin

        Override this to provide custom tools.
        """
        return []

    def get_hooks(self) -> dict[str, Any]:
        """Return hook handlers

        Returns:
            Dict of hook_name -> handler function
        """
        return {}
