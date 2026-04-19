"""Git 工具测试"""

import subprocess
from unittest.mock import MagicMock, patch

from nano_code.tools.git_tools import git_blame, git_branch, git_diff, git_info, git_log, git_status


class TestGitStatus:
    """git_status 工具测试"""

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_status_clean(self, mock_run):
        """测试干净的工作区"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_status.invoke({"path": "."})
        assert "工作区干净" in result

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_status_with_changes(self, mock_run):
        """测试有修改的工作区"""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=" M file.py\n?? new_file.py\n", stderr=""
        )

        result = git_status.invoke({"path": "."})
        assert "暂存区" in result or "未跟踪" in result

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_status_error(self, mock_run):
        """测试 Git 错误"""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="fatal: not a git repository"
        )

        result = git_status.invoke({"path": "."})
        assert "Git 错误" in result


class TestGitDiff:
    """git_diff 工具测试"""

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_diff_no_changes(self, mock_run):
        """测试没有差异"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_diff.invoke({"path": ".", "file_path": None})
        assert "没有检测到" in result and "差异" in result

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_diff_with_changes(self, mock_run):
        """测试有差异的情况"""
        diff_content = "--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,3 @@"
        mock_run.return_value = MagicMock(returncode=0, stdout=diff_content, stderr="")

        result = git_diff.invoke({"path": ".", "file_path": None})
        assert result == diff_content

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_diff_specific_file(self, mock_run):
        """测试特定文件的差异"""
        mock_run.return_value = MagicMock(returncode=0, stdout="diff content", stderr="")

        git_diff.invoke({"path": ".", "file_path": "file.py"})

        # 验证调用了正确的命令
        mock_run.assert_called_with(
            ["git", "diff", "file.py"], cwd=".", capture_output=True, text=True, timeout=10
        )


class TestGitLog:
    """git_log 工具测试"""

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_log_with_commits(self, mock_run):
        """测试有提交历史的情况"""
        log_content = "* abc123 Fix bug\n* def456 Add feature"
        mock_run.return_value = MagicMock(returncode=0, stdout=log_content, stderr="")

        result = git_log.invoke({"path": ".", "limit": 5})
        assert "最近 5 条提交" in result
        assert "Fix bug" in result
        assert "Add feature" in result

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_log_no_commits(self, mock_run):
        """测试没有提交历史的情况"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_log.invoke({"path": ".", "limit": 10})
        assert "没有提交历史" in result


class TestGitBlame:
    """git_blame 工具测试"""

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_blame_success(self, mock_run):
        """测试成功的 blame 分析"""
        blame_content = """abc123 author Alice
author Alice
summary Fix bug
	print('hello')

def456 author Bob
author Bob
summary Add feature
	print('world')
"""
        mock_run.return_value = MagicMock(returncode=0, stdout=blame_content, stderr="")

        result = git_blame.invoke({"file_path": "file.py", "path": "."})
        assert "Git Blame 分析" in result
        assert "Alice" in result
        assert "Bob" in result

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_blame_error(self, mock_run):
        """测试 blame 错误"""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="fatal: no such path")

        result = git_blame.invoke({"file_path": "nonexistent.py", "path": "."})
        assert "Git 错误" in result


class TestGitBranch:
    """git_branch 工具测试"""

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_branch_with_branches(self, mock_run):
        """测试有分支的情况"""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="* main\n  feature\n  develop", stderr=""
        )

        result = git_branch.invoke({"path": "."})
        assert "Git 分支" in result
        assert "当前分支: main" in result
        assert "main" in result
        assert "feature" in result
        assert "develop" in result

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_branch_no_branches(self, mock_run):
        """测试没有分支的情况"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_branch.invoke({"path": "."})
        assert "没有找到分支" in result


class TestGitInfo:
    """git_info 工具测试"""

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_info_success(self, mock_run):
        """测试成功的仓库信息获取"""

        # Mock 多个命令的返回值
        def mock_subprocess_run(cmd, *args, **kwargs):
            if cmd == ["git", "rev-parse", "--git-dir"]:
                return MagicMock(returncode=0, stdout=".git", stderr="")
            elif cmd == ["git", "remote", "-v"]:
                return MagicMock(
                    returncode=0,
                    stdout="origin\thttps://github.com/user/repo.git\t(fetch)",
                    stderr="",
                )
            elif cmd == ["git", "rev-list", "--count", "HEAD"]:
                return MagicMock(returncode=0, stdout="42", stderr="")
            elif cmd == ["git", "shortlog", "-s", "-n", "--all"]:
                return MagicMock(returncode=0, stdout="42\tAlice\n10\tBob", stderr="")
            else:
                return MagicMock(returncode=1, stdout="", stderr="unknown command")

        mock_run.side_effect = mock_subprocess_run

        result = git_info.invoke({"path": "."})
        assert "Git 仓库信息" in result
        assert "远程仓库" in result
        assert "总提交数: 42" in result
        assert "主要贡献者" in result

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_info_not_repo(self, mock_run):
        """测试非 Git 仓库的情况"""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="fatal: not a git repository"
        )

        result = git_info.invoke({"path": "."})
        assert "不是 Git 仓库" in result


class TestGitToolsErrorHandling:
    """Git 工具错误处理测试"""

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_command_timeout(self, mock_run):
        """测试命令超时"""
        mock_run.side_effect = subprocess.TimeoutExpired(["git"], 10)

        result = git_status.invoke({"path": "."})
        assert "超时" in result

    @patch("nano_code.tools.git_tools.subprocess.run")
    def test_git_command_file_not_found(self, mock_run):
        """测试 Git 未安装"""
        mock_run.side_effect = FileNotFoundError()

        result = git_status.invoke({"path": "."})
        assert "Git 未安装" in result
