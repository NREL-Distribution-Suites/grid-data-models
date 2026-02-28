# SQL Persistence

GDM supports persisting systems through high-level APIs on `DistributionSystem` and `CatalogSystem`.

Supported database targets:

- SQLite files (via `db_path` or SQLite `db_url`)
- PostgreSQL servers (via `db_url` DSN)

This is useful for:

- storing complete model snapshots,
- preserving component UUID identity across save/load cycles,
- loading distribution systems with `prefer_normalized=True`,
- keeping normalized distribution table structure aligned across SQLite and PostgreSQL.

## DistributionSystem: write and load

```python
from gdm.distribution import DistributionSystem

# write using a file path
system: DistributionSystem = ...
system.to_db("distribution.sqlite")

# load (default snapshot path)
loaded = DistributionSystem.from_db("distribution.sqlite")

# write/load using SQLite URL
sqlite_url = "sqlite:///distribution.sqlite"
system.to_db(db_url=sqlite_url)
loaded = DistributionSystem.from_db(db_url=sqlite_url)

# write/load using PostgreSQL DSN
postgres_url = "postgresql+psycopg://user:password@host:5432/database"
system.to_db(db_url=postgres_url)
loaded = DistributionSystem.from_db(db_url=postgres_url)
```

By default, `to_db` writes snapshot payloads. For distribution systems, normalized tables are also persisted.

## Backend behavior

### Distribution systems

- SQLite: writes snapshot payload + normalized distribution tables.
- PostgreSQL: writes snapshot payload + normalized distribution tables, with table names and relational layout aligned to SQLite.

`prefer_normalized=True` is supported on both backends for `DistributionSystem.from_db(...)`.

### Catalog systems

- SQLite and PostgreSQL both use snapshot storage.

### Load from normalized representation

Use `prefer_normalized=True` to reconstruct from normalized topology/component tables first.

```python
loaded = DistributionSystem.from_db(
    db_url="postgresql+psycopg://user:password@host:5432/database",
    prefer_normalized=True,
)
```

If normalized rows are unavailable for the stored system, loading falls back to snapshot reconstruction.

## CatalogSystem: write and load

```python
from gdm.distribution import CatalogSystem

catalog: CatalogSystem = ...
catalog.to_db("catalog.sqlite")

loaded_catalog = CatalogSystem.from_db("catalog.sqlite")

catalog.to_db(db_url="postgresql+psycopg://user:password@host:5432/database")
loaded_catalog = CatalogSystem.from_db(
    db_url="postgresql+psycopg://user:password@host:5432/database"
)
```

`CatalogSystem` persistence uses snapshot storage.

## Replace semantics and schema initialization

For both system types, writes replace existing records for that `system_kind` by default.

- `replace=True` (default): replace previously persisted record(s) for that system kind.
- `initialize_schema=True` (default): bootstrap schema/tables when needed.

In repeated writes to an existing database, `initialize_schema=False` can be used once schema is already present.

## Table-structure parity notes (SQLite vs PostgreSQL)

For distribution persistence, PostgreSQL now materializes the same normalized table set used in SQLite (for example, `distribution_buses`, `distribution_loads`, `matrix_impedance_branches`, and related component/equipment tables). This keeps SQL inspection and downstream table-based workflows consistent across backends.

GDM additive tables (`gdm_system_snapshots`, `gdm_metadata`, `gdm_component_uuid_map`) remain backend-managed and are available on both SQLite and PostgreSQL.

## Time series behavior

When persisting a `DistributionSystem`, time-series associations are stored in DB metadata tables, and loading restores component time-series attachments from persisted snapshot data.

## Inspecting stored snapshot payloads

For diagnostics, raw snapshot payload can be inspected via `gdm.db.load_snapshot_payload`.

```python
from gdm.db import load_snapshot_payload

payload = load_snapshot_payload(
    db_url="postgresql+psycopg://user:password@host:5432/database",
    system_kind="distribution",
)
```

For metadata-only inspection, `gdm.db.inspect_snapshot_metadata` is also available.

```python
from gdm.db import inspect_snapshot_metadata

metadata = inspect_snapshot_metadata(db_path="distribution.sqlite")
```

## Local PostgreSQL test setup

If you run persistence tests locally against PostgreSQL, set a DSN environment variable used by the test fixtures:

```bash
export GDM_TEST_POSTGRES_DSN='postgresql+psycopg://postgres:postgres@localhost:5432/gdm_test'
```

Then run DB persistence tests:

```bash
pytest -q tests/test_db_io.py -k postgres_dsn
```
