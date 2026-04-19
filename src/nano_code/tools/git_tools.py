"""Git 集成工具 - 基本的 Git 操作支持"""

import subprocess

from langchain_core.tools import tool


@tool
def git_status(path: str = ".") -> str:
    """查看 Git 仓库状态。

    Args:
        path: 仓库路径，默认为当前目录

    Returns:
        Git 状态信息
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], cwd=path, capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return f"Git 错误: {result.stderr.strip()}"

        status_output = result.stdout.strip()
        if not status_output:
            return "工作区干净，没有修改"

        # 解析状态输出
        lines = status_output.split("\n")
        staged = []
        unstaged = []
        untracked = []

        for line in lines:
            if not line.strip():
                continue

            status_code = line[:2]
            filename = line[3:]

            if status_code.startswith("??"):
                untracked.append(filename)
            elif status_code[0] in "MADRC":
                staged.append(f"{status_code} {filename}")
            elif status_code[1] in "MADRC":
                unstaged.append(f"{status_code} {filename}")

        result = "Git 状态:\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        if staged:
            result += f"暂存区 ({len(staged)} 个文件):\n"
            result += "\n".join([f"  {item}" for item in staged]) + "\n"

        if unstaged:
            result += f"未暂存 ({len(unstaged)} 个文件):\n"
            result += "\n".join([f"  {item}" for item in unstaged]) + "\n"

        if untracked:
            result += f"未跟踪 ({len(untracked)} 个文件):\n"
            result += "\n".join([f"  {item}" for item in untracked]) + "\n"

        return result

    except subprocess.TimeoutExpired:
        return "错误: Git 命令执行超时"
    except FileNotFoundError:
        return "错误: Git 未安装或不在 PATH 中"
    except Exception as e:
        return f"错误: {e}"


@tool
def git_diff(path: str = ".", file_path: str | None = None) -> str:
    """查看 Git 差异。

    Args:
        path: 仓库路径，默认为当前目录
        file_path: 特定文件路径，如果提供则只显示该文件的差异

    Returns:
        Git 差异信息
    """
    try:
        cmd = ["git", "diff"]
        if file_path:
            cmd.append(file_path)

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return f"Git 错误: {result.stderr.strip()}"

        diff_output = result.stdout.strip()
        if not diff_output:
            target = file_path or "工作区"
            return f"没有检测到 {target} 的差异"

        # 限制输出长度，避免过长
        lines = diff_output.split("\n")
        if len(lines) > 50:
            diff_output = "\n".join(lines[:50]) + f"\n... (还有 {len(lines) - 50} 行)\n"

        return diff_output

    except subprocess.TimeoutExpired:
        return "错误: Git 命令执行超时"
    except FileNotFoundError:
        return "错误: Git 未安装或不在 PATH 中"
    except Exception as e:
        return f"错误: {e}"


@tool
def git_log(path: str = ".", limit: int = 10) -> str:
    """查看 Git 提交历史。

    Args:
        path: 仓库路径，默认为当前目录
        limit: 显示最近几条提交，默认为 10

    Returns:
        Git 提交历史
    """
    try:
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--oneline", "--graph"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return f"Git 错误: {result.stderr.strip()}"

        log_output = result.stdout.strip()
        if not log_output:
            return "没有提交历史"

        return f"最近 {limit} 条提交:\n{log_output}"

    except subprocess.TimeoutExpired:
        return "错误: Git 命令执行超时"
    except FileNotFoundError:
        return "错误: Git 未安装或不在 PATH 中"
    except Exception as e:
        return f"错误: {e}"


@tool
def git_blame(file_path: str, path: str = ".") -> str:
    """查看文件的 Git blame 信息。

    Args:
        file_path: 要查看的文件路径
        path: 仓库路径，默认为当前目录

    Returns:
        Git blame 信息
    """
    try:
        result = subprocess.run(
            ["git", "blame", "--line-porcelain", file_path],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return f"Git 错误: {result.stderr.strip()}"

        blame_output = result.stdout.strip()
        if not blame_output:
            return f"无法获取 {file_path} 的 blame 信息"

        # 解析 porcelain 格式，提取关键信息
        lines = blame_output.split("\n")
        authors = {}
        recent_commits = set()

        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("author "):
                author = line[7:]
                authors[author] = authors.get(author, 0) + 1
            elif line.startswith("summary "):
                recent_commits.add(line[8:15])  # 简短的提交信息
            elif line == "":  # 空行表示一行结束
                pass
            i += 1

        result = f"Git Blame 分析: {file_path}\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        if authors:
            result += "主要作者:\n"
            sorted_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)
            for author, count in sorted_authors[:5]:  # 显示前 5 个作者
                result += f"  {author}: {count} 行\n"

        result += f"\n总行数: {len([line for line in lines if line == ''])}"

        return result

    except subprocess.TimeoutExpired:
        return "错误: Git 命令执行超时"
    except FileNotFoundError:
        return "错误: Git 未安装或不在 PATH 中"
    except Exception as e:
        return f"错误: {e}"


@tool
def git_branch(path: str = ".") -> str:
    """查看 Git 分支信息。

    Args:
        path: 仓库路径，默认为当前目录

    Returns:
        Git 分支信息
    """
    try:
        # 获取当前分支
        result = subprocess.run(
            ["git", "branch", "--list"], cwd=path, capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return f"Git 错误: {result.stderr.strip()}"

        branches_output = result.stdout.strip()
        if not branches_output:
            return "没有找到分支"

        branches = branches_output.split("\n")
        current_branch = None
        all_branches = []

        for branch in branches:
            branch = branch.strip()
            if branch.startswith("* "):
                current_branch = branch[2:]
                all_branches.append(f"*{current_branch}")
            else:
                all_branches.append(branch)

        result = "Git 分支:\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result += f"当前分支: {current_branch or '未知'}\n\n"
        result += "所有分支:\n"
        result += "\n".join([f"  {branch}" for branch in all_branches])

        # 获取远程分支信息
        try:
            remote_result = subprocess.run(
                ["git", "branch", "-r"], cwd=path, capture_output=True, text=True, timeout=5
            )

            if remote_result.returncode == 0 and remote_result.stdout.strip():
                remote_branches = [
                    b.strip() for b in remote_result.stdout.strip().split("\n") if b.strip()
                ]
                if remote_branches:
                    result += f"\n\n远程分支 ({len(remote_branches)}):\n"
                    result += "\n".join(
                        [f"  {branch}" for branch in remote_branches[:10]]
                    )  # 最多显示 10 个

        except Exception:
            pass  # 忽略远程分支查询错误

        return result

    except subprocess.TimeoutExpired:
        return "错误: Git 命令执行超时"
    except FileNotFoundError:
        return "错误: Git 未安装或不在 PATH 中"
    except Exception as e:
        return f"错误: {e}"


@tool
def git_info(path: str = ".") -> str:
    """获取 Git 仓库的基本信息。

    Args:
        path: 仓库路径，默认为当前目录

    Returns:
        Git 仓库信息
    """
    try:
        # 检查是否在 Git 仓库中
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"], cwd=path, capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            return "错误: 当前目录不是 Git 仓库"

        info = "Git 仓库信息:\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        # 获取远程仓库信息
        try:
            remote_result = subprocess.run(
                ["git", "remote", "-v"], cwd=path, capture_output=True, text=True, timeout=5
            )

            if remote_result.returncode == 0 and remote_result.stdout.strip():
                remotes = remote_result.stdout.strip().split("\n")
                info += "远程仓库:\n"
                for remote in remotes[:3]:  # 最多显示 3 个远程
                    info += f"  {remote}\n"

        except Exception:
            pass

        # 获取提交统计
        try:
            commit_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if commit_result.returncode == 0:
                commit_count = commit_result.stdout.strip()
                info += f"\n总提交数: {commit_count}\n"

        except Exception:
            pass

        # 获取作者统计
        try:
            author_result = subprocess.run(
                ["git", "shortlog", "-s", "-n", "--all"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if author_result.returncode == 0 and author_result.stdout.strip():
                authors = author_result.stdout.strip().split("\n")[:5]  # 前 5 个作者
                info += "\n主要贡献者:\n"
                for author in authors:
                    info += f"  {author}\n"

        except Exception:
            pass

        return info

    except subprocess.TimeoutExpired:
        return "错误: Git 命令执行超时"
    except FileNotFoundError:
        return "错误: Git 未安装或不在 PATH 中"
    except Exception as e:
        return f"错误: {e}"
