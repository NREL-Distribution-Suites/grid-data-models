"""PostgreSQL persistence helpers for GDM systems.

This module currently persists and restores transactional snapshot payloads
through GDM additive tables.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from typing import Type

from sqlalchemy import MetaData
from sqlalchemy import CheckConstraint
from sqlalchemy import create_engine
from sqlalchemy import text

from gdm.db.connection import create_db_engine
from gdm.db.sqlite_store import DEFAULT_DB_FORMAT_VERSION
from gdm.db.sqlite_store import _attach_time_series_from_snapshot
from gdm.db.sqlite_store import _load_distribution_topology_from_normalized
from gdm.db.sqlite_store import write_system_to_db as write_system_to_sqlite
from gdm.db.sqlite_store_snapshot import (
    _decode_snapshot_payload,
    _restore_time_series_sidecar,
    _serialize_system_to_json_text,
)


def _ensure_gdm_tables_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS gdm_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
    )

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS gdm_system_snapshots (
                system_kind TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS gdm_component_uuid_map (
                component_type TEXT NOT NULL,
                component_id BIGINT NOT NULL,
                uuid TEXT NOT NULL,
                PRIMARY KEY (component_type, component_id),
                UNIQUE (component_type, uuid)
            )
            """
        )
    )

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS gdm_distribution_normalized_cache (
                system_kind TEXT PRIMARY KEY,
                sqlite_payload BYTEA NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _upsert_metadata_postgres(conn, key: str, value: str | None) -> None:
    if value is None:
        return

    conn.execute(
        text(
            """
            INSERT INTO gdm_metadata(key, value)
            VALUES (:key, :value)
            ON CONFLICT(key) DO UPDATE SET value = EXCLUDED.value
            """
        ),
        {"key": key, "value": str(value)},
    )


def _build_distribution_normalized_cache_payload(system) -> bytes:
    with tempfile.TemporaryDirectory() as tmp_dir:
        sqlite_path = Path(tmp_dir) / "distribution_normalized.sqlite"
        write_system_to_sqlite(
            system=system,
            db_path=sqlite_path,
            replace=True,
            initialize_schema=True,
            system_kind="distribution",
        )
        return sqlite_path.read_bytes()


def _build_distribution_normalized_sqlite_db(system, sqlite_path: Path) -> None:
    write_system_to_sqlite(
        system=system,
        db_path=sqlite_path,
        replace=True,
        initialize_schema=True,
        system_kind="distribution",
    )


def _sync_sqlite_normalized_tables_to_postgres(
    sqlite_path: Path, postgres_conn, replace: bool
) -> None:
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    sqlite_metadata = MetaData()
    sqlite_metadata.reflect(bind=sqlite_engine)

    mirror_metadata = MetaData()
    source_tables = [
        table
        for table in sqlite_metadata.sorted_tables
        if not table.name.startswith("sqlite_") and not table.name.startswith("gdm_")
    ]
    for table in source_tables:
        table.to_metadata(mirror_metadata)

    for table in mirror_metadata.tables.values():
        for constraint in list(table.constraints):
            if isinstance(constraint, CheckConstraint):
                table.constraints.remove(constraint)

    mirror_metadata.create_all(bind=postgres_conn, checkfirst=True)

    target_tables = [mirror_metadata.tables[table.name] for table in source_tables]
    if replace:
        for table in reversed(target_tables):
            postgres_conn.execute(table.delete())

    with sqlite_engine.connect() as sqlite_conn:
        for source_table in source_tables:
            rows = sqlite_conn.execute(source_table.select()).mappings().all()
            if not rows:
                continue
            target_table = mirror_metadata.tables[source_table.name]
            postgres_conn.execute(target_table.insert(), [dict(row) for row in rows])

    sqlite_engine.dispose()


def _load_distribution_from_normalized_cache_payload(payload: bytes):
    with tempfile.TemporaryDirectory() as tmp_dir:
        sqlite_path = Path(tmp_dir) / "distribution_normalized.sqlite"
        sqlite_path.write_bytes(payload)
        with sqlite3.connect(sqlite_path) as conn:
            normalized = _load_distribution_topology_from_normalized(conn)
            if normalized is not None:
                _attach_time_series_from_snapshot(conn, normalized)
            return normalized


def write_system_to_db(
    *,
    system,
    db_path: str | Path | None = None,
    db_url: str | None = None,
    schema_path: str | Path | None = None,
    replace: bool = True,
    initialize_schema: bool = True,
    system_kind: str,
) -> None:
    """Write a system snapshot to PostgreSQL with transactional replace semantics."""
    if schema_path is not None:
        raise NotImplementedError(
            "Custom schema_path is not supported for PostgreSQL persistence yet."
        )

    payload = _serialize_system_to_json_text(system)
    normalized_payload: bytes | None = None
    normalized_sqlite_path: Path | None = None
    tmp_dir: tempfile.TemporaryDirectory | None = None
    if system_kind == "distribution":
        tmp_dir = tempfile.TemporaryDirectory()
        normalized_sqlite_path = Path(tmp_dir.name) / "distribution_normalized.sqlite"
        _build_distribution_normalized_sqlite_db(system, normalized_sqlite_path)
        normalized_payload = normalized_sqlite_path.read_bytes()

    engine = create_db_engine(db_path=db_path, db_url=db_url)
    try:
        with engine.begin() as conn:
            if initialize_schema:
                _ensure_gdm_tables_postgres(conn)

            if system_kind == "distribution" and normalized_sqlite_path is not None:
                _sync_sqlite_normalized_tables_to_postgres(
                    normalized_sqlite_path,
                    conn,
                    replace=replace,
                )

            if replace:
                conn.execute(
                    text("DELETE FROM gdm_system_snapshots WHERE system_kind = :system_kind"),
                    {"system_kind": system_kind},
                )

                if system_kind == "distribution":
                    conn.execute(
                        text(
                            "DELETE FROM gdm_distribution_normalized_cache "
                            "WHERE system_kind = :system_kind"
                        ),
                        {"system_kind": system_kind},
                    )

            conn.execute(
                text(
                    """
                    INSERT INTO gdm_system_snapshots(system_kind, payload_json, created_at)
                    VALUES (:system_kind, :payload_json, CURRENT_TIMESTAMP)
                    ON CONFLICT(system_kind)
                    DO UPDATE SET payload_json = EXCLUDED.payload_json, created_at = CURRENT_TIMESTAMP
                    """
                ),
                {"system_kind": system_kind, "payload_json": payload},
            )

            if system_kind == "distribution" and normalized_payload is not None:
                conn.execute(
                    text(
                        """
                        INSERT INTO gdm_distribution_normalized_cache(
                            system_kind,
                            sqlite_payload,
                            created_at
                        )
                        VALUES (:system_kind, :sqlite_payload, CURRENT_TIMESTAMP)
                        ON CONFLICT(system_kind)
                        DO UPDATE SET
                            sqlite_payload = EXCLUDED.sqlite_payload,
                            created_at = CURRENT_TIMESTAMP
                        """
                    ),
                    {"system_kind": system_kind, "sqlite_payload": normalized_payload},
                )

            _upsert_metadata_postgres(conn, "gdm_db_format_version", DEFAULT_DB_FORMAT_VERSION)
            _upsert_metadata_postgres(
                conn, f"{system_kind}_data_format_version", system.data_format_version
            )
            if system_kind == "distribution":
                _upsert_metadata_postgres(
                    conn,
                    f"{system_kind}_storage_mode",
                    "snapshot+normalized+timeseries-associations-v1",
                )
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()


def load_system_from_db(
    *,
    system_cls: Type,
    db_path: str | Path | None = None,
    db_url: str | None = None,
    system_kind: str,
    prefer_normalized: bool = False,
) -> object:
    """Load a system from PostgreSQL snapshot tables."""
    engine = create_db_engine(db_path=db_path, db_url=db_url)
    if system_kind == "distribution" and prefer_normalized:
        with engine.connect() as conn:
            cached_row = conn.execute(
                text(
                    """
                    SELECT sqlite_payload
                    FROM gdm_distribution_normalized_cache
                    WHERE system_kind = :system_kind
                    """
                ),
                {"system_kind": system_kind},
            ).fetchone()

        if cached_row is not None and cached_row[0]:
            normalized_system = _load_distribution_from_normalized_cache_payload(cached_row[0])
            if normalized_system is not None:
                return normalized_system

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT payload_json FROM gdm_system_snapshots WHERE system_kind = :system_kind"),
            {"system_kind": system_kind},
        ).fetchone()

    if row is None:
        raise ValueError(f"No persisted '{system_kind}' system found in target database")

    payload = row[0]
    if not payload:
        raise ValueError(f"Persisted payload for '{system_kind}' is empty in target database")

    snapshot = _decode_snapshot_payload(payload)
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_json = Path(tmp_dir) / f"{system_kind}_snapshot.json"
        temp_json.write_text(snapshot["system_json"])
        _restore_time_series_sidecar(Path(tmp_dir), snapshot)
        return system_cls.from_json(temp_json)


def load_snapshot_payload(
    db_path: str | Path | None = None,
    system_kind: str = "distribution",
    db_url: str | None = None,
) -> dict:
    """Return raw snapshot payload as a JSON dictionary for inspection."""
    engine = create_db_engine(db_path=db_path, db_url=db_url)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT payload_json FROM gdm_system_snapshots WHERE system_kind = :system_kind"),
            {"system_kind": system_kind},
        ).fetchone()

    if row is None:
        raise ValueError(f"No persisted '{system_kind}' system found in target database")

    payload = row[0]
    snapshot = _decode_snapshot_payload(payload)
    return {
        "snapshot_format": "gdm-postgres-v1",
        "system_json": snapshot["system_json"],
        "time_series_directory": snapshot.get("time_series_directory"),
        "time_series_zip_b64": snapshot.get("time_series_zip_b64"),
    }


def inspect_snapshot_metadata(
    db_path: str | Path | None = None, db_url: str | None = None
) -> dict[str, str]:
    """Return GDM metadata key-values for debugging and validation."""
    engine = create_db_engine(db_path=db_path, db_url=db_url)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT key, value FROM gdm_metadata")).fetchall()
    return {str(key): str(value) for key, value in rows}
