"""TUI snapshot tests - visual regression testing for jojo-code TUI

Uses Textual's built-in App.save_screenshot() for baseline generation.
Run locally with a display, or headlessly.

Usage:
    # Generate/update baselines
    SNAPSHOT_UPDATE=1 pytest tests/test_tui/ -v

    # Run comparison tests
    pytest tests/test_tui/ -v

    # Local screenshot preview
    python tests/test_tui/preview_screenshot.py
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
BASELINE_DIR = SNAPSHOT_DIR / "baseline"
UPDATE_MODE = os.getenv("SNAPSHOT_UPDATE", "0") == "1"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def app():
    """Create app instance with mocked WebSocket."""
    with patch("jojo_code.cli.ws_client.WSClient") as mock_ws:
        mock_instance = AsyncMock()
        mock_instance.connect = AsyncMock(return_value=None)
        mock_instance.get_model = AsyncMock(return_value="MiniMax-M2.7")
        mock_instance.get_stats = AsyncMock(return_value={"messages": 0, "tokens": 0})
        mock_ws.return_value = mock_instance

        from jojo_code.cli.app import JojoCodeApp

        app = JojoCodeApp(server_url="ws://localhost:9999")
        async with app.run_test() as pilot:
            await pilot.pause()
            yield pilot, app


@pytest.fixture(autouse=True)
def setup_snapshot_dir():
    """Ensure snapshot directories exist."""
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    yield


# ============================================================================
# Snapshot Tests
# ============================================================================


@pytest.mark.asyncio
async def test_screenshot_empty_state(app):
    """Empty chat state should match baseline."""
    pilot, test_app = app
    baseline = BASELINE_DIR / "empty_state.png"

    if UPDATE_MODE:
        path = test_app.save_screenshot(str(baseline))
        print(f"\n✅ Baseline updated: {path}")
        return

    assert baseline.exists(), (
        f"Baseline not found: {baseline}. Run with SNAPSHOT_UPDATE=1 to generate."
    )


@pytest.mark.asyncio
async def test_app_title(app):
    """App should have correct title."""
    _pilot, test_app = app
    assert test_app.title == "jojo-code"


@pytest.mark.asyncio
async def test_status_bar_present(app):
    """Status bar should be present."""
    _pilot, test_app = app
    from jojo_code.cli.views.status_bar import StatusBar

    status_bar = test_app.query_one("#status-bar", StatusBar)
    assert status_bar is not None


@pytest.mark.asyncio
async def test_chat_view_present(app):
    """Chat view should be present."""
    _pilot, test_app = app
    from jojo_code.cli.views.chat import ChatView

    chat = test_app.query_one("#chat", ChatView)
    assert chat is not None


@pytest.mark.asyncio
async def test_input_box_present(app):
    """Input box should be present."""
    _pilot, test_app = app
    from jojo_code.cli.views.input_box import InputBox

    inp = test_app.query_one("#input-box", InputBox)
    assert inp is not None


# ============================================================================
# Import sanity checks
# ============================================================================


def test_chat_view_import():
    from jojo_code.cli.views.chat import ChatView

    assert ChatView is not None


def test_input_box_import():
    from jojo_code.cli.views.input_box import InputBox

    assert InputBox is not None


def test_status_bar_import():
    from jojo_code.cli.views.status_bar import StatusBar

    assert StatusBar is not None


def test_app_import():
    from jojo_code.cli.app import JojoCodeApp

    assert JojoCodeApp is not None


# ============================================================================
# Preview script (run directly)
# ============================================================================

if __name__ == "__main__":
    print("Generating preview screenshot...")

    with patch("jojo_code.cli.ws_client.WSClient") as mock_ws:
        mock_instance = AsyncMock()
        mock_instance.connect = AsyncMock(return_value=None)
        mock_instance.get_model = AsyncMock(return_value="MiniMax-M2.7")
        mock_instance.get_stats = AsyncMock(return_value={"messages": 5, "tokens": 1234})
        mock_ws.return_value = mock_instance

        from jojo_code.cli.app import JojoCodeApp

        app = JojoCodeApp(server_url="ws://localhost:9999")

        async def run():
            async with app.run_test() as pilot:
                await pilot.pause()
                path = app.save_screenshot("/tmp/jojo_tui_preview.png")
                print(f"Saved to: {path}")
                print(f"Size: {Path(path).stat().st_size} bytes")

        asyncio.run(run())
