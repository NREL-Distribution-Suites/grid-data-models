"""Schema and metadata helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from gdm.db.connection import sqlite_path_from_target


def default_schema_path() -> Path:
    """Return the default path to the SQL schema file bundled with the package."""
    return Path(__file__).resolve().parent / "distribution_schema.sql"


def _initialize_schema(conn: sqlite3.Connection, schema_path: str | Path | None) -> None:
    if _has_gdm_tables(conn):
        return

    resolved_schema_path = Path(schema_path) if schema_path else default_schema_path()
    if not resolved_schema_path.exists():
        raise FileNotFoundError(f"Schema file was not found at {resolved_schema_path}")

    schema_sql = resolved_schema_path.read_text()
    conn.executescript(schema_sql)


def _has_gdm_tables(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'gdm_system_snapshots'"
    ).fetchone()
    return row is not None


def _ensure_gdm_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS gdm_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS gdm_system_snapshots (
            system_kind TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS gdm_component_uuid_map (
            component_type TEXT NOT NULL,
            component_id INTEGER NOT NULL,
            uuid TEXT NOT NULL,
            PRIMARY KEY (component_type, component_id),
            UNIQUE (component_type, uuid)
        );
        """
    )


def _upsert_metadata(conn: sqlite3.Connection, key: str, value: str | None) -> None:
    if value is None:
        return
    conn.execute(
        """
        INSERT INTO gdm_metadata(key, value)
        VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, str(value)),
    )


def inspect_snapshot_metadata(
    db_path: str | Path | None = None, db_url: str | None = None
) -> dict[str, str]:
    """Return GDM metadata key-values for debugging and validation."""
    db_path = sqlite_path_from_target(db_path=db_path, db_url=db_url)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT key, value FROM gdm_metadata").fetchall()
    return {key: value for key, value in rows}
