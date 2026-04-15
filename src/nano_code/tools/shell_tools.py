"""Shell 命令执行工具"""

import subprocess

from langchain_core.tools import tool


@tool
def run_command(
    command: str,
    timeout: int = 30,
    cwd: str | None = None,
) -> str:
    """执行 shell 命令并返回输出。

    Args:
        command: 要执行的命令
        timeout: 超时时间（秒），默认 30
        cwd: 工作目录，默认当前目录

    Returns:
        命令的标准输出，或错误信息

    Raises:
        TimeoutError: 命令执行超时
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
        )

        # 合并 stdout 和 stderr
        output = result.stdout
        if result.returncode != 0:
            if result.stderr:
                output = f"Error (exit code {result.returncode}):\n{result.stderr}"
            elif not output:
                output = f"Error: command failed with exit code {result.returncode}"

        return output.strip() if output.strip() else "(无输出)"

    except subprocess.TimeoutExpired as e:
        raise TimeoutError(f"命令执行超时（{timeout}秒）: {command}") from e
    except Exception as e:
        return f"Error: {e}"


# 为了向后兼容，提供工具类别名
ExecuteCommandTool = run_command
RunScriptTool = run_command  # 使用同一个函数
