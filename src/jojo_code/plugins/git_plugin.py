"""Git Plugin - Official jojo-code plugin

Provides tools for Git operations:
- Git status and info
- Branch management
- Commit history
- Diff viewing
"""

import subprocess
from pathlib import Path

from langchain_core.tools import Tool

from jojo_code.plugin.base import BasePlugin, PluginMetadata, PluginPermission


class GitPlugin(BasePlugin):
    """Official Git plugin for jojo-code

    Provides Git operations for repository management.
    """

    metadata = PluginMetadata(
        name="git",
        version="0.1.0",
        description="Git operations for repository management",
        author="jojo-code team",
        tags=["git", "vcs", "repository"],
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
                name="git_status",
                description=(
                    "Get git repository status including staged, unstaged, and untracked files"
                ),
                func=self._git_status,
            ),
            Tool(
                name="git_branch_list",
                description="List all local and remote branches with current branch highlighted",
                func=self._git_branch_list,
            ),
            Tool(
                name="git_log",
                description="Show recent commit history with author, date, and message",
                func=self._git_log,
            ),
            Tool(
                name="git_diff",
                description="Show changes between commits, branches, or files",
                func=self._git_diff,
            ),
            Tool(
                name="git_stash_list",
                description="List all stashed changes",
                func=self._git_stash_list,
            ),
        ]

    def _run_git(self, *args: str, cwd: str | None = None) -> tuple[str, str, int]:
        """Run a git command

        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        try:
            result = subprocess.run(
                ["git"] + list(args),
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            return result.stdout, result.stderr, result.returncode
        except FileNotFoundError:
            return "", "git not found", 127
        except Exception as e:
            return "", str(e), 1

    def _find_repo_root(self, path: str = ".") -> Path | None:
        """Find the root of the git repository"""
        try:
            cwd = Path(path).resolve()
            result = self._run_git("rev-parse", "--show-toplevel", cwd=str(cwd))
            if result[2] == 0 and result[0].strip():
                return Path(result[0].strip())
        except Exception:
            pass
        return None

    def _git_status(self, path: str = ".") -> str:
        """Get git status

        Args:
            path: Path to repository (default: current directory)

        Returns:
            Status report
        """
        repo_root = self._find_repo_root(path)
        if not repo_root:
            return f"Error: Not a git repository: {path}"

        stdout, stderr, code = self._run_git("status", "--porcelain", cwd=str(repo_root))

        if code != 0:
            return f"Error: {stderr}"

        lines = stdout.strip().split("\n") if stdout.strip() else []

        if not lines:
            return f"✅ Repository clean: {repo_root.name}"

        # Categorize changes
        staged = []
        unstaged = []
        untracked = []

        for line in lines:
            if len(line) < 2:
                continue
            index_status = line[0]
            worktree_status = line[1]
            filename = line[3:].strip()

            if index_status == "?" and worktree_status == "?":
                untracked.append(filename)
            elif index_status in "MADR" or worktree_status in "MADR":
                status = ""
                if index_status == "M":
                    status += "staged "
                if worktree_status == "M":
                    status += "unstaged "
                staged.append(f"{filename} ({status.strip()})" if status else filename)
            elif index_status == "!" or worktree_status == "!":
                pass  # Ignored files

        report = [f"📊 Git Status: {repo_root.name}", "=" * 50]

        if staged:
            report.append(f"\n✅ Staged ({len(staged)}):")
            for f in staged[:20]:
                report.append(f"  {f}")
            if len(staged) > 20:
                report.append(f"  ... and {len(staged) - 20} more")

        if unstaged:
            report.append(f"\n⚠️  Unstaged ({len(unstaged)}):")
            for f in unstaged[:20]:
                report.append(f"  {f}")
            if len(unstaged) > 20:
                report.append(f"  ... and {len(unstaged) - 20} more")

        if untracked:
            report.append(f"\n❓ Untracked ({len(untracked)}):")
            for f in untracked[:20]:
                report.append(f"  {f}")
            if len(untracked) > 20:
                report.append(f"  ... and {len(untracked) - 20} more")

        report.append(f"\nTotal: {len(lines)} change(s)")
        return "\n".join(report)

    def _git_branch_list(self, path: str = ".") -> str:
        """List git branches

        Args:
            path: Path to repository

        Returns:
            Branch list
        """
        repo_root = self._find_repo_root(path)
        if not repo_root:
            return f"Error: Not a git repository: {path}"

        # Get current branch
        stdout, _, code = self._run_git("branch", "--show-current", cwd=str(repo_root))
        current = stdout.strip()

        # Get all branches
        stdout, _, code = self._run_git(
            "branch", "-a", "--format=%(refname:short)|%(upstream:short)", cwd=str(repo_root)
        )

        if code != 0:
            return "Error listing branches"

        lines = stdout.strip().split("\n") if stdout.strip() else []
        branches = []
        for line in lines:
            parts = line.split("|")
            branch = parts[0].strip()
            upstream = parts[1].strip() if len(parts) > 1 else ""
            is_current = branch == current
            marker = " ← current" if is_current else ""
            upstream_info = f" → {upstream}" if upstream else " (no upstream)"
            branches.append(f"{branch}{upstream_info}{marker}")

        report = [f"🌿 Branches in {repo_root.name}", "=" * 50]
        report.append(f"\nCurrent: {current or '(detached)'}")
        report.append(f"\nAll branches ({len(branches)}):")
        for b in branches:
            report.append(f"  {b}")

        return "\n".join(report)

    def _git_log(self, path: str = ".", limit: int = 10) -> str:
        """Show commit history

        Args:
            path: Path to repository
            limit: Number of commits to show

        Returns:
            Commit history
        """
        repo_root = self._find_repo_root(path)
        if not repo_root:
            return f"Error: Not a git repository: {path}"

        stdout, _, code = self._run_git(
            "log",
            f"--max-count={limit}",
            "--pretty=format:%h|%s|%an|%ad",
            "--date=short",
            cwd=str(repo_root),
        )

        if code != 0:
            return "Error reading git log"

        lines = stdout.strip().split("\n") if stdout.strip() else []

        report = [f"📜 Commit History: {repo_root.name}", "=" * 50, ""]

        for line in lines:
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                hash_, subject, author, date = parts[0], parts[1], parts[2], parts[3]
                report.append(f"{hash_} {date} {author}")
                report.append(f"   {subject}")
                report.append("")

        return "\n".join(report)

    def _git_diff(self, path: str = ".", target: str = "") -> str:
        """Show diff

        Args:
            path: Path to repository or file
            target: Optional commit/branch to diff against

        Returns:
            Diff output
        """
        repo_root = self._find_repo_root(path)
        if not repo_root:
            return f"Error: Not a git repository: {path}"

        if target:
            stdout, stderr, code = self._run_git("diff", target, cwd=str(repo_root))
        else:
            stdout, stderr, code = self._run_git("diff", cwd=str(repo_root))

        if code != 0:
            return f"Error: {stderr}"

        if not stdout.strip():
            return "✅ No changes"

        return f"📝 Diff{': ' + target if target else ''}\n{'=' * 50}\n{stdout}"

    def _git_stash_list(self, path: str = ".") -> str:
        """List stashed changes

        Args:
            path: Path to repository

        Returns:
            Stash list
        """
        repo_root = self._find_repo_root(path)
        if not repo_root:
            return f"Error: Not a git repository: {path}"

        stdout, _, code = self._run_git(
            "stash", "list", "--pretty=format:%gd|%s|%an|%ad", "--date=short", cwd=str(repo_root)
        )

        if code != 0:
            return "Error listing stash"

        lines = stdout.strip().split("\n") if stdout.strip() else []

        if not lines or (len(lines) == 1 and not lines[0]):
            return f"✅ No stashed changes in {repo_root.name}"

        report = [f"📦 Stash List: {repo_root.name}", "=" * 50, ""]

        for line in lines:
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) >= 3:
                stash_ref = parts[0]
                subject = parts[1]
                author = parts[2]
                report.append(f"{stash_ref} {author}")
                report.append(f"   {subject}")

        return "\n".join(report)
