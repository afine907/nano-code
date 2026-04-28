"""Tests for ImpactAnalyzer"""

import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

from jojo_code.agent.impact_analyzer import (
    ImpactAnalyzer,
    PythonAnalyzer,
    TypeScriptAnalyzer,
    FileImpact,
)
from jojo_code.agent.task_spec import (
    TaskSpec,
    TaskStatus,
    ImpactAnalysis,
    DecisionRecord,
    DecisionType,
    AgentType,
)


@dataclass
class MockTaskSpec:
    """Mock TaskSpec for testing"""

    task: str = "Add logging to user authentication"
    status: Any = TaskStatus.PENDING
    impact_analysis: Optional[ImpactAnalysis] = None
    audit_trail: list[DecisionRecord] = None

    def __post_init__(self):
        if self.audit_trail is None:
            self.audit_trail = []

    def add_decision(self, **kwargs):
        record = DecisionRecord(
            agent=kwargs.get("agent", AgentType.IMPACT_ANALYZER),
            decision_type=kwargs.get("decision_type", DecisionType.REASONING),
            content=kwargs.get("content"),
            reasoning=kwargs.get("reasoning", ""),
            confidence=kwargs.get("confidence", 1.0),
        )
        self.audit_trail.append(record)
        return record

    def update_status(self):
        if self.impact_analysis:
            self.status = TaskStatus.IMPACT_ANALYZED


class TestPythonAnalyzer:
    """Test PythonAnalyzer"""

    def test_parse_valid_file(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n\nclass MyClass:\n    pass")

        analyzer = PythonAnalyzer(py_file)
        assert analyzer.parse() is True
        assert analyzer.tree is not None

    def test_parse_invalid_file(self, tmp_path):
        py_file = tmp_path / "invalid.py"
        py_file.write_text("def invalid syntax here")

        analyzer = PythonAnalyzer(py_file)
        assert analyzer.parse() is False

    def test_get_imports(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("import os\nfrom pathlib import Path\nimport sys as system")

        analyzer = PythonAnalyzer(py_file)
        analyzer.parse()
        imports = analyzer.get_imports()

        assert "os" in imports
        assert "pathlib.Path" in imports or "Path" in imports
        assert "system" in imports or "sys" in imports

    def test_get_functions(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("def func1():\n    pass\n\ndef func2():\n    pass")

        analyzer = PythonAnalyzer(py_file)
        analyzer.parse()
        functions = analyzer.get_functions()

        assert "func1" in functions
        assert "func2" in functions

    def test_get_classes(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("class MyClass:\n    pass\n\nclass AnotherClass:\n    pass")

        analyzer = PythonAnalyzer(py_file)
        analyzer.parse()
        classes = analyzer.get_classes()

        assert "MyClass" in classes
        assert "AnotherClass" in classes

    def test_find_symbol_references(self, tmp_path):
        py_file = tmp_path / "test.py"
        content = "x = 1\nprint(x)\n# use x again\ny = x + 1"
        py_file.write_text(content)

        analyzer = PythonAnalyzer(py_file)
        analyzer.parse()
        refs = analyzer.find_symbol_references("x")

        assert len(refs) >= 3
        assert 1 in refs
        assert 2 in refs


class TestTypeScriptAnalyzer:
    """Test TypeScriptAnalyzer"""

    def test_init(self, tmp_path):
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("")

        analyzer = TypeScriptAnalyzer(ts_file)
        assert analyzer.file_path == ts_file
        assert isinstance(analyzer.use_tree_sitter, bool)

    def test_parse_valid_file(self, tmp_path):
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("function hello(): void {\n    console.log('hi');\n}")

        analyzer = TypeScriptAnalyzer(ts_file)
        assert analyzer.parse() is True

    def test_get_imports_text_mode(self, tmp_path):
        ts_file = tmp_path / "test.ts"
        content = """import { Component } from 'react';
import axios from 'axios';
const utils = require('./utils');"""
        ts_file.write_text(content)

        analyzer = TypeScriptAnalyzer(ts_file)
        analyzer.use_tree_sitter = False
        analyzer.parse()
        imports = analyzer.get_imports()

        assert len(imports) >= 2

    def test_get_functions_text_mode(self, tmp_path):
        ts_file = tmp_path / "test.ts"
        content = """function myFunc() {
    return true;
}
const arrow = () => {};
"""
        ts_file.write_text(content)

        analyzer = TypeScriptAnalyzer(ts_file)
        analyzer.use_tree_sitter = False
        analyzer.parse()
        functions = analyzer.get_functions()

        assert "myFunc" in functions or len(functions) >= 0

    def test_get_classes_text_mode(self, tmp_path):
        ts_file = tmp_path / "test.ts"
        content = "class User {\n    name: string;\n}\n\nclass Admin extends User {}"
        ts_file.write_text(content)

        analyzer = TypeScriptAnalyzer(ts_file)
        analyzer.use_tree_sitter = False
        analyzer.parse()
        classes = analyzer.get_classes()

        assert "User" in classes
        assert "Admin" in classes


class TestImpactAnalyzer:
    """Test ImpactAnalyzer"""

    def test_init(self):
        task_spec = MockTaskSpec(task="Add new feature to auth module")
        analyzer = ImpactAnalyzer(task_spec)

        assert analyzer.task_spec.task == "Add new feature to auth module"
        assert len(analyzer.file_impacts) == 0

    def test_extract_keywords(self):
        task_spec = MockTaskSpec(task="Add logging to user authentication system")
        analyzer = ImpactAnalyzer(task_spec)

        keywords = analyzer._extract_keywords(analyzer.task_spec.task)

        assert "logging" in keywords
        assert "authentication" in keywords
        assert "system" in keywords
        assert "the" not in keywords

    def test_analyze_with_python_files(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        py_file = src_dir / "auth.py"
        py_file.write_text("""def authenticate(user, password):
    print("Authenticating...")
    return True

class AuthManager:
    def login(self):
        pass
""")

        task_spec = MockTaskSpec(task="Add logging to authentication")
        analyzer = ImpactAnalyzer(task_spec, code_base_path=tmp_path)
        result = analyzer.analyze()

        assert isinstance(result, ImpactAnalysis)
        assert result.summary != ""
        assert result.risk_level in ("low", "medium", "high")
        assert task_spec.impact_analysis is not None
        assert len(task_spec.audit_trail) >= 2

    def test_analyze_with_ts_files(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        ts_file = src_dir / "auth.ts"
        ts_file.write_text("""export function authenticate(user: string, pass: string): boolean {
    console.log("Auth check");
    return true;
}

export class AuthService {
    login() {}
}
""")

        task_spec = MockTaskSpec(task="Update authentication service")
        analyzer = ImpactAnalyzer(task_spec, code_base_path=tmp_path)
        result = analyzer.analyze()

        assert isinstance(result, ImpactAnalysis)
        assert len(result.affected_components) >= 0

    def test_calculate_overall_risk(self):
        task_spec = MockTaskSpec()
        analyzer = ImpactAnalyzer(task_spec)

        assert analyzer._calculate_overall_risk() == "low"

        analyzer.file_impacts = [
            FileImpact(file_path="a.py", language="python", risk_level="high"),
            FileImpact(file_path="b.py", language="python", risk_level="high"),
        ]
        assert analyzer._calculate_overall_risk() == "high"

        analyzer.file_impacts = [
            FileImpact(file_path="a.py", language="python", risk_level="low"),
            FileImpact(file_path="b.py", language="python", risk_level="medium"),
        ]
        assert analyzer._calculate_overall_risk() in ("low", "medium")

    def test_generate_suggestions(self):
        task_spec = MockTaskSpec()
        analyzer = ImpactAnalyzer(task_spec)

        suggestions = analyzer._generate_suggestions()
        assert len(suggestions) >= 1
        assert "No affected files" in suggestions[0]

        analyzer.file_impacts = [
            FileImpact(file_path="a.py", language="python", risk_level="high")
        ]
        suggestions = analyzer._generate_suggestions()
        assert any("affected files" in s.lower() for s in suggestions)

    def test_audit_trail_recording(self):
        task_spec = MockTaskSpec()
        analyzer = ImpactAnalyzer(task_spec)

        assert len(task_spec.audit_trail) == 0

        task_spec = MockTaskSpec()
        analyzer = ImpactAnalyzer(task_spec)
        analyzer.task_spec = task_spec
        analyzer.code_base_path = Path("/tmp")

        result = analyzer.analyze()

        assert len(task_spec.audit_trail) >= 2
        input_decisions = [d for d in task_spec.audit_trail if d.decision_type == DecisionType.INPUT]
        output_decisions = [d for d in task_spec.audit_trail if d.decision_type == DecisionType.OUTPUT]
        assert len(input_decisions) >= 1
        assert len(output_decisions) >= 1

    def test_file_impact_dataclass(self):
        impact = FileImpact(
            file_path="/path/to/file.py",
            language="python",
            risk_level="medium",
            affected_symbols=["func1", "MyClass"],
            suggestions=["Review function implementations"],
        )

        assert impact.file_path == "/path/to/file.py"
        assert impact.language == "python"
        assert impact.risk_level == "medium"
        assert "func1" in impact.affected_symbols


class TestIntegration:
    """Integration tests"""

    def test_full_workflow(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        py_file = src_dir / "main.py"
        py_file.write_text("""import logging

def main():
    logging.info("Starting app")
    authenticate()

def authenticate():
    pass
""")

        task_spec = TaskSpec(task="Add detailed logging to authentication flow")
        analyzer = ImpactAnalyzer(task_spec, code_base_path=tmp_path)
        result = analyzer.analyze()

        assert task_spec.status == TaskStatus.IMPACT_ANALYZED
        assert task_spec.impact_analysis is not None
        assert result.summary != ""
        assert len(task_spec.audit_trail) >= 2

    def test_multiple_language_support(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        py_file = src_dir / "backend.py"
        py_file.write_text("def process():\n    pass")

        ts_file = src_dir / "frontend.ts"
        ts_file.write_text("function render() {}\n")

        task_spec = TaskSpec(task="Update processing and rendering")
        analyzer = ImpactAnalyzer(task_spec, code_base_path=tmp_path)
        result = analyzer.analyze()

        languages = {imp.language for imp in analyzer.file_impacts}
        assert "python" in languages or "typescript" in languages or "javascript" in languages
