from pathlib import Path


def _ensure_agents_md(root: Path) -> Path:
    """Ensure AGENTS.md exists in the given root. If missing, create a minimal skeleton.
    Returns the path to AGENTS.md.
    """
    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        return agents_path
    # Minimal skeleton content
    skeleton = (
        "# AGENTS\n\n"
        "## agent-a\n"
        "- sample capability A1\n"
        "- sample capability A2\n\n"
        "## agent-b\n"
        "- sample capability B1\n"
    )
    agents_path.write_text(skeleton, encoding="utf-8")
    return agents_path


def init_project_context(start: Path | None = None) -> tuple[Path | None, dict]:
    """Initialize project context in the given start location.

    - Detect project root using existing markers (.git, pyproject.toml).
    - If AGENTS.md is missing, create a minimal skeleton.
    - Return a tuple of (agents_md_path, context_dict).
    """
    from .project import find_project_root

    root = find_project_root(start)
    if root is None:
        # Fallback to current working directory when no root can be detected
        root = Path.cwd()

    agents_path = _ensure_agents_md(root)
    # Build a small context map for consumers
    context = {
        "root": str(root),
        "agents_md": str(agents_path),
    }
    return agents_path, context
