"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest
from dotenv import load_dotenv

# 加载 .env 文件（从项目根目录）
load_dotenv(Path(__file__).parent.parent / ".env")


@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file for testing."""
    file_path = tmp_path / "sample.py"
    file_path.write_text('''
def hello(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(hello("World"))
''')
    return file_path


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project structure for testing."""
    # Create main file
    (tmp_path / "main.py").write_text("""
def greet(name):
    print(f"Hello, {name}!")

if __name__ == "__main__":
    greet("World")
""")

    # Create README
    (tmp_path / "README.md").write_text("# Test Project\n\nA simple test project.")

    # Create subdirectory with files
    subdir = tmp_path / "src" / "utils"
    subdir.mkdir(parents=True)
    (subdir / "helper.py").write_text("""
def add(a, b):
    return a + b
""")

    return tmp_path
