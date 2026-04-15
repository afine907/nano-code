"""
Nano Code - 插件系统
支持扩展功能的热插拔插件系统
"""

import asyncio
import importlib
import importlib.util
import json
import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import semver

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """插件错误"""

    pass


class PluginLoadError(PluginError):
    """插件加载错误"""

    pass


class PluginNotFoundError(PluginError):
    """插件未找到错误"""

    pass


@dataclass
class PluginMetadata:
    """插件元数据"""

    name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    homepage: str = ""
    keywords: list[str] = field(default_factory=list)
    dependencies: dict[str, str] = field(default_factory=dict)
    min_nano_code_version: str = "0.1.0"
    max_nano_code_version: str = None


@dataclass
class Plugin:
    """插件实例"""

    metadata: PluginMetadata
    module: Any
    enabled: bool = False
    loaded_at: str | None = None

    def __post_init__(self):
        if not self.loaded_at:
            from datetime import datetime

            self.loaded_at = datetime.now().isoformat()


class PluginInterface(ABC):
    """插件接口基类"""

    @abstractmethod
    async def on_load(self) -> None:
        """插件加载时调用"""
        pass

    @abstractmethod
    async def on_unload(self) -> None:
        """插件卸载时调用"""
        pass

    @abstractmethod
    async def on_enable(self) -> None:
        """插件启用时调用"""
        pass

    @abstractmethod
    async def on_disable(self) -> None:
        """插件禁用时调用"""
        pass


class PluginManager:
    """插件管理器"""

    def __init__(self, plugins_dir: Path = None):
        self.plugins_dir = plugins_dir or Path.home() / ".nano-code" / "plugins"
        self.plugins: dict[str, Plugin] = {}
        self.hooks: dict[str, list[Callable]] = {}
        self._lock = asyncio.Lock()

        # 确保插件目录存在
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def discover_plugins(self) -> list[Path]:
        """发现可用插件"""
        plugins = []

        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "plugin.py").exists():
                plugins.append(item)
            elif item.is_file() and item.suffix == ".py":
                plugins.append(item)

        return plugins

    async def load_plugin(self, plugin_path: Path) -> Plugin:
        """加载插件"""
        async with self._lock:
            # 获取插件路径
            if plugin_path.is_dir():
                plugin_file = plugin_path / "plugin.py"
            else:
                plugin_file = plugin_path
                plugin_path = plugin_path.parent

            # 加载模块
            spec = importlib.util.spec_from_file_location("nano_code_plugin", plugin_file)

            if spec is None or spec.loader is None:
                raise PluginLoadError(f"Cannot load plugin from {plugin_file}")

            module = importlib.util.module_from_spec(spec)

            # 添加到 sys.modules
            module_name = f"nano_code_plugins.{plugin_path.stem}"
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 检查是否有 metadata
            if not hasattr(module, "PLUGIN_METADATA"):
                raise PluginLoadError(f"Plugin {plugin_path} missing PLUGIN_METADATA")

            metadata_dict = module.PLUGIN_METADATA
            metadata = PluginMetadata(**metadata_dict)

            # 检查版本兼容性
            current_version = "0.2.0"  # 应该是 nano-code 的版本
            if not self._check_version_compatibility(
                current_version, metadata.min_nano_code_version, metadata.max_nano_code_version
            ):
                raise PluginLoadError(
                    f"Plugin requires nano-code >={metadata.min_nano_code_version}"
                )

            # 创建插件实例
            plugin = Plugin(metadata=metadata, module=module)

            # 调用 on_load 钩子
            if hasattr(module, "on_load"):
                await module.on_load()

            # 注册插件
            self.plugins[metadata.name] = plugin
            logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")

            return plugin

    def _check_version_compatibility(
        self, current: str, min_version: str, max_version: str | None
    ) -> bool:
        """检查版本兼容性"""
        current_v = semver.VersionInfo.parse(current)

        if min_version:
            min_v = semver.VersionInfo.parse(min_version)
            if current_v < min_v:
                return False

        if max_version:
            max_v = semver.VersionInfo.parse(max_version)
            if current_v > max_v:
                return False

        return True

    async def unload_plugin(self, name: str) -> None:
        """卸载插件"""
        async with self._lock:
            if name not in self.plugins:
                raise PluginNotFoundError(f"Plugin {name} not found")

            plugin = self.plugins[name]

            # 调用 on_unload 钩子
            if hasattr(plugin.module, "on_unload"):
                await plugin.module.on_unload()

            # 移除插件
            del self.plugins[name]
            logger.info(f"Unloaded plugin: {name}")

    async def enable_plugin(self, name: str) -> None:
        """启用插件"""
        async with self._lock:
            if name not in self.plugins:
                raise PluginNotFoundError(f"Plugin {name} not found")

            plugin = self.plugins[name]

            if not plugin.enabled:
                # 调用 on_enable 钩子
                if hasattr(plugin.module, "on_enable"):
                    await plugin.module.on_enable()

                plugin.enabled = True
                logger.info(f"Enabled plugin: {name}")

    async def disable_plugin(self, name: str) -> None:
        """禁用插件"""
        async with self._lock:
            if name not in self.plugins:
                raise PluginNotFoundError(f"Plugin {name} not found")

            plugin = self.plugins[name]

            if plugin.enabled:
                # 调用 on_disable 钩子
                if hasattr(plugin.module, "on_disable"):
                    await plugin.module.on_disable()

                plugin.enabled = False
                logger.info(f"Disabled plugin: {name}")

    def get_plugin(self, name: str) -> Plugin | None:
        """获取插件"""
        return self.plugins.get(name)

    def list_plugins(self, enabled_only: bool = False) -> list[Plugin]:
        """列出插件"""
        plugins = list(self.plugins.values())

        if enabled_only:
            plugins = [p for p in plugins if p.enabled]

        return plugins

    def register_hook(self, hook_name: str, handler: Callable) -> None:
        """注册钩子"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(handler)

    def unregister_hook(self, hook_name: str, handler: Callable) -> None:
        """注销钩子"""
        if hook_name in self.hooks:
            self.hooks[hook_name].remove(handler)

    async def trigger_hook(self, hook_name: str, *args, **kwargs) -> list[Any]:
        """触发钩子"""
        results = []

        if hook_name in self.hooks:
            for handler in self.hooks[hook_name]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(*args, **kwargs)
                    else:
                        result = handler(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Hook {hook_name} error: {e}")

        return results

    async def load_all_plugins(self) -> None:
        """加载所有可用插件"""
        plugin_paths = self.discover_plugins()

        for plugin_path in plugin_paths:
            try:
                plugin = await self.load_plugin(plugin_path)

                # 自动启用
                await self.enable_plugin(plugin.metadata.name)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_path}: {e}")

    def get_plugin_info(self, name: str) -> dict | None:
        """获取插件信息"""
        plugin = self.get_plugin(name)

        if plugin is None:
            return None

        return {
            "name": plugin.metadata.name,
            "version": plugin.metadata.version,
            "description": plugin.metadata.description,
            "author": plugin.metadata.author,
            "enabled": plugin.enabled,
            "loaded_at": plugin.loaded_at,
        }


class PluginContext:
    """插件上下文，提供插件访问核心功能的接口"""

    def __init__(self, plugin_name: str, manager: PluginManager):
        self.plugin_name = plugin_name
        self.manager = manager

    def register_command(self, name: str, handler: Callable) -> None:
        """注册命令"""
        self.manager.register_hook(f"command:{name}", handler)

    def register_tool(self, name: str, tool_class: type) -> None:
        """注册工具"""
        self.manager.register_hook(f"tool:{name}", tool_class)

    def emit_event(self, event_name: str, data: dict) -> None:
        """发出事件"""
        self.manager.trigger_hook(f"event:{event_name}", data)

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        # 从插件配置目录读取
        config_file = self.manager.plugins_dir / self.plugin_name / "config.json"

        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
                return config.get(key, default)

        return default

    def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        config_file = self.manager.plugins_dir / self.plugin_name / "config.json"

        config = {}
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)

        config[key] = value

        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)


def create_plugin_template(name: str, version: str, author: str) -> None:
    """创建插件模板"""
    template_dir = Path(__file__).parent.parent.parent / "plugins" / name
    template_dir.mkdir(parents=True, exist_ok=True)

    # 创建 plugin.py
    plugin_code = f'''"""
{name} - Nano Code Plugin
"""

PLUGIN_METADATA = {{
    "name": "{name}",
    "version": "{version}",
    "description": "A Nano Code plugin",
    "author": "{author}",
    "license": "MIT",
    "keywords": [],
    "dependencies": {{}},
    "min_nano_code_version": "0.1.0"
}}


class {name.replace("-", "_").title().replace("_", "")}Plugin:
    """插件主类"""

    async def on_load(self):
        """插件加载"""
        print("Loading {name}...")

    async def on_unload(self):
        """插件卸载"""
        print("Unloading {name}...")

    async def on_enable(self):
        """插件启用"""
        print("Enabling {name}...")

    async def on_disable(self):
        """插件禁用"""
        print("Disabling {name}...")


# 导出插件实例
plugin = {name.replace("-", "_").title().replace("_", "")}Plugin()


# 异步加载钩子
async def on_load():
    await plugin.on_load()


# 异步卸载钩子
async def on_unload():
    await plugin.on_unload()


# 异步启用钩子
async def on_enable():
    await plugin.on_enable()


# 异步禁用钩子
async def on_disable():
    await plugin.on_disable()
'''

    with open(template_dir / "plugin.py", "w") as f:
        f.write(plugin_code)

    # 创建 config.json
    with open(template_dir / "config.json", "w") as f:
        json.dump({}, f)

    # 创建 README.md
    readme = f"""# {name}

A Nano Code plugin.

## Installation

Place this folder in `~/.nano-code/plugins/`

## Configuration

Edit `config.json` to customize behavior.
"""

    with open(template_dir / "README.md", "w") as f:
        f.write(readme)

    print(f"Created plugin template at {template_dir}")


# 全局插件管理器
_plugin_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
