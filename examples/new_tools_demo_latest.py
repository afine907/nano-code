"""新工具功能演示脚本 - 基于最新master分支"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nano_code.tools.code_analysis_tools import analyze_python_file, find_python_dependencies
from nano_code.tools.git_tools import git_status, git_info
from nano_code.tools.performance_tools import analyze_function_complexity


def demo_code_analysis():
    """演示代码分析工具"""
    print("🔍 代码分析工具演示")
    print("=" * 50)
    
    # 创建一个示例 Python 文件