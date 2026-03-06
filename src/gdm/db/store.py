"""Backend-dispatching persistence adapters for GDM systems."""

from __future__ import annotations

from pathlib import Path
from typing import Type

from gdm.db.connection import get_backend_name
from gdm.db.postgres_store import (
    inspect_snapshot_metadata as inspect_snapshot_metadata_postgres,
    load_snapshot_payload as load_snapshot_payload_postgres,
    load_system_from_db as load_system_from_postgres,
    write_system_to_db as write_system_to_postgres,
)
from gdm.db.sqlite_store import (
    DEFAULT_DB_FORMAT_VERSION,
    load_snapshot_payload as load_snapshot_payload_sqlite,
    load_system_from_db as load_system_from_sqlite,
    write_system_to_db as write_system_to_sqlite,
)
from gdm.db.sqlite_store_schema import default_schema_path
from gdm.db.sqlite_store_schema import (
    inspect_snapshot_metadata as inspect_snapshot_metadata_sqlite,
)


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
    """Write a system to a supported DB backend."""
    backend = get_backend_name(db_path=db_path, db_url=db_url)
    if backend == "sqlite":
        return write_system_to_sqlite(
            system=system,
            db_path=db_path,
            db_url=db_url,
            schema_path=schema_path,
            replace=replace,
            initialize_schema=initialize_schema,
            system_kind=system_kind,
        )

    if backend == "postgresql":
        return write_system_to_postgres(
            system=system,
            db_path=db_path,
            db_url=db_url,
            schema_path=schema_path,
            replace=replace,
            initialize_schema=initialize_schema,
            system_kind=system_kind,
        )

    raise NotImplementedError(f"Database backend '{backend}' is not supported.")


def load_system_from_db(
    *,
    system_cls: Type,
    db_path: str | Path | None = None,
    db_url: str | None = None,
    system_kind: str,
    prefer_normalized: bool = False,
) -> object:
    """Load a system from a supported DB backend."""
    backend = get_backend_name(db_path=db_path, db_url=db_url)
    if backend == "sqlite":
        return load_system_from_sqlite(
            system_cls=system_cls,
            db_path=db_path,
            db_url=db_url,
            system_kind=system_kind,
            prefer_normalized=prefer_normalized,
        )

    if backend == "postgresql":
        return load_system_from_postgres(
            system_cls=system_cls,
            db_path=db_path,
            db_url=db_url,
            system_kind=system_kind,
            prefer_normalized=prefer_normalized,
        )

    raise NotImplementedError(f"Database backend '{backend}' is not supported.")


def load_snapshot_payload(
    db_path: str | Path | None = None,
    system_kind: str = "distribution",
    db_url: str | None = None,
) -> dict:
    """Return raw snapshot payload as a JSON dictionary for inspection."""
    backend = get_backend_name(db_path=db_path, db_url=db_url)
    if backend == "sqlite":
        return load_snapshot_payload_sqlite(
            db_path=db_path,
            db_url=db_url,
            system_kind=system_kind,
        )

    if backend == "postgresql":
        return load_snapshot_payload_postgres(
            db_path=db_path,
            db_url=db_url,
            system_kind=system_kind,
        )

    raise NotImplementedError(f"Database backend '{backend}' is not supported.")


def inspect_snapshot_metadata(
    db_path: str | Path | None = None, db_url: str | None = None
) -> dict[str, str]:
    """Return GDM metadata key-values for debugging and validation."""
    backend = get_backend_name(db_path=db_path, db_url=db_url)
    if backend == "sqlite":
        return inspect_snapshot_metadata_sqlite(db_path=db_path, db_url=db_url)

    if backend == "postgresql":
        return inspect_snapshot_metadata_postgres(db_path=db_path, db_url=db_url)

    raise NotImplementedError(f"Database backend '{backend}' is not supported.")


__all__ = [
    "DEFAULT_DB_FORMAT_VERSION",
    "default_schema_path",
    "inspect_snapshot_metadata",
    "load_snapshot_payload",
    "load_system_from_db",
    "write_system_to_db",
]
