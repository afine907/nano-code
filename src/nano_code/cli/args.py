"""命令行参数解析"""

import argparse
from pathlib import Path

from nano_code import __version__


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器

    Returns:
        配置好的 ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="nano-code",
        description=(
            "A mini coding agent built with LangGraph - Learn Agent architecture through practice"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  nano-code                    启动交互式会话
  nano-code --version          显示版本
  nano-code --help             显示帮助
  nano-code -p "分析这个项目"   非交互模式执行
  nano-code --model gpt-4o     指定模型
  nano-code --config .env      使用指定配置文件
        """,
    )

    # 版本
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # 非交互模式
    parser.add_argument(
        "-p",
        "--prompt",
        type=str,
        help="非交互模式：执行单个提示后退出",
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="非交互模式运行",
    )

    # 模型选择
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="指定使用的模型 (例如: gpt-4o, gpt-4o-mini)",
    )

    # 配置文件
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="指定配置文件路径",
    )

    # 工作目录
    parser.add_argument(
        "-d",
        "--dir",
        type=Path,
        help="指定工作目录",
    )

    # 调试模式
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式",
    )

    return parser


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数

    Args:
        args: 参数列表，默认使用 sys.argv

    Returns:
        解析后的参数
    """
    parser = create_parser()
    return parser.parse_args(args)
