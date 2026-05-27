from __future__ import annotations
"""In-memory session store. Swap the backend for Redis in production."""
from collections import defaultdict, deque
from app.models import SessionMessage
from app.config import get_settings

settings = get_settings()

_sessions: dict[str, deque[SessionMessage]] = defaultdict(
    lambda: deque(maxlen=settings.max_history_turns * 2)
)


def get_history(session_id: str) -> list[SessionMessage]:
    return list(_sessions[session_id])


def add_turn(session_id: str, user_msg: str, assistant_msg: str) -> None:
    _sessions[session_id].append(SessionMessage(role="user", content=user_msg))
    _sessions[session_id].append(SessionMessage(role="assistant", content=assistant_msg))


def clear_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def history_as_gemini_messages(session_id: str) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in get_history(session_id)]
