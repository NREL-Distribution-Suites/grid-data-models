"""UUID identity map helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3
from uuid import UUID


def _upsert_component_uuid_map(
    conn: sqlite3.Connection, component_type: str, component_id: int, component_uuid: UUID
) -> None:
    conn.execute(
        """
        INSERT INTO gdm_component_uuid_map(component_type, component_id, uuid)
        VALUES(?, ?, ?)
        ON CONFLICT(component_type, component_id) DO UPDATE SET uuid=excluded.uuid
        """,
        (component_type, component_id, str(component_uuid)),
    )


def _fetch_component_uuid(
    conn: sqlite3.Connection, component_type: str, component_id: int
) -> UUID | None:
    row = conn.execute(
        "SELECT uuid FROM gdm_component_uuid_map WHERE component_type = ? AND component_id = ?",
        (component_type, component_id),
    ).fetchone()
    if row is None:
        return None
    return UUID(row[0])
