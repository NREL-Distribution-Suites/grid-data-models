"""This module contains dataset store."""

from typing import Any
from uuid import UUID

from infrasys.system import System
from infrasys.component_models import Component

from gdm.exceptions import GDMNotAttachedToSystemError, GDMIncompatibleInstanceError
from gdm.dataset.cost_model import CostModel
import gdm


class DatasetSystem(System):
    """Class interface for dataset system."""

    def __init__(self, *args, catalog_cost_mapping: dict[str, list[str]] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_format_version = gdm.distribution.__version__
        self.catalog_cost_mapping = catalog_cost_mapping or {}

    def serialize_system_attributes(self) -> dict[str, Any]:
        """Method to serialize system attributes."""
        return {"catalog_cost_mapping": self.catalog_cost_mapping}

    def deserialize_system_attributes(self, data: dict[str, Any]) -> None:
        """Method to deserialize system attributes."""
        self.catalog_cost_mapping = data["catalog_cost_mapping"]

    def add_cost(self, catalog: Component, cost: CostModel):
        """Method to add cost to catalog."""
        if not catalog.is_attached(system_uuid=self.uuid):
            msg = f"Catalog not attached to the system {catalog=}"
            raise GDMNotAttachedToSystemError(msg)

        if isinstance(catalog, CostModel):
            msg = f"Catalog can not be an instance of cost model {catalog=}"
            raise GDMIncompatibleInstanceError(msg)

        self.add_component(cost)
        cost = self.get_component(CostModel, name=cost.name)
        catalog_uuid = str(catalog.uuid)
        cost_uuid = str(cost.uuid)

        if catalog_uuid not in self.catalog_cost_mapping:
            self.catalog_cost_mapping[catalog_uuid] = []

        if cost_uuid not in self.catalog_cost_mapping[catalog_uuid]:
            self.catalog_cost_mapping[catalog_uuid].append(cost_uuid)

    def add_costs(self, catalog: Component, costs: list[CostModel]):
        """Method to add cost to catalog."""
        for cost in costs:
            self.add_cost(catalog, cost)

    def get_costs(self, catalog: Component) -> list[CostModel]:
        """Get costs for a catalog."""

        if not catalog.is_attached(system_uuid=self.uuid):
            msg = f"Catalog not attached to the system {catalog=}"
            raise GDMNotAttachedToSystemError(msg)

        catalog_uuid = str(catalog.uuid)
        if catalog_uuid not in self.catalog_cost_mapping:
            return []

        return [
            self.get_component_by_uuid(UUID(cost_uuid))
            for cost_uuid in self.catalog_cost_mapping[catalog_uuid]
        ]

    def remove_cost(self, catalog: Component, cost: CostModel):
        """Remove cost from catalog."""

        if not catalog.is_attached(system_uuid=self.uuid):
            msg = f"Catalog not attached to the system {catalog=}"
            raise GDMNotAttachedToSystemError(msg)

        if not cost.is_attached(system_uuid=self.uuid):
            msg = f"Cost not attached to the system {cost=}"
            raise GDMNotAttachedToSystemError(msg)

        self.remove_component(cost)

        catalog_uuid = str(catalog.uuid)
        cost_uuid = str(cost.uuid)

        if (
            str(catalog_uuid) in self.catalog_cost_mapping
            and cost_uuid in self.catalog_cost_mapping[catalog_uuid]
        ):
            self.catalog_cost_mapping[catalog_uuid].remove(cost_uuid)
