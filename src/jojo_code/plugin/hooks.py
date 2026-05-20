"""Plugin hook system for lifecycle and event callbacks"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Supported hook names
HOOK_BEFORE_TOOL_CALL = "before_tool_call"
HOOK_AFTER_TOOL_CALL = "after_tool_call"
HOOK_BEFORE_AGENT_RUN = "before_agent_run"
HOOK_AFTER_AGENT_RUN = "after_agent_run"
HOOK_ON_ERROR = "on_error"
HOOK_ON_LOAD = "on_load"
HOOK_ON_UNLOAD = "on_unload"


def hook(name: str) -> Callable:
    """Decorator to mark a function as a hook handler

    Usage:
        @hook("before_tool_call")
        def my_handler(tool_name: str, args: dict) -> None:
            pass
    """

    def decorator(func: Callable) -> Callable:
        func._hook_name = name  # type: ignore
        return func

    return decorator


class HookDispatcher:
    """Hook dispatcher - manages and dispatches hook events

    Hooks allow plugins to intercept and react to agent lifecycle events.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def register(self, name: str, handler: Callable) -> None:
        """Register a hook handler

        Args:
            name: Hook name
            handler: Callable handler
        """
        self._handlers[name].append(handler)

    def unregister(self, name: str, handler: Callable) -> None:
        """Unregister a hook handler

        Args:
            name: Hook name
            handler: Handler to remove
        """
        if name in self._handlers:
            self._handlers[name].remove(handler)

    def dispatch(self, name: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Dispatch a hook event to all handlers (sync and async)

        Args:
            name: Hook name
            *args: Positional args to pass to handlers
            **kwargs: Keyword args to pass to handlers

        Returns:
            List of handler return values
        """
        results = []
        for handler in self._handlers.get(name, []):
            try:
                result = handler(*args, **kwargs)
                # Support async handlers
                if asyncio.iscoroutine(result):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Create task but don't await - log warning for fire-and-forget
                            asyncio.create_task(result)
                            logger.warning(
                                f"Async hook handler '{handler.__name__}' for '{name}' "
                                "is fire-and-forget - results not collected"
                            )
                        else:
                            results.append(loop.run_until_complete(result))
                    except RuntimeError as e:
                        logger.warning(
                            f"Could not run async hook handler '{handler.__name__}' for '{name}': {e}"
                        )
                else:
                    results.append(result)
            except Exception:
                # Don't let one handler break others
                pass
        return results

    def has_handlers(self, name: str) -> bool:
        """Check if a hook has handlers registered"""
        return len(self._handlers.get(name, [])) > 0

    def clear(self) -> None:
        """Clear all handlers (for testing)"""
        self._handlers.clear()
