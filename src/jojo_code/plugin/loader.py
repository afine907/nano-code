"""Plugin loader - load plugins from modules or files"""

import importlib
import importlib.util
import sys
from pathlib import Path

from jojo_code.plugin.base import BasePlugin


class PluginLoadError(Exception):
    """Error loading a plugin"""


class PluginLoader:
    """Load plugins from Python modules or files"""

    def load_from_module(self, module_path: str) -> BasePlugin:
        """Load a plugin from a module path

        Args:
            module_path: Dotted module path, e.g. "jojo_code.skills.builtins"

        Returns:
            Plugin instance

        Raises:
            PluginLoadError: If loading fails
        """
        try:
            module = importlib.import_module(module_path)

            # Find the plugin class in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                ):
                    return attr()

            raise PluginLoadError(f"No BasePlugin subclass found in {module_path}")
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin from {module_path}: {e}") from e

    def load_from_file(self, file_path: str | Path) -> BasePlugin:
        """Load a plugin from a Python file

        Args:
            file_path: Path to Python file

        Returns:
            Plugin instance

        Raises:
            PluginLoadError: If loading fails
        """
        file_path = Path(file_path)

        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{file_path.stem}", file_path)
            if not spec or not spec.loader:
                raise PluginLoadError(f"Cannot load spec from {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module.__name__] = module
            spec.loader.exec_module(module)

            # Find BasePlugin subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                ):
                    return attr()

            raise PluginLoadError(f"No BasePlugin subclass found in {file_path}")
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin from {file_path}: {e}") from e

    def load_from_class(self, plugin_class: type[BasePlugin]) -> BasePlugin:
        """Load a plugin from a class

        Args:
            plugin_class: A BasePlugin subclass

        Returns:
            Plugin instance
        """
        if not issubclass(plugin_class, BasePlugin):
            raise PluginLoadError(f"{plugin_class} is not a BasePlugin subclass")
        return plugin_class()
