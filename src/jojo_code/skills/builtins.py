"""内置 Skills 实现"""

from jojo_code.skills.base import skill
from jojo_code.skills.types import SkillCategory


@skill(
    name="web_search",
    description="搜索网页获取信息",
    category=SkillCategory.WEB,
    tags=["search", "web", "information"],
    examples=["搜索 Python 教程", "查找 AI 相关新闻"],
)
def web_search(query: str) -> str:
    """搜索网页

    Args:
        query: 搜索关键词

    Returns:
        搜索结果
    """
    # 实际实现会调用 web_search 工具
    return f"搜索结果 for: {query}"


@skill(
    name="web_fetch",
    description="获取网页内容",
    category=SkillCategory.WEB,
    tags=["web", "fetch", "content"],
    examples=["获取 https://example.com 的内容"],
)
def web_fetch(url: str) -> str:
    """获取网页内容

    Args:
        url: 网页 URL

    Returns:
        网页内容
    """
    return f"网页内容 from: {url}"


@skill(
    name="read_file",
    description="读取文件内容",
    category=SkillCategory.FILE,
    tags=["file", "read", "io"],
    examples=["读取 /path/to/file.txt"],
)
def read_file(path: str, encoding: str = "utf-8") -> str:
    """读取文件

    Args:
        path: 文件路径
        encoding: 编码

    Returns:
        文件内容
    """
    try:
        with open(path, encoding=encoding) as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


@skill(
    name="write_file",
    description="写入文件内容",
    category=SkillCategory.FILE,
    tags=["file", "write", "io"],
    examples=["写入 content 到 /path/to/file.txt"],
)
def write_file(path: str, content: str, encoding: str = "utf-8") -> str:
    """写入文件

    Args:
        path: 文件路径
        content: 文件内容
        encoding: 编码

    Returns:
        操作结果
    """
    try:
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"


@skill(
    name="run_command",
    description="执行 shell 命令",
    category=SkillCategory.SYSTEM,
    tags=["shell", "command", "system"],
    examples=["执行 ls -la", "运行 python script.py"],
)
def run_command(command: str, shell: bool = True) -> str:
    """执行 shell 命令

    Args:
        command: 命令
        shell: 是否使用 shell

    Returns:
        命令输出
    """
    import subprocess

    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error: {e}"


@skill(
    name="analyze_code",
    description="分析代码质量和结构",
    category=SkillCategory.CODE,
    tags=["code", "analysis", "quality"],
    examples=["分析 main.py 的代码质量"],
)
def analyze_code(file_path: str) -> dict:
    """分析代码

    Args:
        file_path: 代码文件路径

    Returns:
        分析结果
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # 简单分析
        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
        return {
            "file": file_path,
            "lines": len(lines),
            "characters": len(content),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "code_lines": code_lines,
        }
    except Exception as e:
        return {"error": str(e)}


@skill(
    name="format_json",
    description="格式化 JSON 数据",
    category=SkillCategory.DATA,
    tags=["json", "format", "data"],
    examples=['格式化 {"a":1}', "美化 JSON 字符串"],
)
def format_json(json_str: str, indent: int = 2) -> str:
    """格式化 JSON

    Args:
        json_str: JSON 字符串
        indent: 缩进空格数

    Returns:
        格式化后的 JSON
    """
    import json

    try:
        data = json.loads(json_str)
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception as e:
        return f"Error: {e}"


@skill(
    name="validate_json",
    description="验证 JSON 格式",
    category=SkillCategory.DATA,
    tags=["json", "validate", "data"],
    examples=['验证 {"a":1} 是否为有效 JSON'],
)
def validate_json(json_str: str) -> dict:
    """验证 JSON

    Args:
        json_str: JSON 字符串

    Returns:
        验证结果
    """
    import json

    try:
        json.loads(json_str)
        return {"valid": True}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@skill(
    name="calculate",
    description="执行数学计算",
    category=SkillCategory.DATA,
    tags=["math", "calculate", "compute"],
    examples=["计算 2+2", "计算 sqrt(16)"],
)
def calculate(expression: str) -> str:
    """数学计算

    Args:
        expression: 数学表达式

    Returns:
        计算结果
    """
    try:
        # 安全评估数学表达式
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"

        result = eval(expression)  # 注意：生产环境应使用安全的 math parser
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@skill(
    name="translate",
    description="翻译文本",
    category=SkillCategory.SEARCH,
    tags=["translate", "language", "text"],
    examples=["翻译 Hello 为中文", "翻译 你好 为英文"],
)
def translate(text: str, target_lang: str = "en") -> str:
    """翻译文本

    Args:
        text: 待翻译文本
        target_lang: 目标语言

    Returns:
        翻译结果
    """
    # 简单实现，实际应调用翻译 API
    return f"[Translated to {target_lang}]: {text}"


# 导出所有内置 skills
__all__ = [
    "web_search",
    "web_fetch",
    "read_file",
    "write_file",
    "run_command",
    "analyze_code",
    "format_json",
    "validate_json",
    "calculate",
    "translate",
]
