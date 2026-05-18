"""Memory management module.

Provides session memory management with:
- Short-term memory (current session)
- Long-term memory (persistent storage)
- Memory retrieval (search)
"""

from jojo_code.memory.conversation import (
    Conversation,
    ConversationManager,
    ConversationMemory,
    MemoryStore,
    Message,
)
from jojo_code.memory.long_term import LongTermMemory, create_longterm_memory
from jojo_code.memory.retriever import MemoryRetriever, SessionMemory, create_session_memory
from jojo_code.memory.short_term import (
    ShortTermMemory,
)
from jojo_code.memory.short_term import (
    create_session_memory as create_short_memory,
)
from jojo_code.memory.types import MemoryItem, MemoryScope, MemoryType, SearchResult

__all__ = [
    # Types
    "MemoryItem",
    "MemoryType",
    "MemoryScope",
    "SearchResult",
    # Conversation (legacy)
    "Conversation",
    "ConversationManager",
    "ConversationMemory",
    "MemoryStore",
    "Message",
    # Short-term memory
    "ShortTermMemory",
    "create_session_memory",
    # Long-term memory
    "LongTermMemory",
    "create_longterm_memory",
    # Retriever
    "MemoryRetriever",
    "SessionMemory",
    "create_session_memory",
    "create_short_memory",
]
