"""工具注册中心"""

from typing import Any

from langchain_core.tools import BaseTool

from nano_code.tools.file_tools import edit_file, list_directory, read_file, write_file
from nano_code.tools.search_tools import glob_search, grep_search
from nano_code.tools.shell_tools import run_command


class ToolRegistry:
    """工具注册中心

    管理所有可用工具，提供注册、获取、执行功能。
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """注册默认工具集"""
        default_tools = [
            # 文件工具
            read_file,
            write_file,
            edit_file,
            list_directory,
            # 搜索工具
            grep_search,
            glob_search,
            # Shell 工具
            run_command,
        ]

        for tool in default_tools:
            self._tools[tool.name] = tool

    def register(self, tool: BaseTool) -> None:
        """注册新工具

        Args:
            tool: LangChain 工具实例
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，不存在则返回 None
        """
        return self._tools.get(name)

    def execute(self, name: str, args: dict[str, Any]) -> str:
        """执行工具

        Args:
            name: 工具名称
            args: 工具参数

        Returns:
            工具执行结果

        Raises:
            ValueError: 工具不存在
        """
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")

        result = tool.invoke(args)
        return str(result)

    def get_langchain_tools(self) -> list[BaseTool]:
        """获取所有 LangChain 格式的工具列表

        Returns:
            工具列表
        """
        return list(self._tools.values())

    def list_tools(self) -> list[str]:
        """列出所有工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())


# 全局注册表实例
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表实例（单例）"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
