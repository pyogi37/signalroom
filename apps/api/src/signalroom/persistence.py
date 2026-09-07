import json
import os
import sqlite3
from pathlib import Path

from .models import Session


DATA_DIR = Path(os.getenv("SIGNALROOM_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE = DATA_DIR / "signalroom.sqlite3"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


def initialize() -> None:
    with _connect() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                organization TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)


def save_session(session: Session) -> Session:
    with _connect() as connection:
        connection.execute(
            """INSERT INTO sessions(id, organization, status, payload) VALUES (?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET organization=excluded.organization, status=excluded.status,
               payload=excluded.payload, updated_at=CURRENT_TIMESTAMP""",
            (session.id, session.organization, session.status, session.model_dump_json()),
        )
    return session


def get_session(session_id: str) -> Session | None:
    with _connect() as connection:
        row = connection.execute("SELECT payload FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return Session.model_validate_json(row["payload"]) if row else None


def recent_sessions(limit: int = 12) -> list[dict[str, str]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, organization, status, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def log_event(session_id: str, event: str, detail: dict | str) -> None:
    serialized = detail if isinstance(detail, str) else json.dumps(detail)
    with _connect() as connection:
        connection.execute(
            "INSERT INTO audit_events(session_id, event, detail) VALUES (?, ?, ?)",
            (session_id, event, serialized),
        )


def audit_events(session_id: str) -> list[dict[str, object]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, event, detail, created_at FROM audit_events WHERE session_id = ? ORDER BY id", (session_id,)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        try:
            item["detail"] = json.loads(str(item["detail"]))
        except json.JSONDecodeError:
            pass
        result.append(item)
    return result


initialize()
