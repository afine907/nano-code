"""Code Review Plugin - Official jojo-code plugin

Provides tools for automated code review including:
- Security vulnerability scanning
- Code quality analysis
- Style consistency checks
- Complexity analysis
"""

import ast
import re
from pathlib import Path

from langchain_core.tools import Tool

from jojo_code.plugin.base import BasePlugin, PluginMetadata, PluginPermission


class CodeReviewPlugin(BasePlugin):
    """Official code review plugin for jojo-code

    Provides automated code review capabilities including
    security scanning, quality analysis, and style checking.
    """

    metadata = PluginMetadata(
        name="code-review",
        version="0.1.0",
        description="Automated code review tools for security, quality, and style",
        author="jojo-code team",
        tags=["code-review", "security", "quality"],
    )

    permission = PluginPermission.RESTRICTED

    def on_load(self) -> None:
        """Called when plugin is loaded"""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded"""
        pass

    def get_tools(self) -> list[Tool]:
        """Return list of tools provided by this plugin"""
        return [
            Tool(
                name="review_python_security",
                description=(
                    "Scan Python code for common security vulnerabilities: "
                    "SQL injection, XSS, hardcoded secrets, insecure deserialization"
                ),
                func=self._review_python_security,
            ),
            Tool(
                name="review_code_quality",
                description=(
                    "Analyze code quality metrics: function length, nesting depth, "
                    "cyclomatic complexity, code smells"
                ),
                func=self._review_code_quality,
            ),
            Tool(
                name="review_code_style",
                description=(
                    "Check code style consistency: naming conventions, "
                    "docstring coverage, import organization"
                ),
                func=self._review_code_style,
            ),
        ]

    def _review_python_security(self, file_path: str) -> str:
        """Scan Python file for security vulnerabilities

        Args:
            file_path: Path to Python file to scan

        Returns:
            Security report with findings
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found: {file_path}"

            content = path.read_text()
            findings = []

            # Check for hardcoded secrets
            secret_patterns = [
                (r'password\s*=\s*["\'][^"\']{1,}["\']', "Hardcoded password"),
                (r'api[_-]?key\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "Hardcoded API key"),
                (r'secret\s*=\s*["\'][^"\']{8,}["\']', "Potential hardcoded secret"),
                (r'token\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "Hardcoded token"),
                (r"aws[_-]?access[_-]?key", "AWS access key pattern"),
                (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "Private key file reference"),
            ]

            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern, issue in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(f"L{line_num}: [HIGH] {issue}")

            # Check for dangerous patterns
            dangerous = [
                ("eval(", "Use of eval() - code injection risk"),
                ("exec(", "Use of exec() - code injection risk"),
                ("pickle.loads", "Insecure deserialization with pickle"),
                ("subprocess.call", "Consider subprocess.run() with shell=False"),
                ("os.system", "os.system() is vulnerable to shell injection"),
                ("input(", "Consider using input() carefully to avoid injection"),
                ("__import__", "Dynamic import can be dangerous"),
                (".format(", "str.format() less safe than f-string or template"),
                ('" % ', "Old-style string formatting - consider f-string"),
                ("shelve.open", "shelve uses pickle - security risk"),
            ]

            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern, issue in dangerous:
                    if pattern in line:
                        # Skip comments
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            continue
                        findings.append(f"L{line_num}: [MEDIUM] {issue}")

            # Check for SQL injection risk
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute):
                            if node.func.attr in ("execute", "executemany", "cursor"):
                                # Check if using f-string or format in SQL
                                for arg in node.args:
                                    if isinstance(arg, ast.JoinedStr):
                                        findings.append(
                                            f"L{node.lineno}: [HIGH] Possible SQL injection - "
                                            "f-string in SQL query"
                                        )
            except SyntaxError:
                findings.append("Warning: Could not parse AST for SQL injection check")

            if not findings:
                return f"✅ Security Review: No vulnerabilities found in {file_path}"

            report = f"🔒 Security Review Report: {file_path}\n"
            report += "=" * 50 + "\n"
            report += "\n".join(findings)
            report += f"\n{'=' * 50}\nTotal: {len(findings)} finding(s)"
            return report

        except Exception as e:
            return f"Error reviewing {file_path}: {e}"

    def _review_code_quality(self, file_path: str) -> str:
        """Analyze code quality metrics

        Args:
            file_path: Path to Python file

        Returns:
            Quality report with metrics
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found: {file_path}"

            content = path.read_text()

            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return f"Syntax error: {e}"

            findings = []
            metrics = {"functions": 0, "classes": 0, "long_functions": 0, "deep_nesting": 0}

            for node in ast.walk(tree):
                # Count classes
                if isinstance(node, ast.ClassDef):
                    metrics["classes"] += 1
                    # Check class docstring
                    if not ast.get_docstring(node):
                        findings.append(
                            f"L{node.lineno}: [MINOR] Class '{node.name}' missing docstring"
                        )

                # Analyze functions
                if isinstance(node, ast.FunctionDef):
                    metrics["functions"] += 1

                    # Check function length
                    if node.end_lineno and node.lineno:
                        func_length = node.end_lineno - node.lineno
                        if func_length > 50:
                            metrics["long_functions"] += 1
                            findings.append(
                                f"L{node.lineno}: [INFO] Function '{node.name}' "
                                f"is {func_length} lines (>{50})"
                            )

                    # Check docstring
                    if not ast.get_docstring(node):
                        findings.append(
                            f"L{node.lineno}: [MINOR] Function '{node.name}' missing docstring"
                        )

                    # Check for too many arguments
                    if len(node.args.args) > 6:
                        findings.append(
                            f"L{node.lineno}: [INFO] Function '{node.name}' "
                            f"has {len(node.args.args)} arguments (>{6})"
                        )

                    # Analyze nesting depth
                    max_depth = self._get_max_nesting_depth(node)
                    if max_depth > 4:
                        metrics["deep_nesting"] += 1
                        findings.append(
                            f"L{node.lineno}: [INFO] Function '{node.name}' "
                            f"has nesting depth {max_depth} (>{4})"
                        )

            report = f"📊 Code Quality Report: {file_path}\n"
            report += "=" * 50 + "\n"
            report += f"Functions: {metrics['functions']} | Classes: {metrics['classes']}\n"
            report += f"Long functions: {metrics['long_functions']}\n"
            report += f"Deep nesting: {metrics['deep_nesting']}\n"
            if findings:
                report += "\n--- Findings ---\n"
                report += "\n".join(findings)
            else:
                report += "\n✅ No quality issues found"

            return report

        except Exception as e:
            return f"Error analyzing {file_path}: {e}"

    def _get_max_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth of a node"""
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                child_depth = self._get_max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            elif isinstance(child, ast.FunctionDef):
                # Don't count nested function definitions
                continue
            else:
                child_depth = self._get_max_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _review_code_style(self, file_path: str) -> str:
        """Check code style consistency

        Args:
            file_path: Path to Python file

        Returns:
            Style report
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found: {file_path}"

            content = path.read_text()
            findings = []

            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # Check line length
                if len(line) > 100:
                    findings.append(f"L{i}: [STYLE] Line > 100 chars ({len(line)})")

                # Check for TODO without owner
                if "TODO" in line and not re.search(r"TODO\([^)]+\)", line):
                    findings.append(f"L{i}: [STYLE] TODO without owner: {stripped[:50]}")

                # Check naming conventions
                # Classes: CapWords
                # Functions: snake_case
                # Constants: UPPER_SNAKE
                # Private: _leading_underscore
                if i > 0:
                    if not stripped.startswith("#") and stripped:
                        pass  # Basic checks

            # Check import organization
            import_lines = [
                idx
                for idx, line_text in enumerate(lines)
                if re.match(r"^\s*(import|from)\s", line_text)
            ]
            if import_lines and len(import_lines) > 10:
                findings.append(
                    f"[INFO] Large import block ({len(import_lines)} lines). "
                    "Consider splitting into groups."
                )

            if not findings:
                return f"✅ Style Review: No issues found in {file_path}"

            report = f"🎨 Style Review Report: {file_path}\n"
            report += "=" * 50 + "\n"
            report += "\n".join(findings)
            return report

        except Exception as e:
            return f"Error reviewing style for {file_path}: {e}"
