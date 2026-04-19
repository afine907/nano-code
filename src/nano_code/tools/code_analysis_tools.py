"""代码分析工具 - 静态分析、复杂度评估、依赖检查"""

import ast
from pathlib import Path

from langchain_core.tools import tool


@tool
def analyze_python_file(path: str) -> str:
    """分析 Python 文件的复杂度、函数数量、类数量等指标。

    Args:
        path: Python 文件路径

    Returns:
        代码分析结果，包含函数数量、类数量、复杂度等信息
    """
    file_path = Path(path)
    if not file_path.exists():
        return f"错误: 文件不存在 {path}"

    if file_path.suffix != ".py":
        return f"错误: {path} 不是 Python 文件"

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        # 统计基本信息
        function_count = 0
        class_count = 0
        import_count = 0
        line_count = len(content.splitlines())
        comment_count = content.count("#")

        # 遍历 AST 统计
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_count += 1
            elif isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += 1

        # 计算复杂度（简化版）
        complexity = _calculate_complexity(tree)

        result = f"""文件分析结果: {path}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
基本信息:
  行数: {line_count}
  函数数量: {function_count}
  类数量: {class_count}
  导入数量: {import_count}
  注释行数: {comment_count}
  估算复杂度: {complexity}

代码质量指标:
  平均函数密度: {line_count / max(function_count, 1):.1f} 行/函数
  注释比例: {comment_count / max(line_count, 1) * 100:.1f}%
"""

        return result

    except SyntaxError as e:
        return f"语法错误: {e}"
    except Exception as e:
        return f"分析失败: {e}"


def _calculate_complexity(tree: ast.AST) -> int:
    """计算代码复杂度（简化版圈复杂度）"""
    complexity = 1  # 基础复杂度

    for node in ast.walk(tree):
        # 增加控制流语句的复杂度
        if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
            complexity += 1
        elif isinstance(node, ast.ExceptHandler):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1

    return complexity


@tool
def find_python_dependencies(path: str) -> str:
    """分析 Python 文件或项目的依赖关系。

    Args:
        path: Python 文件或目录路径

    Returns:
        依赖分析结果
    """
    target_path = Path(path)

    if not target_path.exists():
        return f"错误: 路径不存在 {path}"

    dependencies = set()

    if target_path.is_file() and target_path.suffix == ".py":
        # 分析单个文件
        try:
            content = target_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.add(node.module.split(".")[0])

        except Exception as e:
            return f"分析失败: {e}"

    elif target_path.is_dir():
        # 分析目录下的所有 Python 文件
        for py_file in target_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            dependencies.add(alias.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dependencies.add(node.module.split(".")[0])

            except Exception:
                continue  # 跳过无法解析的文件

    else:
        return f"错误: {path} 不是有效的 Python 文件或目录"

    if not dependencies:
        return f"在 {path} 中未找到依赖项"

    # 过滤掉标准库模块（简化版）
    stdlib_modules = {
        "os",
        "sys",
        "pathlib",
        "typing",
        "ast",
        "json",
        "re",
        "datetime",
        "collections",
        "itertools",
        "functools",
        "argparse",
        "logging",
    }

    third_party_deps = sorted(dependencies - stdlib_modules)
    stdlib_deps = sorted(dependencies & stdlib_modules)

    result = f"依赖分析: {path}\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    if third_party_deps:
        result += f"第三方依赖 ({len(third_party_deps)}):\n"
        for dep in third_party_deps:
            result += f"  - {dep}\n"

    if stdlib_deps:
        result += f"\n标准库依赖 ({len(stdlib_deps)}):\n"
        for dep in stdlib_deps:
            result += f"  - {dep}\n"

    return result


@tool
def check_code_style(path: str, rules: str = "basic") -> str:
    """检查代码风格问题。

    Args:
        path: Python 文件路径
        rules: 检查规则，可选 'basic', 'strict'

    Returns:
        代码风格检查结果
    """
    file_path = Path(path)
    if not file_path.exists():
        return f"错误: 文件不存在 {path}"

    if file_path.suffix != ".py":
        return f"错误: {path} 不是 Python 文件"

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        issues = []

        # 基本检查规则
        for i, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > 100:
                issues.append(f"第 {i} 行: 行长度超过 100 字符 ({len(line)})")

            # 检查尾随空格
            if line.rstrip() != line:
                issues.append(f"第 {i} 行: 存在尾随空格")

            # 检查制表符
            if "\t" in line:
                issues.append(f"第 {i} 行: 使用制表符而不是空格")

        # 严格模式额外检查
        if rules == "strict":
            for i, line in enumerate(lines, 1):
                # 检查单行过长函数定义
                if line.strip().startswith("def ") and len(line) > 80:
                    issues.append(f"第 {i} 行: 函数定义过长")

                # 检查缺少空格的运算符
                operators = ["=", "==", "!=", "<", ">", "<=", ">=", "+", "-", "*", "/"]
                for op in operators:
                    if (
                        f"{op}" in line
                        and f" {op} " not in line
                        and op + " " not in line
                        and " " + op not in line
                    ):
                        if not line.strip().startswith("def ") and not line.strip().startswith(
                            "class "
                        ):
                            issues.append(f"第 {i} 行: 运算符 '{op}' 周围可能缺少空格")

        # 检查文件末尾是否有空行
        if lines and lines[-1].strip() != "":
            issues.append("文件末尾缺少空行")

        if not issues:
            return f"代码风格检查通过: {path} (规则: {rules})"

        result = f"代码风格问题 ({len(issues)} 个):\n"
        result += "\n".join(issues[:10])  # 最多显示前 10 个问题

        if len(issues) > 10:
            result += f"\n... 还有 {len(issues) - 10} 个问题"

        return result

    except Exception as e:
        return f"检查失败: {e}"


@tool
def suggest_refactoring(path: str) -> str:
    """分析代码并提供重构建议。

    Args:
        path: Python 文件路径

    Returns:
        重构建议
    """
    file_path = Path(path)
    if not file_path.exists():
        return f"错误: 文件不存在 {path}"

    if file_path.suffix != ".py":
        return f"错误: {path} 不是 Python 文件"

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        suggestions = []

        # 分析函数长度（使用 AST 节点数量作为代理）
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 使用 AST 节点数量作为函数复杂度的代理
                func_complexity = len(list(ast.walk(node)))
                if func_complexity > 30:
                    suggestions.append(
                        f"函数 '{node.name}' 可能过长 (复杂度: {func_complexity})，"
                        "考虑拆分为更小的函数"
                    )

                # 检查参数数量
                if len(node.args.args) > 5:
                    suggestions.append(
                        f"函数 '{node.name}' 参数过多 ({len(node.args.args)} 个)，考虑使用参数对象"
                    )

        # 分析类
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                if len(methods) > 10:
                    suggestions.append(
                        f"类 '{node.name}' 方法过多 ({len(methods)} 个)，考虑职责分离"
                    )

        # 检查重复的字符串常量
        string_constants = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if len(node.value) > 10:  # 只检查较长的字符串
                    string_constants[node.value] = string_constants.get(node.value, 0) + 1

        for const, count in string_constants.items():
            if count > 1:
                suggestions.append(
                    f"字符串常量 '{const[:30]}...' 重复使用 {count} 次，考虑定义为常量"
                )

        if not suggestions:
            return f"重构建议: {path}\n代码结构良好，暂无明显重构需求"

        result = f"重构建议 ({len(suggestions)} 项):\n"
        result += "\n".join([f"• {sugg}" for sugg in suggestions[:5]])  # 最多显示前 5 个建议

        if len(suggestions) > 5:
            result += f"\n... 还有 {len(suggestions) - 5} 个建议"

        return result

    except SyntaxError as e:
        return f"语法错误: {e}"
    except Exception as e:
        return f"分析失败: {e}"
