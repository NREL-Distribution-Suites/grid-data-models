import importlib.metadata
from pathlib import Path

from infrasys import System


class CatalogSystem(System):
    """Class interface for catalog system."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_format_version = importlib.metadata.version("grid-data-models")

    def to_db(
        self,
        db_path: str | Path,
        schema_path: str | Path | None = None,
        replace: bool = True,
        initialize_schema: bool = True,
    ) -> None:
        """Persist the catalog system to a SQLite database."""
        from gdm.db import write_system_to_db

        write_system_to_db(
            system=self,
            db_path=db_path,
            schema_path=schema_path,
            replace=replace,
            initialize_schema=initialize_schema,
            system_kind="catalog",
        )

    @classmethod
    def from_db(cls, db_path: str | Path) -> "CatalogSystem":
        """Load a catalog system from a SQLite database."""
        from gdm.db import load_system_from_db

        return load_system_from_db(system_cls=cls, db_path=db_path, system_kind="catalog")
