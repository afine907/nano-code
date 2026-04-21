"""JSON-RPC Server main entry point.

Usage:
    python -m jojo_code.server.main

This starts the JSON-RPC server that communicates via stdio.
"""

# 加载 .env 文件（必须在其他导入之前）
from dotenv import load_dotenv

load_dotenv()

from jojo_code.server.handlers import register_handlers
from jojo_code.server.jsonrpc import get_server


def main():
    """运行 JSON-RPC 服务器"""
    # 注册处理器
    register_handlers()

    # 获取服务器并运行
    server = get_server()
    server.run()


if __name__ == "__main__":
    main()
