"""工具注册中心"""

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool

from jojo_code.security.permission import PermissionResult
from jojo_code.tools.code_analysis_tools import (
    analyze_python_file,
    check_code_style,
    find_python_dependencies,
    suggest_refactoring,
)
from jojo_code.tools.data_tools import (
    diff_json,
    format_json,
    json_to_yaml,
    minify_json,
    validate_json,
    yaml_to_json,
)
from jojo_code.tools.doc_tools import count_lines, extract_code, read_pdf
from jojo_code.tools.file_tools import edit_file, list_directory, read_file, write_file
from jojo_code.tools.git_tools import git_blame, git_branch, git_diff, git_info, git_log, git_status
from jojo_code.tools.http_tools import curl, http_get, http_post
from jojo_code.tools.performance_tools import (
    analyze_function_complexity,
    benchmark_code_snippet,
    profile_python_file,
    suggest_performance_optimizations,
)
from jojo_code.tools.search_tools import glob_search, grep_search
from jojo_code.tools.shell_tools import run_command
from jojo_code.tools.system_tools import (
    disk_usage,
    memory_usage,
    port_check,
    process_list,
    system_info,
)

# 新增工具
from jojo_code.tools.web_fetch_tools import web_fetch, web_scrape
from jojo_code.tools.web_tools import web_search

# 为了向后兼容，提供别名
Tool = BaseTool
tool = BaseTool  # 装饰器兼容

# 确认回调类型
ConfirmCallback = Callable[[PermissionResult], bool]


class PermissionError(Exception):
    """权限错误"""

    def __init__(self, message: str, result: PermissionResult | None = None):
        super().__init__(message)
        self.result = result


class ToolRegistry:
    """工具注册中心

    管理所有可用工具，提供注册、获取、执行功能。
    支持权限检查和用户确认。
    """

    def __init__(
        self,
        permission_manager: Any = None,
        confirm_callback: ConfirmCallback | None = None,
    ) -> None:
        """初始化工具注册中心

        Args:
            permission_manager: 权限管理器实例
            confirm_callback: 用户确认回调函数
        """
        self._tools: dict[str, BaseTool] = {}
        # 记录工具分类：read/write
        self._tool_categories: dict[str, str] = {}
        self._permission_manager = permission_manager
        self._confirm_callback = confirm_callback
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
            # Web 搜索工具
            web_search,
            # Shell 工具
            run_command,
            # 代码分析工具
            analyze_python_file,
            find_python_dependencies,
            check_code_style,
            suggest_refactoring,
            # Git 工具
            git_status,
            git_diff,
            git_log,
            git_blame,
            git_branch,
            git_info,
            # 性能工具
            profile_python_file,
            analyze_function_complexity,
            suggest_performance_optimizations,
            benchmark_code_snippet,
            # Web 抓取工具
            web_fetch,
            web_scrape,
            # 文档工具
            read_pdf,
            extract_code,
            count_lines,
            # 系统工具
            system_info,
            disk_usage,
            memory_usage,
            process_list,
            port_check,
            # 数据处理工具
            validate_json,
            format_json,
            minify_json,
            yaml_to_json,
            json_to_yaml,
            diff_json,
            # HTTP 工具
            http_get,
            http_post,
            curl,
        ]

        for tool in default_tools:
            self._tools[tool.name] = tool
            # 简单分类：只读工具 vs 写操作工具
            name = getattr(tool, "name", "")
            if name in {"write_file", "edit_file", "run_command"}:
                self._tool_categories[name] = "write"
            else:
                self._tool_categories[name] = "read"

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
            PermissionError: 权限拒绝
        """
        # 权限检查
        if self._permission_manager is not None:
            result = self._permission_manager.check(name, args)

            if result.denied:
                raise PermissionError(f"权限拒绝: {result.reason}", result)

            if result.needs_confirm:
                if self._confirm_callback is not None:
                    approved = self._confirm_callback(result)
                    if not approved:
                        raise PermissionError("用户拒绝执行", result)
                else:
                    raise PermissionError(f"操作需要确认: {result.reason}", result)

        # 执行工具
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

    def is_write_tool(self, name: str) -> bool:
        """判断工具是否为写操作工具

        Args:
            name: 工具名称

        Returns:
            是否是写操作工具
        """
        return self._tool_categories.get(name) == "write"

    def list_tools(self) -> list[str]:
        """列出所有工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def unregister(self, name: str) -> bool:
        """注销工具

        Args:
            name: 工具名称

        Returns:
            是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False


# 全局注册表实例
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表实例（单例）"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
