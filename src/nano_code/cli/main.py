"""CLI 主入口"""

# 加载 .env 文件（必须在其他导入之前）
from dotenv import load_dotenv

load_dotenv()

import os
import sys

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402
from prompt_toolkit import PromptSession  # noqa: E402
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory  # noqa: E402
from prompt_toolkit.history import FileHistory  # noqa: E402
from rich.markdown import Markdown  # noqa: E402

from nano_code import __version__
from nano_code.agent.graph import get_agent_graph  # noqa: E402
from nano_code.agent.state import create_initial_state  # noqa: E402
from nano_code.cli.args import parse_args  # noqa: E402
from nano_code.cli.config_wizard import ConfigWizard  # noqa: E402
from nano_code.cli.console import (  # noqa: E402
    console,
    print_error,
    print_help,
    print_history,
    print_model_info,
    print_session_stats,
    print_status_bar,
    print_success,
    print_user,
    print_welcome,
    session_stats,
    thinking_animation,
)
from nano_code.cli.modes import ModeManager, get_mode_manager  # noqa: E402
from nano_code.core.config import get_settings  # noqa: E402
from nano_code.core.exceptions import NanoCodeError  # noqa: E402
from nano_code.memory.conversation import ConversationMemory  # noqa: E402


class CLI:
    """CLI 主类"""

    def __init__(self):
        self.version = __version__
        self._settings = get_settings()

    def get_help(self) -> str:
        """获取帮助信息"""
        return """
Nano Code CLI - 帮助信息

可用命令:
  /help     - 显示帮助
  /version  - 显示版本
  /status   - 显示状态
  /config   - 重新配置
  /exit     - 退出

快捷键:
  Ctrl+C    - 中断当前操作
  Ctrl+D    - 退出程序
"""

    def run(self, args=None) -> None:
        """运行 CLI

        Args:
            args: 命令行参数（用于测试）
        """
        main(args)


def get_current_model() -> str:
    """获取当前模型名称"""
    settings = get_settings()
    return settings.model


def run_non_interactive(prompt: str, model: str | None = None) -> None:
    """运行非交互模式

    Args:
        prompt: 用户提示
        model: 指定模型（可选）
    """
    from rich.panel import Panel

    # 检查配置
    wizard = ConfigWizard()
    if not wizard.check_config():
        console.print("[red]❌ 请先运行配置向导: nano-code[/red]")
        sys.exit(1)

    # 加载配置
    settings = get_settings()

    # 覆盖模型（如果指定）
    if model:
        os.environ["MODEL"] = model

    console.print(
        Panel.fit(
            f"[bold]Nano Code {__version__}[/bold]\n模型: {model or settings.model}\n模式: 非交互",
            border_style="blue",
        )
    )

    # 初始化 Agent
    graph = get_agent_graph()

    # 执行提示
    console.print(f"\n[bold green]User:[/bold green] {prompt}")
    console.print("\n[bold blue]🤖 Assistant:[/bold blue]")

    try:
        state = create_initial_state(prompt)
        state["messages"] = [{"role": "user", "content": prompt}]

        full_response = ""
        for chunk in graph.stream(state):
            for node_name, node_output in chunk.items():
                if node_name == "thinking" and "messages" in node_output:
                    messages = node_output["messages"]
                    for msg in messages:
                        if isinstance(msg, dict):
                            content = msg.get("content", "")
                        else:
                            content = getattr(msg, "content", "")
                        if content and isinstance(content, str):
                            full_response += content

        if full_response:
            try:
                console.print(Markdown(full_response))
            except Exception:
                console.print(full_response)

    except NanoCodeError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.hint:
            console.print(f"[dim]💡 {e.hint}[/dim]")
        sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ 发生错误: {e}[/red]")
        sys.exit(1)


def run_interactive() -> None:
    """运行交互式会话"""
    # 检查配置，必要时运行向导
    wizard = ConfigWizard()
    if not wizard.check_config():
        console.print("[yellow]检测到首次运行，启动配置向导...[/yellow]")
        if not wizard.run():
            console.print("[red]配置失败，请重试[/red]")
            sys.exit(1)
        # 重新加载配置
        load_dotenv(override=True)

    print_welcome()

    # 初始化记忆
    settings = get_settings()
    storage_path = settings.storage_path / "sessions" / "default.json"
    memory = ConversationMemory(storage_path=storage_path, auto_save=True)

    # 初始化 Agent
    graph = get_agent_graph()

    # 获取当前模型
    current_model = get_current_model()

    # 初始化模式管理器
    mode_manager = get_mode_manager()

    # 初始化 prompt session（增强版）
    session: PromptSession[str] = PromptSession(
        history=FileHistory(str(settings.storage_path / "history.txt")),
        auto_suggest=AutoSuggestFromHistory(),
        multiline=False,
        mouse_support=True,
    )

    console.print("\n[dim]💡 提示: 输入多行内容时，按 Tab 换行，Enter 发送[/dim]")
    console.print("[dim]💡 输入 /help 查看所有命令[/dim]")
    console.print("[dim]💡 输入 /config 重新配置[/dim]")
    console.print("[dim]💡 按 F2 切换 Plan/Build 模式[/dim]\n")

    # 显示初始状态栏
    print_status_bar(current_model, mode=mode_manager.current_mode)
    console.print()

    while True:
        try:
            # 获取用户输入
            user_input = session.prompt("\n> ")

            if not user_input.strip():
                continue

            # 处理命令
            if user_input.startswith("/"):
                should_continue = handle_command(user_input, memory, current_model)
                if not should_continue:
                    break
                continue

            # 打印用户消息
            print_user(user_input)

            # 添加到记忆
            memory.add_message(HumanMessage(content=user_input))

            # 运行 Agent（带动画）
            state = create_initial_state(user_input)
            # 转换 BaseMessage 为 dict 格式
            state["messages"] = [
                {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
                for msg in memory.get_context()
            ]

            # 执行图（流式输出）
            full_response = ""
            processed_messages = 0  # 跟踪已处理的消息数，避免重复
            console.print("\n[bold blue]🤖 Assistant:[/bold blue]")

            try:
                with thinking_animation("Thinking"):
                    for chunk in graph.stream(state):
                        for node_name, node_output in chunk.items():
                            if node_name == "thinking" and "messages" in node_output:
                                messages = node_output["messages"]
                                # 只处理新增的消息
                                for msg in messages[processed_messages:]:
                                    processed_messages += 1
                                    if isinstance(msg, dict):
                                        content = msg.get("content", "")
                                    else:
                                        content = getattr(msg, "content", "")
                                    if content and isinstance(content, str):
                                        full_response += content
                            if node_name == "execute" and "tool_results" in node_output:
                                for result in node_output["tool_results"]:
                                    if result:
                                        from nano_code.cli.console import print_tool_result

                                        print_tool_result(result)

                # 流式完成后尝试渲染 Markdown
                if full_response:
                    try:
                        console.print(Markdown(full_response))
                    except Exception:
                        console.print(f" {full_response}")

                    # 添加到记忆
                    memory.add_message(AIMessage(content=full_response))

            except NanoCodeError as e:
                console.print(f"\n[red]❌ {e.message}[/red]")
                if e.hint:
                    console.print(f"[dim]💡 {e.hint}[/dim]")
                continue

            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ 已取消[/yellow]")
                continue

            # 更新 token 统计
            token_count = memory.token_count()
            session_stats.total_tokens = token_count

            # 显示状态栏
            print_status_bar(current_model, mode=mode_manager.current_mode)

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ 已取消[/yellow]")
            continue
        except EOFError:
            console.print("\n[blue]👋 再见！[/blue]")
            break
        except Exception as e:
            import traceback

            print_error(f"{e}")
            console.print(f"[dim red]{traceback.format_exc()}[/dim red]")


def handle_command(
    command: str,
    memory: ConversationMemory,
    model: str,
    mode_manager: ModeManager | None = None,
) -> bool:
    """处理命令

    Args:
        command: 命令字符串
        memory: 记忆管理器
        model: 当前模型名称
        mode_manager: 模式管理器

    Returns:
        是否继续运行（False 表示退出）
    """
    if mode_manager is None:
        mode_manager = get_mode_manager()

    cmd = command.strip().lower()

    if cmd in ("/exit", "/quit", "/q"):
        print_session_stats(model)
        console.print("[blue]👋 再见！[/blue]")
        return False

    elif cmd == "/clear":
        memory.clear()
        session_stats.reset()
        print_success("已清空记忆")
        print_status_bar(model)

    elif cmd == "/help":
        print_help()

    elif cmd == "/stats":
        print_session_stats(model)

    elif cmd == "/model":
        print_model_info(model)

    elif cmd == "/history":
        print_history(memory.get_context())

    elif cmd == "/reset-stats":
        session_stats.reset()
        print_success("统计已重置")
        print_status_bar(model)

    elif cmd == "/config":
        # 重新运行配置向导
        wizard = ConfigWizard()
        if wizard.run():
            load_dotenv(override=True)
            print_success("配置已更新，重启后生效")

    elif cmd == "/version":
        console.print(f"[bold]Nano Code {__version__}[/bold]")

    else:
        console.print(f"[yellow]⚠️ 未知命令: {command}[/yellow]")
        console.print("[dim]输入 /help 查看可用命令[/dim]")

    return True


def main(args=None) -> None:
    """主入口

    Args:
        args: 命令行参数（用于测试）
    """
    # 解析命令行参数
    parsed_args = parse_args(args)

    # 处理配置文件
    if parsed_args.config:
        load_dotenv(parsed_args.config, override=True)

    # 处理工作目录
    if parsed_args.dir:
        os.chdir(parsed_args.dir)

    # 处理模型覆盖
    if parsed_args.model:
        os.environ["MODEL"] = parsed_args.model

    # 非交互模式
    if parsed_args.prompt or parsed_args.non_interactive:
        if parsed_args.prompt:
            run_non_interactive(parsed_args.prompt, parsed_args.model)
        else:
            console.print("[red]错误: 非交互模式需要使用 -p/--prompt 指定提示[/red]")
            sys.exit(1)
        return

    # 交互模式
    try:
        run_interactive()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
