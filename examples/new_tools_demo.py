"""新工具功能演示脚本"""

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
    demo_file = Path("demo_code.py")
    demo_file.write_text("""
import os
import sys
from typing import List, Dict

def calculate_stats(data: List[float]) -> Dict[str, float]:
    if not data:
        return {}
    
    total = sum(data)
    count = len(data)
    mean = total / count
    
    sorted_data = sorted(data)
    mid = count // 2
    if count % 2 == 0:
        median = (sorted_data[mid-1] + sorted_data[mid]) / 2
    else:
        median = sorted_data[mid]
    
    return {
        'mean': mean,
        'median': median,
        'total': total,
        'count': count
    }

class DataProcessor:
    def __init__(self, filename: str):
        self.filename = filename
        self.data = []
    
    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                for line in f:
                    try:
                        self.data.append(float(line.strip()))
                    except ValueError:
                        continue
    
    def process(self):
        self.load_data()
        return calculate_stats(self.data)

if __name__ == "__main__":
    processor = DataProcessor("data.txt")
    stats = processor.process()
    print(stats)
""")
    
    print("1. 分析 Python 文件:")
    result = analyze_python_file.invoke(str(demo_file))
    print(result)
    
    print("\n2. 查找依赖关系:")
    result = find_python_dependencies.invoke(str(demo_file))
    print(result)
    
    print("\n3. 分析函数复杂度:")
    result = analyze_function_complexity.invoke(str(demo_file))
    print(result)
    
    # 清理
    demo_file.unlink()


def demo_git_tools():
    """演示 Git 工具"""
    print("\n📝 Git 工具演示")
    print("=" * 50)
    
    print("1. Git 状态检查:")
    result = git_status.invoke(".")
    print(result)
    
    print("\n2. Git 仓库信息:")
    result = git_info.invoke(".")
    print(result)


def main():
    """主演示函数"""
    print("🚀 Nano-Code 新工具功能演示")
    print("=" * 60)
    
    try:
        demo_code_analysis()
        demo_git_tools()
        
        print("\n✅ 演示完成！")
        print("\n新增工具包括:")
        print("• 代码分析工具: analyze_python_file, find_python_dependencies, check_code_style, suggest_refactoring")
        print("• Git 集成工具: git_status, git_diff, git_log, git_blame, git_branch, git_info")
        print("• 性能分析工具: profile_python_file, analyze_function_complexity, suggest_performance_optimizations, benchmark_code_snippet")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        print("请确保在 nano-code 项目根目录运行此脚本")


if __name__ == "__main__":
    main()