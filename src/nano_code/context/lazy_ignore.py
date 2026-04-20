"""Lazy .gitignore 加载管理器

为大型项目提供懒加载 .gitignore 扫描，避免启动时全量扫描。
"""

import fnmatch
from pathlib import Path


class LazyIgnoreManager:
    """懒加载 .gitignore 管理器

    只在启动时加载根目录的 .gitignore，子目录按需加载。

    使用示例:
        >>> manager = LazyIgnoreManager(Path("/project"))
        >>> manager.should_ignore(Path("/project/node_modules"))
        True
        >>> manager.should_ignore(Path("/project/src/main.py"))
        False
    """

    def __init__(self, root: Path):
        """初始化管理器

        Args:
            root: 项目根目录
        """
        self._root = root.resolve()
        self._cache: dict[Path, set[str]] = {}
        self._load_root_ignore()

    def _load_root_ignore(self) -> None:
        """加载根目录的 .gitignore"""
        root_ignore = self._root / ".gitignore"
        if root_ignore.exists():
            self._cache[self._root] = self._parse_gitignore(root_ignore)
        else:
            self._cache[self._root] = set()

    def _parse_gitignore(self, path: Path) -> set[str]:
        """解析 .gitignore 文件

        Args:
            path: .gitignore 文件路径

        Returns:
            忽略模式集合
        """
        patterns: set[str] = set()
        try:
            content = path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith("#"):
                    continue
                # 保存原始模式
                patterns.add(line)
        except Exception:
            pass
        return patterns

    def _get_patterns_for_path(self, path: Path) -> set[str]:
        """获取适用于指定路径的所有忽略模式

        Args:
            path: 要检查的路径

        Returns:
            所有适用的忽略模式
        """
        all_patterns: set[str] = set()

        # 从根目录到路径所在目录，收集所有 .gitignore
        current = path.resolve()
        if current.is_file():
            current = current.parent

        # 遍历从根到当前目录的所有父目录
        dirs_to_check = []
        temp = current
        while temp != self._root and temp.parent != temp:
            dirs_to_check.append(temp)
            temp = temp.parent
        dirs_to_check.append(self._root)
        dirs_to_check.reverse()

        for dir_path in dirs_to_check:
            if dir_path not in self._cache:
                ignore_file = dir_path / ".gitignore"
                if ignore_file.exists():
                    self._cache[dir_path] = self._parse_gitignore(ignore_file)
                else:
                    self._cache[dir_path] = set()
            all_patterns.update(self._cache[dir_path])

        return all_patterns

    def _match_pattern(self, path: Path, pattern: str) -> bool:
        """检查路径是否匹配单个模式

        Args:
            path: 要检查的路径
            pattern: gitignore 模式

        Returns:
            是否匹配
        """
        # 获取相对路径
        try:
            rel_path = path.resolve().relative_to(self._root)
        except ValueError:
            return False

        rel_str = str(rel_path)

        # 处理目录匹配（以 / 结尾）
        if pattern.endswith("/"):
            pattern = pattern[:-1]
            if path.is_dir():
                return fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(
                    rel_str, f"**/{pattern}"
                )
            return False

        # 处理根目录匹配（以 / 开头）
        if pattern.startswith("/"):
            pattern = pattern[1:]
            return fnmatch.fnmatch(rel_str, pattern)

        # 处理递归匹配（**）
        if "**" in pattern:
            # 简化处理，使用 fnmatch
            return fnmatch.fnmatch(rel_str, pattern)

        # 普通模式：匹配任意层级
        return (
            fnmatch.fnmatch(rel_str, pattern)
            or fnmatch.fnmatch(rel_str, f"**/{pattern}")
            or fnmatch.fnmatch(path.name, pattern)
        )

    def should_ignore(self, path: Path) -> bool:
        """检查路径是否应该被忽略

        Args:
            path: 要检查的路径

        Returns:
            是否应该忽略
        """
        # 确保路径在项目内
        try:
            path.resolve().relative_to(self._root)
        except ValueError:
            return False

        # 获取适用的模式
        patterns = self._get_patterns_for_path(path)

        # 检查每个模式
        for pattern in patterns:
            # 处理否定模式（以 ! 开头）
            if pattern.startswith("!"):
                if self._match_pattern(path, pattern[1:]):
                    return False
            else:
                if self._match_pattern(path, pattern):
                    return True

        return False

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._load_root_ignore()
