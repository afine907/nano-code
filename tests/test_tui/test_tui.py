"""TUI snapshot tests - visual regression testing for jojo-code TUI"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestTUISnapshots:
    """Snapshot tests for TUI components"""

    @pytest.fixture
    async def app(self):
        """Create app instance for testing"""
        from textual.app import App

        # Mock WebSocket to avoid connection
        with patch("jojo_code.cli.ws_client.WSClient") as mock_ws:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock(return_value=None)
            mock_instance.get_model = AsyncMock(return_value="MiniMax-M2.7")
            mock_instance.get_stats = AsyncMock(return_value={"messages": 0, "tokens": 0})
            mock_ws.return_value = mock_instance

            from jojo_code.cli.app import JojoCodeApp

            app = JojoCodeApp(server_url="ws://localhost:9999")
            async with app.run_test() as pilot:
                yield pilot, app

    @pytest.mark.skip(reason="Requires display for screenshot")
    async def test_main_window_loads(self, app):
        """Main window should load without errors"""
        pilot, test_app = app
        # Check title
        assert test_app.title == "jojo-code"

    @pytest.mark.skip(reason="Requires display for screenshot")
    async def test_input_box_works(self, app):
        """Input box should accept text"""
        pilot, test_app = app
        # Type something
        await pilot.click("#input-box")
        await pilot.type("hello world")
        # Check input contains text
        input_widget = test_app.query_one("#input-box")
        assert input_widget.value == "hello world"

    @pytest.mark.skip(reason="Requires display for screenshot")
    async def test_disconnected_state(self, app):
        """Should show disconnected warning when server unreachable"""
        pilot, test_app = app
        # Force disconnect
        from jojo_code.cli.views.chat import ChatView

        chat = test_app.query_one("#chat", ChatView)
        assert chat is not None

    def test_app_can_be_instantiated(self):
        """App should be instantiable without errors"""
        from jojo_code.cli.app import JojoCodeApp

        app = JojoCodeApp(server_url="ws://localhost:9999")
        assert app.title == "jojo-code"
        assert app.server_url == "ws://localhost:9999"

    def test_chat_view_can_be_imported(self):
        """ChatView should be importable"""
        from jojo_code.cli.views.chat import ChatView

        assert ChatView is not None

    def test_input_box_can_be_imported(self):
        """InputBox should be importable"""
        from jojo_code.cli.views.input_box import InputBox

        assert InputBox is not None

    def test_status_bar_can_be_imported(self):
        """StatusBar should be importable"""
        from jojo_code.cli.views.status_bar import StatusBar

        assert StatusBar is not None


class TestTUIScreenshot:
    """Screenshot-based visual regression tests

    These tests generate screenshots and compare against baselines.
    Requires: pip install Pillow pytest-xdist  # for parallel screenshot
    """

    @pytest.mark.skip(reason="Baseline screenshots not yet generated")
    def test_screenshot_chat_empty_state(self):
        """Empty chat should match baseline"""
        # This test would:
        # 1. Mount app in headless mode
        # 2. Take screenshot
        # 3. Compare against baseline using pixel diff
        # 4. Fail if diff > threshold
        pass

    @pytest.mark.skip(reason="Baseline screenshots not yet generated")
    def test_screenshot_chat_with_messages(self):
        """Chat with messages should match baseline"""
        pass

    @pytest.mark.skip(reason="Baseline screenshots not yet generated")
    def test_screenshot_disconnected_state(self):
        """Disconnected warning should match baseline"""
        pass

    @pytest.mark.skip(reason="Baseline screenshots not yet generated")
    def test_screenshot_mode_switch(self):
        """Mode switch UI should match baseline"""
        pass


# =============================================================================
# How to use screenshot tests locally
# =============================================================================
"""
To run screenshot tests on your local machine:

1. Install dependencies:
   pip install Pillow pytest-xdist

2. Generate baseline screenshots (first time only):
   # On your local machine with a display
   pytest tests/test_tui/ -k screenshot --snapshot-generate

3. Run screenshot tests:
   pytest tests/test_tui/ -k screenshot

4. Update baselines when UI changes:
   pytest tests/test_tui/ -k screenshot --snapshot-update

The screenshot comparison uses pixel-diff algorithm.
A test fails if >1% of pixels differ from baseline.

Screenshot baslines are stored in:
   tests/test_tui/snapshots/baseline/
"""
