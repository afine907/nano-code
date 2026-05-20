"""jojo-code CLI 入口。

命令:
    jojo-code                  # 启动 TUI
    jojo-code server start     # 启动 WebSocket 服务（前台）
    jojo-code server start -d  # 启动 WebSocket 服务（后台守护）
    jojo-code server stop      # 停止服务
    jojo-code server status    # 查看服务状态
    jojo-code config set       # 设置配置
    jojo-code config show      # 显示配置
    jojo-code config get       # 获取单个配置
"""

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

# ========== 常量 ==========

CONFIG_DIR = Path.home() / ".jojo-code"
CONFIG_FILE = CONFIG_DIR / "config.json"
PID_FILE = CONFIG_DIR / "server.pid"
LOG_FILE = CONFIG_DIR / "server.log"

DEFAULT_CONFIG = {
    "server": "ws://localhost:8080/ws",
    "host": "0.0.0.0",
    "port": "8080",
    "model": "",
}


# ========== 配置管理 ==========


def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """保存配置文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_config_value(key: str) -> str | None:
    """获取配置值"""
    config = load_config()
    return config.get(key)


# ========== 服务管理 ==========


def _read_pid() -> int | None:
    """读取 PID 文件"""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # 检查进程是否还活着
            os.kill(pid, 0)
            return pid
        except (ValueError, ProcessLookupError, PermissionError):
            # PID 文件存在但进程已死，清理
            PID_FILE.unlink(missing_ok=True)
    return None


def _write_pid(pid: int) -> None:
    """写入 PID 文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


def _remove_pid() -> None:
    """删除 PID 文件"""
    PID_FILE.unlink(missing_ok=True)


def server_start(args):
    """启动 WebSocket 服务"""
    config = load_config()
    host = args.host or config.get("host", "0.0.0.0")
    port = args.port or config.get("port", "8080")

    # 检查是否已在运行
    existing_pid = _read_pid()
    if existing_pid is not None:
        print(f"服务已在运行 (PID: {existing_pid})")
        print("如需重启，请先执行: jojo-code server stop")
        return

    if args.daemon:
        # 后台守护模式
        _start_daemon(host, int(port))
    else:
        # 前台模式
        _start_foreground(host, int(port))


def _start_foreground(host: str, port: int):
    """前台启动服务"""
    os.environ["JOJO_CODE_HOST"] = host
    os.environ["JOJO_CODE_PORT"] = str(port)

    print("🚀 jojo-code 服务启动中...")
    print(f"   地址: ws://{host}:{port}/ws")
    print(f"   健康检查: http://{host}:{port}/health")
    print("   按 Ctrl+C 停止")
    print()

    try:
        from jojo_code.server.ws_server import main as server_main

        # 写入 PID（当前进程）
        _write_pid(os.getpid())
        server_main()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        _remove_pid()


def _start_daemon(host: str, port: int):
    """后台守护模式启动"""
    os.environ["JOJO_CODE_HOST"] = host
    os.environ["JOJO_CODE_PORT"] = str(port)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 启动子进程
    process = subprocess.Popen(
        [sys.executable, "-m", "jojo_code.server.ws_server"],
        stdout=open(LOG_FILE, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    _write_pid(process.pid)

    print(f"🚀 服务已在后台启动 (PID: {process.pid})")
    print(f"   地址: ws://{host}:{port}/ws")
    print(f"   日志: {LOG_FILE}")
    print("   停止: jojo-code server stop")


def server_stop(args):
    """停止服务"""
    pid = _read_pid()
    if pid is None:
        print("服务未运行")
        return

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"已发送停止信号 (PID: {pid})")

        # 等待进程退出
        import time

        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except ProcessLookupError:
                break

        _remove_pid()
        print("服务已停止")
    except ProcessLookupError:
        print("进程已不存在")
        _remove_pid()
    except PermissionError:
        print(f"无权限停止进程 {pid}")


def server_status(args):
    """查看服务状态"""
    pid = _read_pid()
    if pid is None:
        print("⚪ 服务未运行")
        return

    print(f"🟢 服务运行中 (PID: {pid})")

    # 尝试健康检查
    config = load_config()
    port = config.get("port", "8080")
    try:
        import urllib.request

        req = urllib.request.urlopen(f"http://localhost:{port}/health", timeout=2)
        data = json.loads(req.read())
        print(f"   状态: {data.get('status', 'unknown')}")
        print(f"   版本: {data.get('version', 'unknown')}")
    except Exception:
        print("   状态: 无法连接")


def config_set(args):
    """设置配置"""
    config = load_config()
    config[args.key] = args.value
    save_config(config)
    print(f"✅ {args.key} = {args.value}")


def config_show(args):
    """显示配置"""
    config = load_config()
    if not config:
        print("暂无配置")
        return

    print("当前配置:")
    for k, v in config.items():
        print(f"  {k} = {v}")


def config_get(args):
    """获取单个配置"""
    config = load_config()
    value = config.get(args.key)
    if value is None:
        print(f"配置 '{args.key}' 不存在")
    else:
        print(value)


def start_tui(args):
    """启动 Textual TUI"""
    # 从配置获取 server URL
    config = load_config()
    server_url = args.server or config.get("server", "ws://localhost:8080/ws")

    try:
        from jojo_code.cli.app import JojoCodeApp

        app = JojoCodeApp(server_url=server_url)
        app.run()
    except ImportError as e:
        print(f"错误: 缺少依赖 - {e}")
        print("请运行: pip install 'jojo-code'")
        sys.exit(1)
    except KeyboardInterrupt:
        pass


# ========== 插件管理 ==========

PLUGIN_CONFIG_FILE = Path.home() / ".jojo-code" / "plugin_config.json"


def _load_plugin_config() -> dict:
    """加载插件配置"""
    if PLUGIN_CONFIG_FILE.exists():
        try:
            return json.loads(PLUGIN_CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"enabled_plugins": [], "disabled_plugins": []}
    return {"enabled_plugins": [], "disabled_plugins": []}


def _save_plugin_config(config: dict) -> None:
    """保存插件配置"""
    PLUGIN_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    PLUGIN_CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _get_all_plugins() -> list[tuple[str, dict]]:
    """获取所有插件及其信息"""
    from pathlib import Path

    from jojo_code.plugin.discovery import PluginDiscovery
    from jojo_code.plugin.integration import get_plugin_registry

    plugins = []

    # 获取已注册插件
    registry = get_plugin_registry()
    for name in registry.list_plugins():
        plugin = registry.get(name)
        if plugin:
            plugins.append(
                (
                    name,
                    {
                        "name": plugin.metadata.name,
                        "version": plugin.metadata.version,
                        "description": plugin.metadata.description,
                        "author": plugin.metadata.author,
                        "tags": plugin.metadata.tags,
                        "permission": (
                            plugin.permission.value
                            if hasattr(plugin.permission, "value")
                            else str(plugin.permission)
                        ),
                        "enabled": True,
                        "registered": True,
                    },
                )
            )

    # 发现社区插件
    plugins_dir = Path.home() / ".jojo-code" / "plugins"
    if plugins_dir.exists():
        discovery = PluginDiscovery()
        discovered = discovery.discover(plugins_dir)
        for plugin in discovered:
            name = plugin.metadata.name
            # 跳过已注册的
            if any(p[0] == name for p in plugins):
                continue
            plugins.append(
                (
                    name,
                    {
                        "name": plugin.metadata.name,
                        "version": plugin.metadata.version,
                        "description": plugin.metadata.description,
                        "author": plugin.metadata.author,
                        "tags": plugin.metadata.tags,
                        "permission": (
                            plugin.permission.value
                            if hasattr(plugin.permission, "value")
                            else str(plugin.permission)
                        ),
                        "enabled": False,
                        "registered": False,
                    },
                )
            )

    return plugins


def plugin_list(args):
    """列出所有插件"""
    plugins = _get_all_plugins()
    config = _load_plugin_config()
    enabled_set = set(config.get("enabled_plugins", []))
    disabled_set = set(config.get("disabled_plugins", []))

    if not plugins:
        print("📦 未发现任何插件")
        print("\n安装插件：")
        print("  1. 将插件放置到 ~/.jojo-code/plugins/ 目录")
        print("  2. 或通过 entry points 安装")
        return

    print("📦 jojo-code 插件列表")
    print("=" * 60)

    enabled_count = 0
    disabled_count = 0

    for name, info in sorted(plugins):
        # 判断状态
        if name in enabled_set or (name not in disabled_set and info.get("registered")):
            status = "🟢 已启用"
            enabled_count += 1
        else:
            status = "⚪ 已禁用"
            disabled_count += 1

        print(f"\n{info['name']} v{info['version']} [{status}]")
        print(f"   {info['description']}")
        print(f"   作者: {info['author']}")
        if info.get("tags"):
            print(f"   标签: {', '.join(info['tags'])}")

    print("\n" + "=" * 60)
    print(f"共 {len(plugins)} 个插件：{enabled_count} 已启用，{disabled_count} 已禁用")


def plugin_enable(args):
    """启用插件"""
    plugin_name = args.name
    config = _load_plugin_config()

    # 检查插件是否存在
    from jojo_code.plugin.integration import get_plugin_registry

    registry = get_plugin_registry()
    plugin = registry.get(plugin_name)

    # 移除禁用列表
    if plugin_name in config.get("disabled_plugins", []):
        config["disabled_plugins"].remove(plugin_name)

    # 添加启用列表
    if plugin_name not in config.get("enabled_plugins", []):
        config.setdefault("enabled_plugins", []).append(plugin_name)

    _save_plugin_config(config)

    if plugin:
        registry.enable(plugin_name)
        print(f"✅ 插件 '{plugin_name}' 已启用")
    else:
        print(f"✅ 插件 '{plugin_name}' 已添加到启用列表（下次启动时加载）")


def plugin_disable(args):
    """禁用插件"""
    plugin_name = args.name
    config = _load_plugin_config()

    # 检查插件是否存在
    from jojo_code.plugin.integration import get_plugin_registry

    registry = get_plugin_registry()
    plugin = registry.get(plugin_name)

    # 移除启用列表
    if plugin_name in config.get("enabled_plugins", []):
        config["enabled_plugins"].remove(plugin_name)

    # 添加禁用列表
    if plugin_name not in config.get("disabled_plugins", []):
        config.setdefault("disabled_plugins", []).append(plugin_name)

    _save_plugin_config(config)

    if plugin:
        registry.disable(plugin_name)
        print(f"✅ 插件 '{plugin_name}' 已禁用")
    else:
        print(f"✅ 插件 '{plugin_name}' 已添加到禁用列表")


def plugin_info(args):
    """显示插件详情"""
    plugin_name = args.name

    from jojo_code.plugin.integration import get_plugin_registry

    registry = get_plugin_registry()
    plugin = registry.get(plugin_name)

    if not plugin:
        print(f"❌ 插件 '{plugin_name}' 未找到")
        return

    print(f"📋 插件详情: {plugin.metadata.name}")
    print("=" * 60)
    print(f"版本:     {plugin.metadata.version}")
    print(f"描述:     {plugin.metadata.description}")
    print(f"作者:     {plugin.metadata.author}")
    tags_str = ", ".join(plugin.metadata.tags) if plugin.metadata.tags else "无"
    perm_str = plugin.permission.value if hasattr(plugin.permission, "value") else plugin.permission
    has_sandbox = hasattr(plugin, "sandbox") and plugin.sandbox and plugin.sandbox.restricted
    sandbox_str = "有" if has_sandbox else "无"
    print(f"标签:     {tags_str}")
    print(f"权限:     {perm_str}")
    print(f"沙箱:     {sandbox_str}")

    # 提供的工具
    tools = plugin.get_tools()
    if tools:
        print(f"\n提供的工具 ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:50]}...")

    # 注册的钩子
    hooks = plugin.get_hooks()
    if hooks:
        print(f"\n注册的钩子 ({len(hooks)}):")
        for hook_name in hooks.keys():
            print(f"  - {hook_name}")


# ========== 主入口 ==========


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        prog="jojo-code",
        description="jojo-code - Python coding agent powered by LangGraph",
    )
    parser.add_argument(
        "--server",
        help="WebSocket server URL (默认从配置读取)",
        default=None,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # server 子命令
    server_parser = subparsers.add_parser("server", help="管理 WebSocket 服务")
    server_sub = server_parser.add_subparsers(dest="action")
    start_parser = server_sub.add_parser("start", help="启动服务")
    start_parser.add_argument("-d", "--daemon", action="store_true", help="后台运行")
    start_parser.add_argument("--host", help="监听地址")
    start_parser.add_argument("--port", help="监听端口")
    server_sub.add_parser("stop", help="停止服务")
    server_sub.add_parser("status", help="查看服务状态")

    # config 子命令
    config_parser = subparsers.add_parser("config", help="管理配置")
    config_sub = config_parser.add_subparsers(dest="action")
    config_set_parser = config_sub.add_parser("set", help="设置配置")
    config_set_parser.add_argument("key", help="配置项")
    config_set_parser.add_argument("value", help="配置值")
    config_sub.add_parser("show", help="显示所有配置")
    config_get_parser = config_sub.add_parser("get", help="获取配置值")
    config_get_parser.add_argument("key", help="配置项")

    # plugin 子命令
    plugin_parser = subparsers.add_parser("plugin", help="管理插件")
    plugin_sub = plugin_parser.add_subparsers(dest="action")
    plugin_list_parser = plugin_sub.add_parser("list", help="列出所有插件")
    plugin_list_parser.set_defaults(func=plugin_list)
    plugin_enable_parser = plugin_sub.add_parser("enable", help="启用插件")
    plugin_enable_parser.add_argument("name", help="插件名称")
    plugin_enable_parser.set_defaults(func=plugin_enable)
    plugin_disable_parser = plugin_sub.add_parser("disable", help="禁用插件")
    plugin_disable_parser.add_argument("name", help="插件名称")
    plugin_disable_parser.set_defaults(func=plugin_disable)
    plugin_info_parser = plugin_sub.add_parser("info", help="显示插件详情")
    plugin_info_parser.add_argument("name", help="插件名称")
    plugin_info_parser.set_defaults(func=plugin_info)

    args = parser.parse_args()

    if args.command is None:
        start_tui(args)
    elif args.command == "server":
        if args.action == "start":
            server_start(args)
        elif args.action == "stop":
            server_stop(args)
        elif args.action == "status":
            server_status(args)
        else:
            server_parser.print_help()
    elif args.command == "config":
        if args.action == "set":
            config_set(args)
        elif args.action == "show":
            config_show(args)
        elif args.action == "get":
            config_get(args)
        else:
            config_parser.print_help()
    elif args.command == "plugin":
        if args.action == "list":
            plugin_list(args)
        elif args.action == "enable":
            plugin_enable(args)
        elif args.action == "disable":
            plugin_disable(args)
        elif args.action == "info":
            plugin_info(args)
        else:
            plugin_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
