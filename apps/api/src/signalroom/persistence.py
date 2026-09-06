"""Room storage and the audit log.

The LangGraph checkpointer is the source of truth for workflow state. This
module stores the projected `Room` the API serves, plus an append-only audit
log of human decisions and system events.
"""

import json
import sqlite3

from .config import data_dir
from .models import Room

DATABASE = data_dir() / "signalroom.sqlite3"

# Bump when the tables change. This is local demo state, so a mismatch rebuilds
# the tables instead of migrating them; the recorded model runs re-seed rooms.
SCHEMA_VERSION = 2


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


def initialize() -> None:
    with _connect() as connection:
        current = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if current != SCHEMA_VERSION:
            connection.executescript("DROP TABLE IF EXISTS rooms; DROP TABLE IF EXISTS audit_events; DROP TABLE IF EXISTS sessions;")
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                organization TEXT NOT NULL,
                industry TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                fixture TEXT,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                event TEXT NOT NULL,
                actor TEXT NOT NULL DEFAULT 'system',
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)


def save_room(room: Room) -> Room:
    with _connect() as connection:
        connection.execute(
            """INSERT INTO rooms(id, organization, industry, status, fixture, payload, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET organization=excluded.organization, industry=excluded.industry,
               status=excluded.status, fixture=excluded.fixture, payload=excluded.payload, updated_at=excluded.updated_at""",
            (room.id, room.organization, room.industry, room.status, room.fixture, room.model_dump_json(), room.created_at, room.updated_at),
        )
    return room


def get_room(room_id: str) -> Room | None:
    with _connect() as connection:
        row = connection.execute("SELECT payload FROM rooms WHERE id = ?", (room_id,)).fetchone()
    return Room.model_validate_json(row["payload"]) if row else None


def list_rooms(limit: int = 24) -> list[dict]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, organization, industry, status, fixture, payload, created_at, updated_at FROM rooms ORDER BY updated_at DESC, rowid DESC LIMIT ?",
            (limit,),
        ).fetchall()
    result = []
    for row in rows:
        payload = json.loads(row["payload"])
        result.append({
            "id": row["id"], "organization": row["organization"], "industry": row["industry"], "status": row["status"],
            "fixture": row["fixture"], "created_at": row["created_at"], "updated_at": row["updated_at"],
            "requirements": len(payload.get("requirements", [])),
            "open_items": sum(1 for item in payload.get("open_items", []) if item.get("status") == "open"),
            "findings": len(((payload.get("critique") or {}).get("findings")) or []),
            "verdict": (payload.get("critique") or {}).get("verdict"),
            "modes": (payload.get("metrics") or {}).get("modes", []),
        })
    return result


def log_event(room_id: str, event: str, detail: dict | str, actor: str = "system") -> None:
    serialized = detail if isinstance(detail, str) else json.dumps(detail)
    with _connect() as connection:
        connection.execute(
            "INSERT INTO audit_events(room_id, event, actor, detail) VALUES (?, ?, ?, ?)",
            (room_id, event, actor, serialized),
        )


def audit_events(room_id: str) -> list[dict]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, event, actor, detail, created_at FROM audit_events WHERE room_id = ? ORDER BY id", (room_id,)
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
