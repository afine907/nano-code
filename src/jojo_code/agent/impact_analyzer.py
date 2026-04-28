"""Impact Analyzer - 无外部依赖的代码影响分析器

分析任务对代码库的影响范围，支持多语言(Python/TypeScript/JavaScript)。
使用纯 Python 实现，不依赖 ctags/grep 等外部工具。
"""

import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .task_spec import (
    AgentType,
    DecisionRecord,
    DecisionType,
    ImpactAnalysis,
    TaskSpec,
)

logger = logging.getLogger(__name__)


@dataclass
class FileImpact:
    """单个文件的影响分析"""

    file_path: str
    language: str
    risk_level: str = "low"
    affected_symbols: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PythonAnalyzer:
    """Python 代码分析器 - 使用 ast 模块"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content: str = ""
        self.tree: ast.AST | None = None

    def parse(self) -> bool:
        """解析 Python 文件"""
        try:
            self.content = self.file_path.read_text(encoding="utf-8")
            self.tree = ast.parse(self.content, filename=str(self.file_path))
            return True
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse {self.file_path}: {e}")
            return False

    def get_imports(self) -> list[str]:
        """获取导入的模块"""
        if not self.tree:
            return []
        imports = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports

    def get_functions(self) -> list[str]:
        """获取函数定义"""
        if not self.tree:
            return []
        functions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                functions.append(node.name)
        return functions

    def get_classes(self) -> list[str]:
        """获取类定义"""
        if not self.tree:
            return []
        classes = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes

    def find_symbol_references(self, symbol: str) -> list[int]:
        """查找符号引用行号"""
        if not self.content:
            return []
        lines = self.content.split("\n")
        references = []
        for i, line in enumerate(lines, 1):
            if symbol in line:
                references.append(i)
        return references


class TypeScriptAnalyzer:
    """TypeScript/JavaScript 分析器 - 支持 tree-sitter 或文本匹配"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content: str = ""
        self.use_tree_sitter: bool = False
        self._check_tree_sitter()

    def _check_tree_sitter(self):
        """检查 tree-sitter 是否可用"""
        try:
            import tree_sitter  # noqa: F401
            self.use_tree_sitter = True
        except ImportError:
            self.use_tree_sitter = False
            logger.info("tree-sitter not available, falling back to text matching")

    def parse(self) -> bool:
        """解析 TypeScript/JavaScript 文件"""
        try:
            self.content = self.file_path.read_text(encoding="utf-8")
            if self.use_tree_sitter:
                return self._parse_with_tree_sitter()
            return True
        except UnicodeDecodeError as e:
            logger.warning(f"Failed to parse {self.file_path}: {e}")
            return False

    def _parse_with_tree_sitter(self) -> bool:
        """使用 tree-sitter 解析"""
        try:
            from tree_sitter import Language, Parser

            self.tree = Parser()
            self.tree.set_language(Language("typescript"))
            self.tree.parse(bytes(self.content, "utf-8"))
            return True
        except Exception as e:
            logger.warning(f"tree-sitter parse failed: {e}")
            self.use_tree_sitter = False
            return True

    def get_imports(self) -> list[str]:
        """获取导入的模块"""
        imports = []
        if self.use_tree_sitter:
            return self._get_imports_tree_sitter()
        return self._get_imports_text()

    def _get_imports_tree_sitter(self) -> list[str]:
        """使用 tree-sitter 获取导入"""
        imports = []
        try:
            root = self.tree.root_node
            for node in root.named_children:
                if node.type == "import_statement":
                    for child in node.named_children:
                        if child.type == "import_clause":
                            imports.append(child.text.decode())
                elif node.type == "import_declaration":
                    for child in node.named_children:
                        if child.type == "import_clause":
                            imports.append(child.text.decode())
        except Exception:
            pass
        return imports

    def _get_imports_text(self) -> list[str]:
        """使用文本匹配获取导入"""
        import_patterns = [
            r"import\s+{([^}]+)}\s+from\s+['\"]([^'\"]+)['\"]",
            r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
            r"import\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        ]
        imports = []
        for pattern in import_patterns:
            for match in re.finditer(pattern, self.content):
                imports.append(match.group(1) if "require" not in pattern else match.group(1))
        return imports

    def get_functions(self) -> list[str]:
        """获取函数定义"""
        if self.use_tree_sitter:
            return self._get_functions_tree_sitter()
        return self._get_functions_text()

    def _get_functions_tree_sitter(self) -> list[str]:
        """使用 tree-sitter 获取函数"""
        functions = []
        try:
            root = self.tree.root_node
            for node in root.named_children:
                if node.type in ("function_declaration", "method_definition"):
                    for child in node.named_children:
                        if child.type == "identifier":
                            functions.append(child.text.decode())
        except Exception:
            pass
        return functions

    def _get_functions_text(self) -> list[str]:
        """使用文本匹配获取函数"""
        patterns = [
            r"function\s+(\w+)\s*\(",
            r"const\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>)",
            r"(\w+)\s*:\s*(?:function|\([^)]*\)\s*=>)",
        ]
        functions = []
        for pattern in patterns:
            for match in re.finditer(pattern, self.content):
                functions.append(match.group(1))
        return functions

    def get_classes(self) -> list[str]:
        """获取类定义"""
        if self.use_tree_sitter:
            return self._get_classes_tree_sitter()
        return self._get_classes_text()

    def _get_classes_tree_sitter(self) -> list[str]:
        """使用 tree-sitter 获取类"""
        classes = []
        try:
            root = self.tree.root_node
            for node in root.named_children:
                if node.type == "class_declaration":
                    for child in node.named_children:
                        if child.type == "identifier":
                            classes.append(child.text.decode())
        except Exception:
            pass
        return classes

    def _get_classes_text(self) -> list[str]:
        """使用文本匹配获取类"""
        pattern = r"class\s+(\w+)"
        return [match.group(1) for match in re.finditer(pattern, self.content)]

    def find_symbol_references(self, symbol: str) -> list[int]:
        """查找符号引用行号"""
        if not self.content:
            return []
        lines = self.content.split("\n")
        references = []
        for i, line in enumerate(lines, 1):
            if symbol in line:
                references.append(i)
        return references


class ImpactAnalyzer:
    """代码影响分析器

    分析任务对代码库的影响范围，支持 Python/TypeScript/JavaScript。
    使用纯 Python 实现，不依赖外部工具。
    """

    def __init__(
        self,
        task_spec: TaskSpec,
        code_base_path: Path | None = None,
    ):
        self.task_spec = task_spec
        self.code_base_path = code_base_path or Path.cwd()
        self.file_impacts: list[FileImpact] = []
        self.affected_files: list[str] = []

    def analyze(self) -> ImpactAnalysis:
        """执行影响分析"""
        self.task_spec.add_decision(
            agent=AgentType.IMPACT_ANALYZER,
            decision_type=DecisionType.INPUT,
            content=f"Starting impact analysis for task: {self.task_spec.task}",
            reasoning="Begin analysis of code base impact",
        )

        python_files = list(self.code_base_path.rglob("*.py"))
        ts_files = list(self.code_base_path.rglob("*.ts")) + list(
            self.code_base_path.rglob("*.tsx")
        )
        js_files = list(self.code_base_path.rglob("*.js")) + list(
            self.code_base_path.rglob("*.jsx")
        )

        task_keywords = self._extract_keywords(self.task_spec.task)

        for py_file in python_files[:50]:
            impact = self._analyze_python_file(py_file, task_keywords)
            if impact.affected_symbols:
                self.file_impacts.append(impact)
                self.affected_files.append(str(py_file))

        for ts_file in (ts_files + js_files)[:50]:
            impact = self._analyze_ts_file(ts_file, task_keywords)
            if impact.affected_symbols:
                self.file_impacts.append(impact)
                self.affected_files.append(str(ts_file))

        risk_level = self._calculate_overall_risk()
        suggestions = self._generate_suggestions()
        summary = self._generate_summary()

        impact_analysis = ImpactAnalysis(
            summary=summary,
            affected_components=self.affected_files,
            risk_level=risk_level,
            suggestions=suggestions,
            metadata={
                "files_analyzed": len(python_files) + len(ts_files) + len(js_files),
                "files_affected": len(self.affected_files),
                "task_keywords": task_keywords,
            },
        )

        self.task_spec.impact_analysis = impact_analysis
        self.task_spec.update_status()

        self.task_spec.add_decision(
            agent=AgentType.IMPACT_ANALYZER,
            decision_type=DecisionType.OUTPUT,
            content=impact_analysis.to_dict(),
            reasoning=f"Analysis complete. Risk level: {risk_level}",
            confidence=0.85,
        )

        return impact_analysis

    def _extract_keywords(self, task: str) -> list[str]:
        """从任务描述中提取关键词"""
        words = re.findall(r"\b\w{3,}\b", task.lower())
        stop_words = {
            "the", "and", "for", "with", "this", "that", "from", "will", "what",
            "when", "where", "which", "have", "has", "been", "were", "are", "was",
        }
        return [w for w in words if w not in stop_words]

    def _analyze_python_file(self, file_path: Path, keywords: list[str]) -> FileImpact:
        """分析 Python 文件"""
        analyzer = PythonAnalyzer(file_path)
        impact = FileImpact(file_path=str(file_path), language="python")

        if not analyzer.parse():
            return impact

        content_lower = analyzer.content.lower()
        for keyword in keywords:
            if keyword in content_lower:
                refs = analyzer.find_symbol_references(keyword)
                if refs:
                    impact.affected_symbols.append(keyword)
                    impact.metadata[f"{keyword}_lines"] = refs[:10]

        impact.affected_symbols.extend(analyzer.get_functions()[:5])
        impact.affected_symbols.extend(analyzer.get_classes()[:5])

        if len(impact.affected_symbols) > 5:
            impact.risk_level = "high"
        elif len(impact.affected_symbols) > 2:
            impact.risk_level = "medium"

        return impact

    def _analyze_ts_file(self, file_path: Path, keywords: list[str]) -> FileImpact:
        """分析 TypeScript/JavaScript 文件"""
        analyzer = TypeScriptAnalyzer(file_path)
        ext = file_path.suffix
        lang = "typescript" if ext in (".ts", ".tsx") else "javascript"
        impact = FileImpact(file_path=str(file_path), language=lang)

        if not analyzer.parse():
            return impact

        content_lower = analyzer.content.lower()
        for keyword in keywords:
            if keyword in content_lower:
                refs = analyzer.find_symbol_references(keyword)
                if refs:
                    impact.affected_symbols.append(keyword)
                    impact.metadata[f"{keyword}_lines"] = refs[:10]

        impact.affected_symbols.extend(analyzer.get_functions()[:5])
        impact.affected_symbols.extend(analyzer.get_classes()[:5])

        if len(impact.affected_symbols) > 5:
            impact.risk_level = "high"
        elif len(impact.affected_symbols) > 2:
            impact.risk_level = "medium"

        return impact

    def _calculate_overall_risk(self) -> str:
        """计算整体风险等级"""
        if not self.file_impacts:
            return "low"
        risk_scores = {"low": 0, "medium": 1, "high": 2}
        total_score = sum(risk_scores.get(f.risk_level, 0) for f in self.file_impacts)
        avg_score = total_score / len(self.file_impacts)
        if avg_score >= 1.5:
            return "high"
        elif avg_score >= 0.5:
            return "medium"
        return "low"

    def _generate_suggestions(self) -> list[str]:
        """生成建议"""
        suggestions = []
        if not self.file_impacts:
            suggestions.append("No affected files found. Consider reviewing task scope.")
            return suggestions
        suggestions.append(f"Review {len(self.affected_files)} affected files")
        suggestions.append("Run tests for affected components")
        if any(f.risk_level == "high" for f in self.file_impacts):
            suggestions.append("High risk changes detected - consider incremental rollout")
        return suggestions

    def _generate_summary(self) -> str:
        """生成分析摘要"""
        return (
            f"Impact analysis complete. "
            f"Found {len(self.affected_files)} affected files "
            f"across {len(set(f.language for f in self.file_impacts))} languages."
        )


__all__ = [
    "ImpactAnalyzer",
    "PythonAnalyzer",
    "TypeScriptAnalyzer",
    "FileImpact",
]
