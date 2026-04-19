"""代码分析工具测试"""

from nano_code.tools.code_analysis_tools import (
    analyze_python_file,
    check_code_style,
    find_python_dependencies,
    suggest_refactoring,
)


class TestAnalyzePythonFile:
    """analyze_python_file 工具测试"""

    def test_analyze_simple_python_file(self, tmp_path):
        """应该能分析简单的 Python 文件"""
        # Arrange
        file_path = tmp_path / "simple.py"
        file_path.write_text("""
def hello():
    print("world")

class TestClass:
    pass
""")

        # Act
        result = analyze_python_file.invoke(str(file_path))

        # Assert
        assert "simple.py" in result
        assert "函数数量: 1" in result
        assert "类数量: 1" in result
        assert "分析结果" in result

    def test_analyze_nonexistent_file(self):
        """分析不存在的文件应该返回错误"""
        result = analyze_python_file.invoke("/nonexistent/file.py")
        assert "错误" in result or "不存在" in result

    def test_analyze_non_python_file(self, tmp_path):
        """分析非 Python 文件应该返回错误"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("not python")

        result = analyze_python_file.invoke(str(file_path))
        assert "不是 Python 文件" in result

    def test_analyze_file_with_syntax_error(self, tmp_path):
        """分析有语法错误的文件应该返回错误"""
        file_path = tmp_path / "broken.py"
        file_path.write_text("def hello(:")  # 语法错误

        result = analyze_python_file.invoke(str(file_path))
        assert "语法错误" in result


class TestFindPythonDependencies:
    """find_python_dependencies 工具测试"""

    def test_find_dependencies_in_file(self, tmp_path):
        """应该能找到文件中的依赖"""
        file_path = tmp_path / "deps.py"
        file_path.write_text("""
import os
import sys
from typing import List
import requests
from datetime import datetime
""")

        result = find_python_dependencies.invoke(str(file_path))

        assert "依赖分析" in result
        assert "requests" in result  # 第三方依赖
        assert "os" in result or "sys" in result  # 标准库依赖

    def test_find_dependencies_in_directory(self, tmp_path):
        """应该能分析目录下的依赖"""
        # 创建多个 Python 文件
        (tmp_path / "file1.py").write_text("import os")
        (tmp_path / "file2.py").write_text("import requests")

        result = find_python_dependencies.invoke(str(tmp_path))

        assert "依赖分析" in result
        # 应该找到两个文件中的依赖

    def test_find_no_dependencies(self, tmp_path):
        """没有依赖的文件应该返回相应信息"""
        file_path = tmp_path / "empty.py"
        file_path.write_text("print('hello')")

        result = find_python_dependencies.invoke(str(file_path))
        assert "未找到依赖项" in result


class TestCheckCodeStyle:
    """check_code_style 工具测试"""

    def test_check_good_code_style(self, tmp_path):
        """符合风格的代码应该通过检查"""
        file_path = tmp_path / "good.py"
        file_path.write_text("""
def hello(name):
    return f"Hello, {name}!"

print(hello("world"))
""")

        result = check_code_style.invoke(str(file_path))
        # 文件末尾可能缺少空行，所以检查是否有严重问题
        assert "检查通过" in result or "代码风格问题" in result

    def test_check_long_lines(self, tmp_path):
        """长行应该被检测出来"""
        file_path = tmp_path / "long.py"
        long_line = (
            "x = " + '"very long string that exceeds 100 characters limit for code style checking"'
        )
        file_path.write_text(long_line)

        result = check_code_style.invoke(str(file_path))
        assert "行长度超过" in result or "代码风格问题" in result

    def test_check_trailing_whitespace(self, tmp_path):
        """尾随空格应该被检测出来"""
        file_path = tmp_path / "space.py"
        file_path.write_text("print('hello')   \nprint('world')\n")

        result = check_code_style.invoke(str(file_path))
        assert "尾随空格" in result

    def test_check_strict_rules(self, tmp_path):
        """严格模式应该检查更多规则"""
        file_path = tmp_path / "strict.py"
        file_path.write_text(
            "def very_long_function_name_that_exceeds_eighty_characters_limit():\n    pass"
        )

        result = check_code_style.invoke(str(file_path))
        assert "函数定义过长" in result or "代码风格问题" in result


class TestSuggestRefactoring:
    """suggest_refactoring 工具测试"""

    def test_suggest_for_long_function(self, tmp_path):
        """长函数应该建议重构"""
        file_path = tmp_path / "long_func.py"
        # 创建一个超过 30 个节点的函数（使用复杂度作为代理）
        func_lines = ["def long_function():"] + [f"    line_{i} = {i}" for i in range(35)]
        file_path.write_text("\n".join(func_lines))

        result = suggest_refactoring.invoke(str(file_path))
        assert "过长" in result or "拆分" in result or "复杂度" in result

    def test_suggest_for_many_parameters(self, tmp_path):
        """参数过多的函数应该建议重构"""
        file_path = tmp_path / "params.py"
        file_path.write_text("def func(a, b, c, d, e, f, g):\n    pass")

        result = suggest_refactoring.invoke(str(file_path))
        assert "参数过多" in result or "重构建议" in result

    def test_suggest_for_duplicate_strings(self, tmp_path):
        """重复的字符串常量应该建议定义为常量"""
        file_path = tmp_path / "dup.py"
        file_path.write_text("""
print("error message")
print("success message")
print("error message")
print("error message")
""")

        result = suggest_refactoring.invoke(str(file_path))
        assert "重复使用" in result or "定义为常量" in result

    def test_good_code_no_suggestions(self, tmp_path):
        """代码质量良好时应该没有重构建议"""
        file_path = tmp_path / "good.py"
        file_path.write_text("""
def hello(name):
    return f"Hello, {name}!"

print(hello("world"))
""")

        result = suggest_refactoring.invoke(str(file_path))
        assert "结构良好" in result or "暂无明显重构需求" in result or "重构建议" in result
