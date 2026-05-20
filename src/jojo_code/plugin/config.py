"""Plugin configuration management.

Supports loading plugin config from:
- plugin.yaml in project root
- pyproject.toml [tool.jojo-code.plugins] section
- Environment variables (JOJO_PLUGIN_*)
- Programmatic API
"""

import os
from pathlib import Path
from typing import Any

import yaml


class PluginConfig:
    """Plugin configuration manager

    Loads and manages plugin settings from various sources.
    Priority (highest to lowest):
    1. Environment variables
    2. plugin.yaml
    3. pyproject.toml
    """

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._enabled_plugins: set[str] = set()
        self._plugin_settings: dict[str, dict[str, Any]] = {}

    def load_from_yaml(self, path: str | Path) -> None:
        """Load configuration from YAML file

        Args:
            path: Path to plugin.yaml file
        """
        path = Path(path)
        if not path.exists():
            return

        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            return

        self._config.update(data.get("plugins", {}))

        # Parse enabled plugins
        enabled = data.get("plugins", {}).get("enabled", [])
        if isinstance(enabled, list):
            self._enabled_plugins.update(enabled)

        # Parse plugin-specific settings
        self._plugin_settings.update(data.get("plugin_settings", {}))

    def load_from_pyproject(self, path: str | Path) -> None:
        """Load configuration from pyproject.toml

        Args:
            path: Path to pyproject.toml
        """
        path = Path(path)
        if not path.exists():
            return

        try:
            import tomllib

            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception:
            # Fallback to basic parsing
            try:
                with open(path) as f:
                    content = f.read()
                    # Simple TOML parsing for [tool.jojo-code.plugins]
                    import re

                    match = re.search(
                        r"\[tool\.jojo-code\.plugins\](.*?)(?=\n\[|\Z)", content, re.DOTALL
                    )
                    if match:
                        section = match.group(1)
                        # Parse simple key=value pairs
                        for line in section.strip().split("\n"):
                            if "=" in line:
                                key, value = line.split("=", 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                if key == "enabled":
                                    plugins = [p.strip() for p in value.split(",")]
                                    self._enabled_plugins.update(plugins)
                                else:
                                    self._config[key] = value
            except Exception:
                return

        plugins_data = data.get("tool", {}).get("jojo-code", {}).get("plugins", {})
        if isinstance(plugins_data, dict):
            self._config.update(plugins_data)
            enabled = plugins_data.get("enabled", [])
            if isinstance(enabled, list):
                self._enabled_plugins.update(enabled)

    def load_from_env(self) -> None:
        """Load configuration from environment variables

        Environment variables:
        - JOJO_PLUGINS_ENABLED: comma-separated list of enabled plugins
        - JOJO_PLUGIN_<NAME>_ENABLED: enable/disable specific plugin
        - JOJO_PLUGIN_<NAME>_CONFIG: JSON config for specific plugin
        """
        # Load enabled plugins from env
        enabled_env = os.getenv("JOJO_PLUGINS_ENABLED", "")
        if enabled_env:
            plugins = [p.strip() for p in enabled_env.split(",") if p.strip()]
            self._enabled_plugins.update(plugins)

        # Load individual plugin settings from env
        import json
        import re

        for key, value in os.environ.items():
            if key.startswith("JOJO_PLUGIN_"):
                match = re.match(r"JOJO_PLUGIN_(\w+)_(\w+)", key)
                if match:
                    plugin_name = match.group(1).lower()
                    setting_name = match.group(2).lower()

                    if setting_name == "enabled":
                        if value.lower() in ("true", "1", "yes"):
                            self._enabled_plugins.add(plugin_name)
                        elif value.lower() in ("false", "0", "no"):
                            self._enabled_plugins.discard(plugin_name)
                    else:
                        if plugin_name not in self._plugin_settings:
                            self._plugin_settings[plugin_name] = {}
                        try:
                            self._plugin_settings[plugin_name][setting_name] = json.loads(value)
                        except json.JSONDecodeError:
                            self._plugin_settings[plugin_name][setting_name] = value

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled

        Args:
            plugin_name: Plugin name

        Returns:
            True if enabled, False if disabled
        """
        # If no enabled list is specified, all plugins are enabled by default
        if not self._enabled_plugins:
            return True
        return plugin_name in self._enabled_plugins

    def get_plugin_setting(self, plugin_name: str, key: str, default: Any = None) -> Any:
        """Get a plugin-specific setting

        Args:
            plugin_name: Plugin name
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        return self._plugin_settings.get(plugin_name, {}).get(key, default)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a global plugin config value

        Args:
            key: Config key
            default: Default value if not found

        Returns:
            Config value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a global plugin config value

        Args:
            key: Config key
            value: Config value
        """
        self._config[key] = value

    def auto_load(self, project_root: str | Path | None = None) -> None:
        """Auto-load config from standard locations

        Args:
            project_root: Project root directory (default: cwd)
        """
        if project_root is None:
            project_root = Path.cwd()
        else:
            project_root = Path(project_root)

        # Load from plugin.yaml
        plugin_yaml = project_root / "plugin.yaml"
        if plugin_yaml.exists():
            self.load_from_yaml(plugin_yaml)

        # Load from pyproject.toml
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            self.load_from_pyproject(pyproject)

        # Load from environment
        self.load_from_env()


# Global config instance
_config: PluginConfig | None = None


def get_plugin_config() -> PluginConfig:
    """Get the global plugin config instance"""
    global _config
    if _config is None:
        _config = PluginConfig()
        _config.auto_load()
    return _config
