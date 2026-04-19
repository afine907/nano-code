"""Project context utilities.

This package provides helpers to detect the project root and to parse a
project's AGENTS.md manifest. It also exposes a simple initializer for
setting up a minimal AGENTS.md when running `/init`.
"""

from .init import init_project_context
from .project import (
    find_project_root,
    load_project_context,
    parse_agents_md,
)

__all__ = [
    "find_project_root",
    "load_project_context",
    "parse_agents_md",
    "init_project_context",
]
