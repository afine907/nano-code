"""搜索工具测试"""

from nano_code.tools.search_tools import glob_search, grep_search


class TestGrepSearch:
    """grep 正则搜索测试"""

    def test_search_simple_pattern(self, tmp_path):
        """应该能搜索简单文本"""
        (tmp_path / "file1.py").write_text("def hello():\n    pass")
        (tmp_path / "file2.py").write_text("def world():\n    pass")

        result = grep_search.invoke({"pattern": "def", "path": str(tmp_path)})

        assert "hello" in result
        assert "world" in result

    def test_search_with_file_pattern(self, tmp_path):
        """应该支持文件类型过滤"""
        (tmp_path / "code.py").write_text("TODO: fix this")
        (tmp_path / "readme.md").write_text("TODO: document")

        result = grep_search.invoke(
            {
                "pattern": "TODO",
                "path": str(tmp_path),
                "file_pattern": "*.py",
            }
        )

        assert "code.py" in result
        assert "readme.md" not in result

    def test_search_returns_line_numbers(self, tmp_path):
        """应该返回行号"""
        (tmp_path / "code.py").write_text("line1\nTODO: fix\nline3")

        result = grep_search.invoke({"pattern": "TODO", "path": str(tmp_path)})

        assert "2" in result  # 行号

    def test_search_regex_pattern(self, tmp_path):
        """应该支持正则表达式"""
        (tmp_path / "code.py").write_text("def hello():\n    pass\ndef world():")

        result = grep_search.invoke({"pattern": r"def \w+", "path": str(tmp_path)})

        assert "hello" in result
        assert "world" in result

    def test_search_no_matches(self, tmp_path):
        """没有匹配时应该返回空或提示"""
        (tmp_path / "code.py").write_text("no matches here")

        result = grep_search.invoke({"pattern": "TODO", "path": str(tmp_path)})

        assert result == "" or "未找到" in result


class TestGlobSearch:
    """glob 文件名匹配测试"""

    def test_find_python_files(self, tmp_path):
        """应该能找到所有 Python 文件"""
        (tmp_path / "main.py").write_text("")
        (tmp_path / "utils.py").write_text("")
        (tmp_path / "readme.md").write_text("")

        result = glob_search.invoke({"pattern": "*.py", "path": str(tmp_path)})

        assert "main.py" in result
        assert "utils.py" in result
        assert "readme.md" not in result

    def test_find_nested_files(self, tmp_path):
        """应该能递归搜索子目录"""
        subdir = tmp_path / "src" / "utils"
        subdir.mkdir(parents=True)
        (subdir / "helper.py").write_text("")

        result = glob_search.invoke({"pattern": "**/*.py", "path": str(tmp_path)})

        assert "helper.py" in result

    def test_find_no_matches(self, tmp_path):
        """没有匹配时应该返回空"""
        (tmp_path / "readme.md").write_text("")

        result = glob_search.invoke({"pattern": "*.py", "path": str(tmp_path)})

        assert result == "" or "未找到" in result

    def test_find_with_multiple_patterns(self, tmp_path):
        """应该能搜索嵌套目录中的文件"""
        (tmp_path / "main.py").write_text("")
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "test.py").write_text("")

        result = glob_search.invoke({"pattern": "**/*.py", "path": str(tmp_path)})

        assert "main.py" in result
        assert "test.py" in result
