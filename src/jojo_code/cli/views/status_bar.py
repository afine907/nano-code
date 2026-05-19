"""Status Bar - 状态栏组件"""

from textual.widgets import Static


class StatusBar(Static):
    """状态栏

    显示模型、连接状态、消息统计。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = "unknown"
        self.mode = "build"
        self.connected = False
        self.messages = 0
        self.tokens = 0

    def render(self) -> str:
        conn_icon = "●" if self.connected else "○"
        conn_text = "connected" if self.connected else "disconnected"

        return (
            f" {conn_icon} {conn_text}"
            f"  ·  {self.model}"
            f"  ·  {self.mode.upper()}"
            f"  ·  {self.messages} msgs"
            f"  ·  {self.tokens} tokens"
        )

    def update_model(self, model: str) -> None:
        """更新模型名称"""
        self.model = model
        self.refresh()

    def update_mode(self, mode: str) -> None:
        """更新模式"""
        self.mode = mode
        self.refresh()

    def update_connection(self, connected: bool) -> None:
        """更新连接状态"""
        self.connected = connected
        self.refresh()

    def update_stats(self, messages: int, tokens: int) -> None:
        """更新统计信息"""
        self.messages = messages
        self.tokens = tokens
        self.refresh()

    def update(
        self,
        model: str | None = None,
        connected: bool | None = None,
        messages: int | None = None,
        tokens: int | None = None,
    ) -> None:
        """更新状态栏字段"""
        if model is not None:
            self.model = model
        if connected is not None:
            self.connected = connected
        if messages is not None:
            self.messages = messages
        if tokens is not None:
            self.tokens = tokens
        self.refresh()
