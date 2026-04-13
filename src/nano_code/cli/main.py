"""CLI 主入口"""

# 加载 .env 文件（必须在其他导入之前）
from dotenv import load_dotenv

load_dotenv()

import sys  # noqa: E402

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402
from prompt_toolkit import PromptSession  # noqa: E402
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory  # noqa: E402
from prompt_toolkit.history import FileHistory  # noqa: E402
from rich.markdown import Markdown  # noqa: E402

from nano_code.agent.graph import get_agent_graph  # noqa: E402
from nano_code.agent.state import create_initial_state  # noqa: E402
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
from nano_code.core.config import get_settings  # noqa: E402
from nano_code.memory.conversation import ConversationMemory  # noqa: E402


def get_current_model() -> str:
    """获取当前模型名称"""
    settings = get_settings()
    return settings.model


def run_interactive() -> None:
    """运行交互式会话"""
    print_welcome()

    # 初始化记忆
    settings = get_settings()
    storage_path = settings.storage_path / "sessions" / "default.json"
    memory = ConversationMemory(storage_path=storage_path, auto_save=True)

    # 初始化 Agent
    graph = get_agent_graph()

    # 获取当前模型
    current_model = get_current_model()

    # 初始化 prompt session（增强版）
    session: PromptSession[str] = PromptSession(
        history=FileHistory(str(settings.storage_path / "history.txt")),
        auto_suggest=AutoSuggestFromHistory(),
        multiline=False,
        mouse_support=True,
    )

    console.print("\n[dim]💡 提示: 输入多行内容时，按 Tab 换行，Enter 发送[/dim]")
    console.print("[dim]💡 输入 /help 查看所有命令[/dim]\n")

    # 显示初始状态栏
    print_status_bar(current_model)
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

            # 执行图（带思考动画）
            with thinking_animation("Thinking"):
                result = graph.invoke(state)

            # 提取响应
            if result.get("messages"):
                last_msg = result["messages"][-1]
                if isinstance(last_msg, dict):
                    response = last_msg.get("content", "")
                else:
                    response = getattr(last_msg, "content", "")

                if response:
                    # 尝试渲染 Markdown
                    try:
                        console.print("\n[bold blue]🤖 Assistant:[/bold blue]")
                        console.print(Markdown(response))
                    except Exception:
                        console.print(f"\n[bold blue]🤖 Assistant:[/bold blue] {response}")

                    # 添加到记忆
                    memory.add_message(AIMessage(content=response))

            # 更新 token 统计
            token_count = memory.token_count()
            session_stats.total_tokens = token_count

            # 显示状态栏
            print_status_bar(current_model)

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ 已取消[/yellow]")
            continue
        except EOFError:
            console.print("\n[blue]👋 再见！[/blue]")
            break
        except Exception as e:
            print_error(str(e))


def handle_command(command: str, memory: ConversationMemory, model: str) -> bool:
    """处理命令

    Args:
        command: 命令字符串
        memory: 记忆管理器
        model: 当前模型名称

    Returns:
        是否继续运行（False 表示退出）
    """
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

    else:
        console.print(f"[yellow]⚠️ 未知命令: {command}[/yellow]")
        console.print("[dim]输入 /help 查看可用命令[/dim]")

    return True


def main() -> None:
    """主入口"""
    try:
        run_interactive()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
