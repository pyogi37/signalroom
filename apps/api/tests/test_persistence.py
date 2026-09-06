import sqlite3

from signalroom import persistence


def test_schema_mismatch_rebuilds_tables(monkeypatch, tmp_path):
    database = tmp_path / "signalroom.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript("""
            CREATE TABLE audit_events (id INTEGER PRIMARY KEY, session_id TEXT, event TEXT, detail TEXT, created_at TEXT);
            CREATE TABLE sessions (id TEXT PRIMARY KEY, payload TEXT);
            INSERT INTO sessions VALUES ('old', '{}');
        """)
    monkeypatch.setattr(persistence, "DATABASE", database)
    persistence.initialize()
    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(audit_events)")}
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        version = connection.execute("PRAGMA user_version").fetchone()[0]
    assert "room_id" in columns and "session_id" not in columns
    assert "sessions" not in tables and "rooms" in tables
    assert version == persistence.SCHEMA_VERSION

    persistence.log_event("r1", "room_created", {"ok": True})
    assert persistence.audit_events("r1")[0]["detail"] == {"ok": True}
    persistence.initialize()  # idempotent at the current version
    assert persistence.audit_events("r1")
