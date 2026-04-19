from __future__ import annotations

import json
import os
import uuid

from .models import Session


class SessionManager:
    def __init__(self, storage_dir: str = "./sessions"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _path(self, session_id: str) -> str:
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def create_session(self, user_id: str | None = None, metadata: dict | None = None) -> Session:
        session_id = str(uuid.uuid4())
        s = Session(id=session_id, user_id=user_id, metadata=metadata or {})
        self.save_session(s)
        return s

    def get_session(self, session_id: str) -> Session | None:
        path = self._path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return Session.from_dict(data)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        s = self.get_session(session_id)
        if s is None:
            raise ValueError(f"Session {session_id} not found")
        s.add_message(role, content)
        self.save_session(s)

    def save_session(self, session: Session) -> None:
        path = self._path(session.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def recover_session(self, session_id: str) -> Session | None:
        # Alias for clarity; returns a populated Session or None if not found
        return self.get_session(session_id)
