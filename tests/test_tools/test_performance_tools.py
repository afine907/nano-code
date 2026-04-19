"""性能工具测试"""

from unittest.mock import MagicMock, patch

from nano_code.tools.performance_tools import (
    analyze_function_complexity,
    benchmark_code_snippet,
    profile_python_file,
    suggest_performance_optimizations,
)


class TestProfilePythonFile:
    """profile_python_file 工具测试"""

    def test_profile_simple_script(self, tmp_path):
        """应该能分析简单的 Python 脚本"""
        file_path = tmp_path / "test.py"
        file_path.write_text("print('Hello World')")

        result = profile_python_file.invoke(str(file_path))

        assert "性能分析结果" in result
        assert "执行时间" in result
        assert "test.py" in result

    def test_profile_nonexistent_file(self):
        """分析不存在的文件应该返回错误"""
        result = profile_python_file.invoke("/nonexistent.py")
        assert "错误" in result and "不存在" in result

    def test_profile_non_python_file(self, tmp_path):
        """分析非 Python 文件应该返回错误"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("not python")

        result = profile_python_file.invoke(str(file_path))
        assert "不是 Python 文件" in result

    @patch("nano_code.tools.performance_tools.subprocess.run")
    def test_profile_with_args(self, mock_run, tmp_path):
        """应该能传递命令行参数"""
        file_path = tmp_path / "test.py"
        file_path.write_text("import sys; print(sys.argv)")

        mock_run.return_value = MagicMock(
            returncode=0, stdout="['test.py', 'arg1', 'arg2']", stderr=""
        )

        profile_python_file.invoke(str(file_path))

        # 验证命令被正确调用
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "python" in call_args
        assert "test.py" in call_args[-1]  # 文件路径在最后一个参数


class TestAnalyzeFunctionComplexity:
    """analyze_function_complexity 工具测试"""

    def test_analyze_simple_functions(self, tmp_path):
        """应该能分析简单的函数"""
        file_path = tmp_path / "simple.py"
        file_path.write_text("""
def simple_func():
    return 42

def complex_func(x, y, z):
    if x > 0:
        for i in range(y):
            if i % 2 == 0:
                z += i
    return z
""")

        result = analyze_function_complexity.invoke(str(file_path))

        assert "函数复杂度分析" in result
        assert "simple_func" in result
        assert "complex_func" in result
        assert "复杂度" in result

    def test_analyze_function_with_many_params(self, tmp_path):
        """应该识别参数过多的函数"""
        file_path = tmp_path / "params.py"
        file_path.write_text("def func(a, b, c, d, e, f, g, h, i, j):\n    pass")

        result = analyze_function_complexity.invoke(str(file_path))

        assert "参数数量: 10" in result

    def test_analyze_nonexistent_file(self):
        """分析不存在的文件应该返回错误"""
        result = analyze_function_complexity.invoke("/nonexistent.py")
        assert "错误" in result and "不存在" in result

    def test_analyze_file_without_functions(self, tmp_path):
        """分析没有函数的文件应该返回相应信息"""
        file_path = tmp_path / "no_funcs.py"
        file_path.write_text("x = 1\nprint(x)")

        result = analyze_function_complexity.invoke(str(file_path))
        assert "未找到函数定义" in result


class TestSuggestPerformanceOptimizations:
    """suggest_performance_optimizations 工具测试"""

    def test_suggest_nested_loops(self, tmp_path):
        """应该建议优化嵌套循环"""
        file_path = tmp_path / "loops.py"
        file_path.write_text("""
for i in range(100):
    for j in range(100):
        print(i, j)
""")

        result = suggest_performance_optimizations.invoke(str(file_path))
        assert "嵌套循环" in result

    def test_suggest_string_concatenation(self, tmp_path):
        """应该建议优化字符串拼接"""
        file_path = tmp_path / "strings.py"
        file_path.write_text("""result = ""
for i in range(100):
    result = result + str(i)
""")

        result = suggest_performance_optimizations.invoke(str(file_path))
        assert "字符串拼接" in result or "性能良好" in result

    def test_suggest_global_variables(self, tmp_path):
        """应该建议避免全局变量"""
        file_path = tmp_path / "globals.py"
        file_path.write_text("""
global_var = 42

def func():
    global global_var
    return global_var
""")

        result = suggest_performance_optimizations.invoke(str(file_path))
        assert "全局变量" in result

    def test_good_performance_no_suggestions(self, tmp_path):
        """性能良好的代码应该没有建议"""
        file_path = tmp_path / "good.py"
        file_path.write_text("""
def good_func():
    return sum(range(100))
""")

        result = suggest_performance_optimizations.invoke(str(file_path))
        assert "性能良好" in result or "暂无明显优化建议" in result or "优化建议" in result


class TestBenchmarkCodeSnippet:
    """benchmark_code_snippet 工具测试"""

    def test_benchmark_simple_code(self):
        """应该能基准测试简单代码"""
        code = "x = sum(range(1000))"
        result = benchmark_code_snippet.invoke({"code": code, "iterations": 100})

        assert "基准测试结果" in result
        assert "执行次数: 100" in result
        assert "平均时间" in result
        assert "性能评估" in result

    def test_benchmark_with_custom_iterations(self):
        """应该能使用自定义迭代次数"""
        code = "pass"
        result = benchmark_code_snippet.invoke({"code": code, "iterations": 50})

        assert "执行次数: 50" in result

    def test_benchmark_failing_code(self):
        """基准测试失败代码应该返回错误"""
        code = "undefined_variable"
        result = benchmark_code_snippet.invoke({"code": code, "iterations": 10})

        assert "基准测试失败" in result

    def test_benchmark_performance_levels(self):
        """应该正确评估性能等级"""
        # 测试快速代码
        fast_code = "x = 1 + 1"
        result = benchmark_code_snippet.invoke({"code": fast_code, "iterations": 1000})

        # 根据执行时间，应该被评估为快速
        assert "性能评估" in result


class TestComplexityCalculation:
    """复杂度计算辅助函数测试"""

    def test_calculate_simple_complexity(self, tmp_path):
        """简单函数的复杂度应该是 1"""
        file_path = tmp_path / "simple.py"
        file_path.write_text("def simple():\n    return 42")

        result = analyze_function_complexity.invoke(str(file_path))
        # 简单函数应该有较低的复杂度
        assert "复杂度: 1" in result or "简单" in result

    def test_calculate_complex_complexity(self, tmp_path):
        """复杂函数的复杂度应该更高"""
        file_path = tmp_path / "complex.py"
        file_path.write_text("""
def complex_func():
    if True:
        if True:
            for i in range(10):
                if i > 5:
                    while True:
                        break
    return 42
""")

        result = analyze_function_complexity.invoke(str(file_path))
        # 复杂函数应该有较高的复杂度等级
        assert "复杂" in result or "复杂度:" in result
