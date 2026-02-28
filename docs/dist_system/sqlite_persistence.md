# SQLite Persistence

GDM supports persisting systems directly to SQLite through high-level APIs on `DistributionSystem` and `CatalogSystem`.

This is useful for:

- storing complete model snapshots in a single database file,
- preserving component UUID identity across save/load cycles,
- loading from a normalized relational representation for faster selective reconstruction.

## DistributionSystem: write and load

```python
from gdm.distribution import DistributionSystem

# write
system: DistributionSystem = ...
system.to_db("distribution.sqlite")

# load (default snapshot path)
loaded = DistributionSystem.from_db("distribution.sqlite")
```

By default, `to_db` writes a snapshot payload and normalized distribution tables.

### Load from normalized representation

Use `prefer_normalized=True` to reconstruct from normalized topology/component tables first.

```python
loaded = DistributionSystem.from_db(
    "distribution.sqlite",
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
```

`CatalogSystem` persistence uses snapshot storage.

## Replace semantics and schema initialization

For both system types, writes replace existing records for that `system_kind` by default.

- `replace=True` (default): replace previously persisted record(s) for that system kind.
- `initialize_schema=True` (default): bootstrap schema/tables when needed.

In repeated writes to an existing database, `initialize_schema=False` can be used once schema is already present.

## Time series behavior

When persisting a `DistributionSystem`, time-series associations are stored in DB metadata tables, and loading restores component time-series attachments from persisted snapshot data.

## Inspecting stored snapshot payloads

For diagnostics, raw snapshot payload can be inspected via `gdm.db.sqlite_store.load_snapshot_payload`.

```python
from gdm.db.sqlite_store import load_snapshot_payload

payload = load_snapshot_payload("distribution.sqlite", system_kind="distribution")
```

For metadata-only inspection, `gdm.db.sqlite_store_schema.inspect_snapshot_metadata` is also available.
