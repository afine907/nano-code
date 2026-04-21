"""测试 LazyIgnoreManager"""

from pathlib import Path

from jojo_code.context.lazy_ignore import LazyIgnoreManager


class TestLazyIgnoreManager:
    """LazyIgnoreManager 测试"""

    def test_init_with_root(self, tmp_path: Path):
        """测试初始化"""
        manager = LazyIgnoreManager(tmp_path)
        assert manager._root == tmp_path.resolve()

    def test_parse_gitignore(self, tmp_path: Path):
        """测试解析 .gitignore"""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("""
# 注释
node_modules/
*.pyc
.env
!keep.env
""")

        manager = LazyIgnoreManager(tmp_path)
        patterns = manager._parse_gitignore(gitignore)

        assert "node_modules/" in patterns
        assert "*.pyc" in patterns
        assert ".env" in patterns
        assert "!keep.env" in patterns
        # 注释不应该被包含
        assert "# 注释" not in patterns

    def test_should_ignore_simple(self, tmp_path: Path):
        """测试简单的忽略规则"""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n*.pyc\n")

        manager = LazyIgnoreManager(tmp_path)

        # node_modules 目录应该被忽略
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        assert manager.should_ignore(node_modules) is True

        # .pyc 文件应该被忽略
        pyc_file = tmp_path / "test.pyc"
        pyc_file.touch()
        assert manager.should_ignore(pyc_file) is True

        # 普通文件不应该被忽略
        normal_file = tmp_path / "test.py"
        normal_file.touch()
        assert manager.should_ignore(normal_file) is False

    def test_should_ignore_nested(self, tmp_path: Path):
        """测试嵌套目录的忽略规则"""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("dist/\n")

        # 创建嵌套目录
        nested_dist = tmp_path / "src" / "dist"
        nested_dist.mkdir(parents=True)

        manager = LazyIgnoreManager(tmp_path)

        # 嵌套的 dist 目录应该被忽略
        assert manager.should_ignore(nested_dist) is True

    def test_clear_cache(self, tmp_path: Path):
        """测试清空缓存"""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n")

        manager = LazyIgnoreManager(tmp_path)
        assert len(manager._cache) > 0

        manager.clear_cache()
        # 清空后会重新加载根目录
        assert tmp_path.resolve() in manager._cache

    def test_empty_gitignore(self, tmp_path: Path):
        """测试没有 .gitignore 的情况"""
        manager = LazyIgnoreManager(tmp_path)

        # 没有 .gitignore 时，所有文件都不应该被忽略
        test_file = tmp_path / "test.py"
        test_file.touch()
        assert manager.should_ignore(test_file) is False

    def test_path_outside_root(self, tmp_path: Path):
        """测试路径在项目外的情况"""
        manager = LazyIgnoreManager(tmp_path)

        # 路径在项目外不应该被忽略
        outside_path = Path("/tmp/outside_file.txt")
        assert manager.should_ignore(outside_path) is False
