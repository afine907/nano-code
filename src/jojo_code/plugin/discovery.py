"""Plugin discovery - find plugins from directories and files"""

import importlib.util
import sys
from pathlib import Path

from jojo_code.plugin.base import BasePlugin


class PluginDiscovery:
    """Discover plugins from directories or Python files

    Discovery looks for:
    1. Directories with a `plugin.py` file defining a BasePlugin subclass
    2. Single `.py` files that define a BasePlugin subclass
    """

    def discover(self, path: Path | str) -> list[BasePlugin]:
        """Discover plugins from a path

        Args:
            path: Directory path or file path

        Returns:
            List of discovered plugin instances
        """
        path = Path(path)

        if not path.exists():
            return []

        if path.is_file():
            return self._discover_from_file(path)
        elif path.is_dir():
            return self._discover_from_directory(path)
        return []

    def _discover_from_file(self, file_path: Path) -> list[BasePlugin]:
        """Discover plugins from a single file"""
        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{file_path.stem}", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module.__name__] = module
                spec.loader.exec_module(module)

                # Find BasePlugin subclasses
                plugins = []
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BasePlugin)
                        and attr is not BasePlugin
                    ):
                        plugins.append(attr())
                return plugins
        except Exception:
            pass
        return []

    def _discover_from_directory(self, dir_path: Path) -> list[BasePlugin]:
        """Discover plugins from a directory"""
        plugins = []

        # Look for plugin.py in subdirectories
        for item in dir_path.iterdir():
            if item.is_dir():
                plugin_file = item / "plugin.py"
                if plugin_file.exists():
                    discovered = self._discover_from_file(plugin_file)
                    plugins.extend(discovered)
            elif item.is_file() and item.suffix == ".py" and item.stem != "__init__":
                discovered = self._discover_from_file(item)
                plugins.extend(discovered)

        return plugins

    def discover_entry_points(self) -> list[BasePlugin]:
        """Discover plugins from installed package entry points

        Plugins can register via setuptools entry_points:
            # pyproject.toml
            [project.entry-points."jojo_code.plugins"]
            my-plugin = "my_plugin:MyPlugin"
        """
        plugins = []
        try:
            from importlib.metadata import entry_points

            eps = entry_points(group="jojo_code.plugins")
            for ep in eps:
                try:
                    plugin_cls = ep.load()
                    if issubclass(plugin_cls, BasePlugin):
                        plugins.append(plugin_cls())
                except Exception:
                    pass
        except Exception:
            pass
        return plugins
