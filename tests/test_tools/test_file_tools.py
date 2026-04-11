"""文件工具测试 - TDD 红色阶段先写"""

import pytest

from nano_code.tools.file_tools import edit_file, list_directory, read_file, write_file


class TestReadFile:
    """read_file 工具测试"""

    def test_read_existing_file(self, tmp_path):
        """应该能读取存在的文件"""
        # Arrange
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello World")

        # Act
        result = read_file.invoke({"path": str(file_path)})

        # Assert
        assert result == "Hello World"

    def test_read_nonexistent_file_raises_error(self):
        """读取不存在的文件应该报错"""
        with pytest.raises(FileNotFoundError):
            read_file.invoke({"path": "/nonexistent/file.txt"})

    def test_read_file_with_chinese(self, tmp_path):
        """应该支持 UTF-8 中文"""
        file_path = tmp_path / "chinese.txt"
        file_path.write_text("你好世界", encoding="utf-8")

        result = read_file.invoke({"path": str(file_path)})
        assert result == "你好世界"

    def test_read_file_with_line_numbers(self, tmp_path):
        """应该能返回带行号的内容"""
        file_path = tmp_path / "code.py"
        file_path.write_text("line1\nline2\nline3")

        result = read_file.invoke({"path": str(file_path), "line_numbers": True})

        assert "1" in result
        assert "line1" in result


class TestWriteFile:
    """write_file 工具测试"""

    def test_write_new_file(self, tmp_path):
        """应该能创建新文件"""
        file_path = tmp_path / "new.txt"

        result = write_file.invoke({"path": str(file_path), "content": "New content"})

        assert "成功" in result
        assert file_path.read_text() == "New content"

    def test_overwrite_existing_file(self, tmp_path):
        """应该能覆盖已有文件"""
        file_path = tmp_path / "existing.txt"
        file_path.write_text("Old content")

        write_file.invoke({"path": str(file_path), "content": "New content"})

        assert file_path.read_text() == "New content"

    def test_write_creates_parent_directories(self, tmp_path):
        """应该能创建不存在的父目录"""
        file_path = tmp_path / "subdir" / "deep" / "file.txt"

        result = write_file.invoke({"path": str(file_path), "content": "content"})

        assert "成功" in result
        assert file_path.exists()


class TestEditFile:
    """edit_file 工具测试"""

    def test_edit_replace_text(self, tmp_path):
        """应该能替换指定文本"""
        file_path = tmp_path / "code.py"
        file_path.write_text("def hello():\n    print('world')")

        result = edit_file.invoke(
            {
                "path": str(file_path),
                "old_text": "print('world')",
                "new_text": "print('hello')",
            }
        )

        assert "成功" in result
        assert "print('hello')" in file_path.read_text()

    def test_edit_text_not_found(self, tmp_path):
        """要替换的文本不存在应该报错"""
        file_path = tmp_path / "code.py"
        file_path.write_text("def hello():\n    pass")

        result = edit_file.invoke(
            {
                "path": str(file_path),
                "old_text": "nonexistent",
                "new_text": "replacement",
            }
        )

        assert "未找到" in result or "错误" in result

    def test_edit_only_first_occurrence(self, tmp_path):
        """应该只替换第一次出现的位置"""
        file_path = tmp_path / "code.py"
        file_path.write_text("foo foo foo")

        edit_file.invoke(
            {
                "path": str(file_path),
                "old_text": "foo",
                "new_text": "bar",
            }
        )

        content = file_path.read_text()
        assert content == "bar foo foo"


class TestListDirectory:
    """list_directory 工具测试"""

    def test_list_directory_contents(self, tmp_path):
        """应该列出目录内容"""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.py").write_text("content2")
        (tmp_path / "subdir").mkdir()

        result = list_directory.invoke({"path": str(tmp_path)})

        assert "file1.txt" in result
        assert "file2.py" in result
        assert "subdir" in result

    def test_list_directory_with_types(self, tmp_path):
        """应该区分文件和目录"""
        (tmp_path / "file.txt").write_text("content")
        (tmp_path / "directory").mkdir()

        result = list_directory.invoke({"path": str(tmp_path)})

        # 目录应该有标识
        assert "directory" in result
        assert "file.txt" in result

    def test_list_nonexistent_directory(self):
        """列出不存在的目录应该报错"""
        with pytest.raises(FileNotFoundError):
            list_directory.invoke({"path": "/nonexistent/directory"})
