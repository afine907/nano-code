"""路径权限守卫"""

import fnmatch
from pathlib import Path
from typing import Any

from nano_code.security.guards import BaseGuard
from nano_code.security.permission import PermissionLevel, PermissionResult


class PathGuard(BaseGuard):
    """路径权限守卫

    控制文件系统访问权限：
    - workspace 隔离
    - 路径白名单/黑名单
    - 写入操作确认
    """

    # 文件相关工具
    FILE_TOOLS = frozenset(["read_file", "write_file", "edit_file", "list_directory"])
    # 写入类工具
    WRITE_TOOLS = frozenset(["write_file", "edit_file"])

    def __init__(
        self,
        workspace_root: Path,
        allowed_patterns: list[str] | None = None,
        denied_patterns: list[str] | None = None,
        confirm_patterns: list[str] | None = None,
        allow_outside: bool = False,
    ):
        """初始化路径守卫

        Args:
            workspace_root: 工作空间根目录
            allowed_patterns: 允许的路径模式列表（白名单）
            denied_patterns: 禁止的路径模式列表（黑名单）
            confirm_patterns: 需要确认的路径模式列表
            allow_outside: 是否允许访问工作空间外的路径
        """
        self.workspace_root = workspace_root.resolve()
        self.allowed_patterns = allowed_patterns or ["*"]
        self.denied_patterns = denied_patterns or []
        self.confirm_patterns = confirm_patterns or []
        self.allow_outside = allow_outside

    @property
    def name(self) -> str:
        return "path_guard"

    def check(self, tool_name: str, args: dict[str, Any]) -> PermissionResult:
        """检查文件工具的路径权限"""
        # 只检查文件相关工具
        if tool_name not in self.FILE_TOOLS:
            return PermissionResult(PermissionLevel.ALLOW, tool_name, args)

        path = self._extract_path(args)
        if path is None:
            return PermissionResult(PermissionLevel.ALLOW, tool_name, args)

        file_path = Path(path).resolve()

        # 1. 检查是否在 workspace 内
        if not self.allow_outside:
            if not self._is_in_workspace(file_path):
                return PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"路径 '{path}' 在工作空间外",
                )

        # 获取相对路径用于模式匹配
        relative_path = self._get_relative_path(file_path)

        # 2. 检查黑名单
        for pattern in self.denied_patterns:
            if self._match_pattern(relative_path, pattern):
                return PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"路径 '{path}' 匹配禁止模式 '{pattern}'",
                )

        # 3. 检查白名单
        in_whitelist = any(self._match_pattern(relative_path, p) for p in self.allowed_patterns)
        if not in_whitelist:
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason=f"路径 '{path}' 不在允许列表中",
            )

        # 4. 写入操作检查是否需要确认
        if tool_name in self.WRITE_TOOLS:
            for pattern in self.confirm_patterns:
                if self._match_pattern(relative_path, pattern):
                    return PermissionResult(
                        PermissionLevel.CONFIRM,
                        tool_name,
                        args,
                        reason=f"修改文件 '{path}' 需要确认",
                    )

        return PermissionResult(PermissionLevel.ALLOW, tool_name, args)

    def _extract_path(self, args: dict[str, Any]) -> str | None:
        """从工具参数中提取路径"""
        return args.get("path")

    def _is_in_workspace(self, file_path: Path) -> bool:
        """检查路径是否在工作空间内"""
        try:
            file_path.relative_to(self.workspace_root)
            return True
        except ValueError:
            return False

    def _get_relative_path(self, file_path: Path) -> str:
        """获取相对路径字符串"""
        try:
            return str(file_path.relative_to(self.workspace_root))
        except ValueError:
            return str(file_path)

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """匹配路径模式

        支持 fnmatch 风格的通配符:
        - * 匹配任意字符（不含 /）
        - ** 匹配任意字符（含 /）
        """
        # 将路径标准化为 POSIX 格式
        path_str = path.replace("\\", "/")
        pattern_str = pattern.replace("\\", "/")

        # 使用 pathlib 的 match 方法处理 ** 模式
        if "**" in pattern_str:
            try:
                return Path(path_str).match(pattern_str)
            except (ValueError, TypeError):
                # 回退到简单匹配
                pass

        return fnmatch.fnmatch(path_str, pattern_str)
