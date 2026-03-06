"""Database connection target helpers.

This module centralizes validation and resolution logic for DB targets while the
storage layer transitions from path-based SQLite APIs to DSN-based backends.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


def resolve_db_url(db_path: str | Path | None = None, db_url: str | None = None) -> str:
    """Resolve a canonical DB URL from compatibility inputs.

    Parameters
    ----------
    db_path : str | Path | None
        Legacy path input for SQLite files.
    db_url : str | None
        DSN/URL input. Examples: ``sqlite:////tmp/system.db``,
        ``postgresql+psycopg://user:pass@host:5432/db``.
    """

    if db_url and db_path:
        raise ValueError("Provide either 'db_path' or 'db_url', not both.")

    if db_url:
        return db_url

    if db_path is None:
        raise ValueError("A database target is required. Provide 'db_url' or 'db_path'.")

    return f"sqlite:///{Path(db_path)}"


def sqlite_path_from_target(db_path: str | Path | None = None, db_url: str | None = None) -> Path:
    """Return a filesystem path for SQLite targets.

    This helper supports both direct file paths and SQLite URLs. Non-SQLite
    URLs are intentionally rejected in this module because PostgreSQL support is
    added incrementally in subsequent milestones.
    """

    resolved = resolve_db_url(db_path=db_path, db_url=db_url)
    parsed = urlparse(resolved)

    if parsed.scheme in {"", "sqlite"}:
        if parsed.scheme == "":
            return Path(resolved)

        if parsed.netloc not in {"", "localhost"}:
            raise ValueError(f"Unsupported SQLite URL host in '{resolved}'.")

        if not parsed.path:
            raise ValueError("SQLite URL must include a file path.")

        return Path(parsed.path)

    raise NotImplementedError(
        f"Database backend '{parsed.scheme}' is not supported yet in this module."
    )


def get_backend_name(db_path: str | Path | None = None, db_url: str | None = None) -> str:
    """Return normalized backend name from DB target.

    Returns
    -------
    str
        One of ``sqlite``, ``postgresql``, or the parsed scheme string for
        other DSN types.
    """

    resolved = resolve_db_url(db_path=db_path, db_url=db_url)
    parsed = urlparse(resolved)
    scheme = parsed.scheme or "sqlite"

    if scheme == "sqlite":
        return "sqlite"

    if scheme.startswith("postgresql"):
        return "postgresql"

    return scheme


def create_db_engine(db_path: str | Path | None = None, db_url: str | None = None):
    """Create a SQLAlchemy engine for the provided DB target."""

    try:
        from sqlalchemy import create_engine
    except ImportError as exc:
        raise ImportError("SQLAlchemy is required for DSN-based database engine support.") from exc

    resolved = resolve_db_url(db_path=db_path, db_url=db_url)
    return create_engine(resolved)
