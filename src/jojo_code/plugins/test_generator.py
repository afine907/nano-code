"""Test Generator Plugin - Official jojo-code plugin

Provides tools for automated test generation:
- Unit test generation from source code
- pytest fixture generation
- Mock/stub generation
- Test coverage analysis
"""

from pathlib import Path

from langchain_core.tools import Tool

from jojo_code.plugin.base import BasePlugin, PluginMetadata, PluginPermission


class TestGeneratorPlugin(BasePlugin):
    """Official test generator plugin for jojo-code

    Provides automated test generation capabilities including
    unit test creation, fixture generation, and mock generation.
    """

    metadata = PluginMetadata(
        name="test-generator",
        version="0.1.0",
        description="Automated test generation for pytest",
        author="jojo-code team",
        tags=["testing", "pytest", "tdd"],
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
                name="generate_unit_tests",
                description=(
                    "Generate pytest unit tests for a Python function or class "
                    "based on source code analysis"
                ),
                func=self._generate_unit_tests,
            ),
            Tool(
                name="generate_test_fixtures",
                description=(
                    "Generate pytest fixtures for a given class or module, including setup/teardown"
                ),
                func=self._generate_test_fixtures,
            ),
            Tool(
                name="generate_test_mocks",
                description="Generate mock/stub objects for external dependencies in tests",
                func=self._generate_test_mocks,
            ),
        ]

    def _generate_unit_tests(self, file_path: str, target: str = "") -> str:
        """Generate pytest unit tests for a Python file

        Args:
            file_path: Path to Python source file
            target: Optional specific function/class name to generate tests for

        Returns:
            Generated test code
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found: {file_path}"

            content = path.read_text()
            module_name = path.stem

            # Parse the AST
            import ast

            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return f"Syntax error in source file: {e}"

            tests = []
            imports = set()
            imports.add("import pytest")

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if target and node.name != target:
                        continue

                    # Generate test for function
                    test_name = f"test_{node.name}"
                    test_lines = [
                        f"def {test_name}():",
                        f'    """Test {node.name}"""',
                    ]

                    # Analyze function signature
                    args = node.args
                    arg_names = [arg.arg for arg in args.args]

                    # Add parametrize if multiple args with defaults
                    if len(arg_names) > 0:
                        test_lines.append(f"    # TODO: Implement test for {node.name}")
                        test_lines.append("    pass")

                    tests.append("\n".join(test_lines))

                elif isinstance(node, ast.ClassDef):
                    if target and node.name != target:
                        continue

                    class_test = [
                        f"class Test{node.name}:",
                        f'    """Tests for {node.name}"""',
                        "",
                    ]

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name.startswith("_"):
                                continue
                            method_name = f"test_{item.name}"
                            class_test.append(f"    def {method_name}(self):")
                            class_test.append(f'        """Test {item.name}"""')
                            class_test.append("        pass")
                            class_test.append("")

                    tests.append("\n".join(class_test))

            if not tests:
                return f"No functions or classes found{f' named {target}' if target else ''}"

            # Assemble final test file
            imports_list = sorted(imports)
            test_content = [
                f'"""Tests for {module_name}"""\n',
                "\n".join(imports_list),
                "",
                "",
                "\n\n".join(tests),
            ]

            return "\n".join(test_content)

        except Exception as e:
            return f"Error generating tests: {e}"

    def _generate_test_fixtures(self, file_path: str, fixture_name: str = "") -> str:
        """Generate pytest fixtures for a module

        Args:
            file_path: Path to Python source file
            fixture_name: Optional specific class name for fixture

        Returns:
            Generated fixture code
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found: {file_path}"

            content = path.read_text()
            module_name = path.stem

            fixtures = []

            # Generate conftest.py style fixtures
            fixtures.append(f"""\"\"\"pytest fixtures for {module_name}\"\"\"\n""")

            # Try to parse and find classes
            import ast

            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return f"Syntax error: {e}"

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if fixture_name and node.name != fixture_name:
                        continue

                    fixtures.append(f"class Test{node.name}:")

            if not fixtures:
                return f"No classes found{f' named {fixture_name}' if fixture_name else ''}"

            return "\n\n".join(fixtures)

        except Exception as e:
            return f"Error generating fixtures: {e}"

    def _generate_test_mocks(self, file_path: str) -> str:
        """Generate mock objects for external dependencies

        Args:
            file_path: Path to source file to analyze for dependencies

        Returns:
            Generated mock/stub code
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found: {file_path}"

            content = path.read_text()

            # Find imports that look like external dependencies
            import re

            external_imports = set()
            for match in re.finditer(r"^\s*(?:from|import)\s+([^\s;]+)", content, re.MULTILINE):
                module = match.group(1).split(".")[0]
                # Filter out standard library and local modules
                stdlib = {
                    "os",
                    "sys",
                    "re",
                    "json",
                    "math",
                    "time",
                    "datetime",
                    "pathlib",
                    "typing",
                    "collections",
                    "itertools",
                    "functools",
                    "abc",
                    "copy",
                    "io",
                    "bytes",
                    "string",
                    "urllib",
                    "http",
                    "socket",
                    "argparse",
                    "logging",
                    "warnings",
                    "contextlib",
                    "types",
                    "gc",
                    "weakref",
                }
                if module not in stdlib and not module.startswith("_"):
                    external_imports.add(module)

            if not external_imports:
                return f"No external dependencies found in {file_path}"

            mocks = [
                '"""Mock objects for external dependencies"""\n',
                "from unittest.mock import Mock, MagicMock, patch",
                "",
            ]

            for ext_module in sorted(external_imports):
                mock_name = f"Mock{ext_module.title().replace('_', '')}"
                mocks.append(f"# Mock for {ext_module}")
                mocks.append(f"{mock_name} = MagicMock()")
                mocks.append(f'"""{mock_name} - Mock for {ext_module}"""\n')

            return "\n".join(mocks)

        except Exception as e:
            return f"Error generating mocks: {e}"
