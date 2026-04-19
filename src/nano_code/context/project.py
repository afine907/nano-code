from pathlib import Path

ROOT_MARKERS = [".git", "pyproject.toml"]


def _markers_in_dir(dir_path: Path) -> bool:
    for marker in ROOT_MARKERS:
        if (dir_path / marker).exists():
            return True
    return False


def find_project_root(start: Path | None = None) -> Path | None:
    """Locate the project root by walking up from `start` to filesystem root.

    The search stops when a directory containing any of ROOT_MARKERS is found.
    If no marker is found up to the filesystem root, return None.
    """
    cur = Path(start) if start is not None else Path.cwd()
    # If start is a file, use its parent directory
    if cur.is_file():
        cur = cur.parent

    for _ in range(0, 1000):  # safe upper bound for traversal
        if _markers_in_dir(cur):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def parse_agents_md(agents_md_path: Path) -> dict[str, list[str]]:
    """Parse AGENTS.md into a simple mapping of agent sections to bullet points.

    Expected simple format (very permissive):
      ## AgentName
      - capability 1
      - capability 2

    Returns a dict like: {"AgentName": ["capability 1", "capability 2"]}
    If parsing fails or file is not Markdown-like, returns an empty dict.
    """
    result: dict[str, list[str]] = {}
    if not agents_md_path.exists():
        return result
    try:
        lines = [ln.rstrip("\n") for ln in agents_md_path.read_text(encoding="utf-8").splitlines()]
    except Exception:
        return result

    current_agent: str | None = None
    for line in lines:
        line_stripped = line.strip()
        # Detect a section header (## AgentName)
        if line_stripped.startswith("## "):
            current_agent = line_stripped.lstrip("# ").strip()
            if current_agent:
                result.setdefault(current_agent, [])
            continue
        # Bullet item under an agent
        if current_agent and (line_stripped.startswith("- ") or line_stripped.startswith("* ")):
            bullet = line_stripped.lstrip("- ").lstrip("* ").strip()
            if bullet:
                result[current_agent].append(bullet)
    return result


def load_project_context(start: Path | None = None) -> dict[str, object]:
    """Load basic project context from the repository root.

    Returns a dict with keys:
      - root: path to project root or None
      - agents: dict parsed from AGENTS.md (or empty dict)
    """
    root = find_project_root(start)
    agents_path = (root / "AGENTS.md") if root else None
    agents = parse_agents_md(agents_path) if agents_path else {}
    return {"root": str(root) if root else None, "agents": agents}
