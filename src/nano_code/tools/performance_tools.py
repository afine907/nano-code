"""性能监控工具 - 代码性能分析和监控"""

import ast
import cProfile
import io
import pstats
import subprocess
import time
from pathlib import Path

from langchain_core.tools import tool


@tool
def profile_python_file(file_path: str, args: str | None = "") -> str:
    """对 Python 文件进行性能分析。

    Args:
        file_path: 要分析的 Python 文件路径
        args: 脚本的命令行参数

    Returns:
        性能分析结果
    """
    target_file = Path(file_path)
    if not target_file.exists():
        return f"错误: 文件不存在 {file_path}"

    if target_file.suffix != ".py":
        return f"错误: {file_path} 不是 Python 文件"

    try:
        # 创建性能分析器
        pr = cProfile.Profile()
        pr.enable()

        # 准备执行环境
        start_time = time.time()

        # 使用 subprocess 运行脚本以获取更准确的性能数据
        cmd = ["python", str(target_file)]
        if args:
            cmd.extend(args.split())

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒超时
        )

        end_time = time.time()
        execution_time = end_time - start_time

        pr.disable()

        # 捕获分析结果
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s)
        ps.sort_stats("cumulative")
        ps.print_stats(20)  # 显示前20个最耗时的函数

        profile_output = s.getvalue()

        # 构建结果
        result_text = f"性能分析结果: {file_path}\n"
        result_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result_text += f"执行时间: {execution_time:.3f} 秒\n"
        result_text += f"退出码: {result.returncode}\n"

        if result.stdout:
            result_text += f"\n脚本输出:\n{result.stdout[:200]}...\n"

        if result.stderr:
            result_text += f"\n错误输出:\n{result.stderr[:200]}...\n"

        result_text += f"\n性能分析数据:\n{profile_output}"

        return result_text

    except subprocess.TimeoutExpired:
        return "错误: 脚本执行超时（30秒）"
    except Exception as e:
        return f"性能分析失败: {e}"


@tool
def analyze_function_complexity(file_path: str) -> str:
    """分析 Python 文件中函数的复杂度。

    Args:
        file_path: Python 文件路径

    Returns:
        函数复杂度分析结果
    """
    target_file = Path(file_path)
    if not target_file.exists():
        return f"错误: 文件不存在 {file_path}"

    if target_file.suffix != ".py":
        return f"错误: {file_path} 不是 Python 文件"

    try:
        content = target_file.read_text(encoding="utf-8")
        tree = ast.parse(content)

        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 计算函数复杂度
                complexity = _calculate_function_complexity(node)

                # 获取函数信息
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "complexity": complexity,
                    "params": len(node.args.args),
                    "has_return": any(isinstance(n, ast.Return) for n in ast.walk(node)),
                    "has_loops": any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node)),
                    "has_conditionals": any(isinstance(n, ast.If) for n in ast.walk(node)),
                }

                functions.append(func_info)

        if not functions:
            return f"在 {file_path} 中未找到函数定义"

        # 按复杂度排序
        functions.sort(key=lambda x: x["complexity"], reverse=True)

        result = f"函数复杂度分析: {file_path}\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for func in functions:
            complexity_level = _get_complexity_level(func["complexity"])
            result += f"函数: {func['name']} (第 {func['line']} 行)\n"
            result += f"  复杂度: {func['complexity']} ({complexity_level})\n"
            result += f"  参数数量: {func['params']}\n"
            result += f"  特性: {', '.join(_get_function_features(func))}\n\n"

        # 提供总体建议
        high_complexity_funcs = [f for f in functions if f["complexity"] > 10]
        if high_complexity_funcs:
            result += f"⚠️  发现 {len(high_complexity_funcs)} 个高复杂度函数，建议重构:\n"
            for func in high_complexity_funcs[:3]:
                result += f"  • {func['name']} (复杂度: {func['complexity']})\n"

        return result

    except SyntaxError as e:
        return f"语法错误: {e}"
    except Exception as e:
        return f"分析失败: {e}"


def _calculate_function_complexity(node: ast.FunctionDef) -> int:
    """计算函数复杂度（圈复杂度）"""
    complexity = 1  # 基础复杂度

    for n in ast.walk(node):
        # 增加控制流语句的复杂度
        if isinstance(n, ast.If):
            complexity += 1
        elif isinstance(n, (ast.For, ast.While)):
            complexity += 2
        elif isinstance(n, ast.Try):
            complexity += len(n.handlers)
        elif isinstance(n, ast.With):
            complexity += 1
        elif isinstance(n, ast.BoolOp):
            complexity += len(n.values) - 1
        elif isinstance(n, ast.Compare):
            complexity += len(n.ops) - 1

    return complexity


def _get_complexity_level(complexity: int) -> str:
    """获取复杂度等级描述"""
    if complexity <= 5:
        return "简单"
    elif complexity <= 10:
        return "中等"
    elif complexity <= 20:
        return "复杂"
    else:
        return "非常复杂"


def _get_function_features(func_info: dict) -> list:
    """获取函数特性列表"""
    features = []
    if func_info["has_return"]:
        features.append("有返回值")
    if func_info["has_loops"]:
        features.append("包含循环")
    if func_info["has_conditionals"]:
        features.append("包含条件语句")
    if func_info["params"] > 3:
        features.append("多参数")

    return features if features else ["简单函数"]


@tool
def suggest_performance_optimizations(file_path: str) -> str:
    """分析代码并提供性能优化建议。

    Args:
        file_path: Python 文件路径

    Returns:
        性能优化建议
    """
    target_file = Path(file_path)
    if not target_file.exists():
        return f"错误: 文件不存在 {file_path}"

    if target_file.suffix != ".py":
        return f"错误: {file_path} 不是 Python 文件"

    try:
        content = target_file.read_text(encoding="utf-8")
        tree = ast.parse(content)
        suggestions = []

        # 检查嵌套循环
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # 检查是否包含嵌套循环
                nested_loops = [
                    n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While)) and n != node
                ]
                if nested_loops:
                    suggestions.append(f"第 {node.lineno} 行: 检测到嵌套循环，考虑优化算法复杂度")

        # 检查列表推导式的使用
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                # 检查复杂的列表推导式
                if len(ast.walk(node)) > 20:  # 简化的复杂度检查
                    suggestions.append(f"第 {node.lineno} 行: 复杂的列表推导式，考虑拆分为普通循环")

        # 检查重复的属性访问
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                attr_name = f"{ast.unparse(node.value)}.{node.attr}"
                # 统计同一属性的访问次数
                access_count = sum(
                    1
                    for n in ast.walk(tree)
                    if isinstance(n, ast.Attribute)
                    and f"{ast.unparse(n.value)}.{n.attr}" == attr_name
                )
                if access_count > 3:
                    suggestions.append(
                        f"第 {node.lineno} 行: 属性 '{attr_name}' 多次访问，考虑缓存到变量"
                    )

        # 检查字符串拼接
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    suggestions.append(f"第 {node.lineno} 行: 字符串拼接，考虑使用 join() 方法")

        # 检查全局变量的使用
        global_vars = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                global_vars.extend(node.names)

        if global_vars:
            suggestions.append(f"使用全局变量: {', '.join(global_vars)}，考虑使用参数传递")

        # 检查大数组的创建
        for node in ast.walk(tree):
            if isinstance(node, ast.List) and len(node.elts) > 100:
                suggestions.append(f"第 {node.lineno} 行: 创建大型列表，考虑使用生成器")

        if not suggestions:
            return f"性能分析: {file_path}\n代码性能良好，暂无明显优化建议"

        result = f"性能优化建议 ({len(suggestions)} 项):\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result += "\n".join([f"• {sugg}" for sugg in suggestions[:5]])  # 最多显示前 5 个建议

        if len(suggestions) > 5:
            result += f"\n... 还有 {len(suggestions) - 5} 个建议"

        return result

    except SyntaxError as e:
        return f"语法错误: {e}"
    except Exception as e:
        return f"分析失败: {e}"


@tool
def benchmark_code_snippet(code: str, iterations: int = 1000) -> str:
    """对代码片段进行简单的基准测试。

    Args:
        code: 要测试的 Python 代码片段
        iterations: 执行次数，默认为 1000

    Returns:
        基准测试结果
    """
    try:
        # 准备测试环境

        # 执行基准测试
        start_time = time.time()

        for _ in range(iterations):
            exec(code)

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        result = "代码基准测试结果:\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result += f"代码片段:\n{code}\n\n"
        result += f"执行次数: {iterations}\n"
        result += f"总时间: {total_time:.6f} 秒\n"
        result += f"平均时间: {avg_time:.6f} 秒\n"
        result += f"每秒执行: {1 / avg_time:.0f} 次\n"

        # 提供简单的性能评估
        if avg_time < 0.001:
            performance = "非常快"
        elif avg_time < 0.01:
            performance = "快速"
        elif avg_time < 0.1:
            performance = "中等"
        else:
            performance = "较慢"

        result += f"\n性能评估: {performance}"

        return result

    except Exception as e:
        return f"基准测试失败: {e}"
