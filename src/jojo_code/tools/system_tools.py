"""系统信息工具"""

from typing import Any

from langchain_core.tools import tool


@tool("system_info")
def system_info() -> str:
    """获取系统信息

    Returns:
        系统信息
    """
    import platform
    import sys

    info = f"""
系统: {platform.system()} {platform.release()}
版本: {platform.version()}
架构: {platform.machine()}
处理器: {platform.processor()}
Python: {sys.version}
    """.strip()

    return info


@tool("disk_usage")
def disk_usage(path: str = "/") -> dict[str, Any]:
    """获取磁盘使用情况

    Args:
        path: 路径

    Returns:
        磁盘使用情况
    """
    import shutil

    try:
        stat = shutil.disk_usage(path)
        return {
            "path": path,
            "total_gb": round(stat.total / (1024**3), 2),
            "used_gb": round(stat.used / (1024**3), 2),
            "free_gb": round(stat.free / (1024**3), 2),
            "percent": round(stat.used / stat.total * 100, 1),
        }
    except Exception as e:
        return {"error": str(e)}


@tool("memory_usage")
def memory_usage() -> dict[str, Any]:
    """获取内存使用情况

    Returns:
        内存使用情况
    """
    try:
        import psutil

        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent,
        }
    except ImportError:
        return {"error": "需要安装 psutil: pip install psutil"}


@tool("process_list")
def process_list(pattern: str = "", limit: int = 10) -> list[dict[str, Any]]:
    """列出进程

    Args:
        pattern: 进程名过滤
        limit: 返回数量限制

    Returns:
        进程列表
    """
    try:
        import psutil

        processes = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                if pattern and pattern.lower() not in info["name"].lower():
                    continue
                processes.append(
                    {
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu": info.get("cpu_percent", 0),
                        "memory": round(info.get("memory_percent", 0), 1),
                    }
                )
            except (KeyError, TypeError, AttributeError):
                pass

        # 按 CPU 排序
        processes.sort(key=lambda x: x["cpu"], reverse=True)
        return processes[:limit]
    except ImportError:
        return [{"error": "需要安装 psutil"}]


@tool("port_check")
def port_check(port: int = 80, host: str = "localhost") -> dict[str, Any]:
    """检查端口是否开放

    Args:
        port: 端口号
        host: 主机地址

    Returns:
        端口状态
    """
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)

    try:
        result = sock.connect_ex((host, port))
        sock.close()

        return {
            "host": host,
            "port": port,
            "status": "open" if result == 0 else "closed",
        }
    except Exception as e:
        return {"error": str(e)}


__all__ = ["system_info", "disk_usage", "memory_usage", "process_list", "port_check"]
