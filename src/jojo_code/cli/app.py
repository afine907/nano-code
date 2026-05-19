"""jojo-code Textual App - Claude Code inspired design"""

import asyncio
import logging

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Static

from jojo_code.cli.theme import COLORS, CSS
from jojo_code.cli.views.input_box import InputBox, NewMessage
from jojo_code.cli.views.status_bar import StatusBar

logger = logging.getLogger(__name__)


class JojoCodeApp(App):
    """jojo-code TUI application - Claude Code inspired design"""

    TITLE = "jojo-code"
    SUB_TITLE = "Python Coding Agent"

    CSS = CSS

    BINDINGS = [
        Binding("ctrl+c", "quit", "退出"),
        Binding("ctrl+l", "clear", "清空"),
        Binding("ctrl+p", "toggle_sidebar", "切换侧边栏"),
    ]

    def __init__(self, server_url: str = "ws://localhost:8080/ws", **kwargs):
        super().__init__(**kwargs)
        self.server_url = server_url
        self._ws_client = None
        self._mode = "build"
        self._connected = False
        self._sidebar_visible = True

    # -------------------------------------------------------------------------
    # Compose
    # -------------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        # Header
        with Horizontal(id="header"):
            yield Static("⭘ jojo-code", id="header-title")
            yield Static("build", id="header-mode")
            yield Static("", id="header-status")
            yield Static("", id="header-spacer")
            yield Static("", id="header-conn")

        # Main content area
        with Horizontal(id="content"):
            # Sidebar (file tree placeholder)
            with VerticalScroll(id="sidebar"):
                yield Static("FILES", classes="sidebar-section")
                yield Static("No workspace open", classes="sidebar-item placeholder")
                yield Static("─" * 24, classes="separator")
                yield Static("SESSIONS", classes="sidebar-section")
                yield Static("New chat", classes="sidebar-item active")

            # Main chat area
            with VerticalScroll(id="chat-wrapper"):
                with VerticalScroll(id="chat"):
                    yield Static(
                        "Type a message to start...\nUse /help for commands",
                        classes="placeholder",
                        id="welcome",
                    )
                # Input area
                with Container(id="input-area"):
                    yield InputBox(id="input-box")
                    yield Button("Send", id="send-btn", variant="primary")

        # Status bar
        with StatusBar(id="status-bar"):
            pass

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    async def on_mount(self) -> None:
        """Connect to server on startup."""
        self._update_header_mode()
        self._update_header_conn(connected=False)

        try:
            from jojo_code.cli.ws_client import WSClient

            self._ws_client = WSClient(self.server_url)
            await self._ws_client.connect()
            self._connected = True
            self._update_header_conn(connected=True)

            model = await self._ws_client.get_model()
            self._update_header_status(model)

            stats = await self._ws_client.get_stats()
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.update(
                model=model or "unknown",
                connected=True,
                messages=stats.get("messages", 0),
                tokens=stats.get("tokens", 0),
            )

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._connected = False
            self._update_header_conn(connected=False)
            self._update_header_status(f"Disconnected: {e}")

    # -------------------------------------------------------------------------
    # Event handlers
    # -------------------------------------------------------------------------

    def on_new_message(self, event: NewMessage) -> None:
        """Handle new message from input box."""
        content = event.content

        if content.startswith("/"):
            self._handle_command(content)
            return

        asyncio.create_task(self._send_message(content))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "send-btn":
            input_box = self.query_one("#input-box", InputBox)
            content = input_box.value.strip()
            if content:
                self.on_new_message(NewMessage(content))
                input_box.value = ""

    def _handle_command(self, cmd: str) -> None:
        """Process slash commands."""
        parts = cmd.strip().split()
        command = parts[0].lower()
        self.query_one("#chat", VerticalScroll)

        commands = {
            "/help": "Commands: /mode, /clear, /quit",
            "/clear": "action_clear",
            "/quit": "action_quit",
            "/exit": "action_quit",
        }

        if command in ("/mode",) and len(parts) > 1:
            new_mode = parts[1] if parts[1] in ("plan", "build") else "build"
            self._mode = new_mode
            self._update_header_mode()
            self._add_system_message(f"Mode: {new_mode}")

        elif command == "/clear":
            self.action_clear()

        elif command in ("/quit", "/exit"):
            self.exit()

        elif command in commands:
            result = commands[command]
            if isinstance(result, str) and result.startswith("action_"):
                getattr(self, result)()
            else:
                self._add_system_message(result)

        else:
            self._add_system_message(f"Unknown: {command}")

    async def _send_message(self, message: str) -> None:
        """Send message and handle streaming response."""
        chat = self.query_one("#chat", VerticalScroll)
        input_box = self.query_one("#input-box", InputBox)
        status_bar = self.query_one("#status-bar", StatusBar)

        # Remove welcome placeholder
        welcome = self.query_one("#welcome", Static)
        if welcome:
            welcome.remove()

        # Show user message
        self._add_user_message(message)
        input_box.value = ""

        # Show loading
        loading = Static(" ◐ thinking...", id="loading", classes="loading-dots")
        chat.mount(loading)
        chat.scroll_end(animate=False)

        try:
            if not self._ws_client:
                from jojo_code.cli.ws_client import WSClient

                self._ws_client = WSClient(self.server_url)
                await self._ws_client.connect()
                self._connected = True
                self._update_header_conn(connected=True)

            full_response = ""
            async for chunk in self._ws_client.stream("chat", {"message": message}):
                if chunk.type == "tool_call":
                    loading.update(f" ◑ {chunk.tool_name}")
                elif chunk.type == "content":
                    full_response += chunk.text
                elif chunk.type == "done":
                    break

            loading.remove()

            if full_response:
                self._add_assistant_message(full_response)

            stats = await self._ws_client.get_stats()
            status_bar.update(
                connected=True,
                messages=stats.get("messages", 0),
                tokens=stats.get("tokens", 0),
            )

        except Exception as e:
            loading.remove()
            self._add_assistant_message(f"Error: {e}")
            self._connected = False
            self._update_header_conn(connected=False)
            status_bar.update(connected=False)

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_clear(self) -> None:
        """Clear chat messages."""
        chat = self.query_one("#chat", VerticalScroll)
        chat.remove_children()
        chat.mount(
            Static(
                "Type a message to start...\nUse /help for commands",
                classes="placeholder",
                id="welcome",
            )
        )
        if self._ws_client:
            asyncio.create_task(self._ws_client.clear())

    def action_quit(self) -> None:
        """Quit application."""
        self.exit()

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        sidebar = self.query_one("#sidebar")
        self._sidebar_visible = not self._sidebar_visible
        if self._sidebar_visible:
            sidebar.styles.width = "26"
        else:
            sidebar.styles.width = "0"

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _add_user_message(self, content: str) -> None:
        """Add a user message bubble."""
        chat = self.query_one("#chat", VerticalScroll)
        bubble = Static(content, classes="message-user")
        chat.mount(bubble)
        chat.scroll_end(animate=False)

    def _add_assistant_message(self, content: str) -> None:
        """Add an assistant message bubble."""
        chat = self.query_one("#chat", VerticalScroll)
        bubble = Static(content, classes="message-assistant")
        chat.mount(bubble)
        chat.scroll_end(animate=False)

    def _add_system_message(self, content: str) -> None:
        """Add a system message."""
        chat = self.query_one("#chat", VerticalScroll)
        msg = Static(content, classes="message-tool")
        chat.mount(msg)
        chat.scroll_end(animate=False)

    def _update_header_mode(self) -> None:
        """Update header mode indicator."""
        mode = self.query_one("#header-mode", Static)
        mode.update(self._mode.upper())
        mode.styles.color = (
            COLORS["accent_purple"] if self._mode == "build" else COLORS["accent_blue"]
        )

    def _update_header_conn(self, connected: bool) -> None:
        """Update header connection status."""
        conn = self.query_one("#header-conn", Static)
        if connected:
            conn.update("● Connected")
            conn.styles.color = COLORS["accent_green"]
        else:
            conn.update("○ Disconnected")
            conn.styles.color = COLORS["accent_red"]

    def _update_header_status(self, text: str) -> None:
        """Update header status text."""
        status = self.query_one("#header-status", Static)
        status.update(text)
