"""Input Box - 多行输入组件"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.events import Key
from textual.widgets import Input, Label


class InputBox(Horizontal):
    """输入框组件

    支持多行输入，Ctrl+Enter 或 Enter 发送消息。
    """

    def compose(self) -> ComposeResult:
        yield Label("❯", id="prompt")
        yield Input(placeholder="Type a message... (/help for commands)", id="input")

    def on_key(self, event: Key) -> None:
        """处理按键事件"""
        if event.key == "enter":
            input_widget = self.query_one("#input", Input)
            value = input_widget.value.strip()
            if value:
                self.app.post_message(NewMessage(value))
                input_widget.value = ""

    def disable(self) -> None:
        """禁用输入"""
        self.query_one("#input", Input).disabled = True

    def enable(self) -> None:
        """启用输入"""
        input_widget = self.query_one("#input", Input)
        input_widget.disabled = False
        input_widget.focus()


class NewMessage:
    """新消息事件"""

    def __init__(self, content: str):
        self.content = content
