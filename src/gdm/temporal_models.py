from datetime import date
from typing import Any

from pydantic import field_validator
from gdm.distribution.distribution_system import DistributionSystem
from rich.console import Console
from infrasys import Component
from rich.table import Table
from loguru import logger
from uuid import UUID


class PropertyEdit(Component):
    name: str
    value: Any
    component_uuid: UUID


class ModelUpdate(Component):
    name: str = ""
    update_date: date
    additions: list[UUID] = []
    edits: list[PropertyEdit] = []
    deletions: list[UUID] = []


class ModelUpdates(Component):
    updates: list[ModelUpdate] = []

    @field_validator("updates")
    @classmethod
    def sort_updates_in_chronological_order(cls, v: list[ModelUpdate]) -> str:
        return sorted(v, key=lambda x: x.update_date, reverse=False)


def _update_temporal_table(
    updates: list, update_date: date, change_type: str, component: Component
):
    updates.append(
        [
            str(update_date),
            change_type,
            str(component.uuid),
            component.label.split(".")[0],
            component.name,
        ]
    )


def get_distribution_system_on_date(
    model_updates: ModelUpdates,
    system: DistributionSystem,
    catalog: DistributionSystem,
    system_date: date,
) -> DistributionSystem:
    log = []
    for model_update in model_updates.updates:
        if model_update.update_date <= system_date:
            logger.info(f"Modification applied at timestamp: {model_update.update_date}")
            for model_uuid in model_update.additions:
                component = catalog.get_component_by_uuid(model_uuid)
                system.add_component(component)
                _update_temporal_table(log, model_update.update_date, "Addition", component)
            for model_uuid in model_update.deletions:
                component = system.get_component_by_uuid(model_uuid)
                system.remove_component(component)
                print(f"Deletion: {model_uuid}")
                _update_temporal_table(log, model_update.update_date, "Deletion", component)
            for edit_model in model_update.edits:
                component = system.get_component_by_uuid(edit_model.component_uuid)
                if not hasattr(component, edit_model.name):
                    raise AttributeError(
                        f"{component.label} does not have a property called {edit_model.name}"
                    )
                setattr(component, edit_model.name, edit_model.value)
                _update_temporal_table(log, model_update.update_date, "Edit", component)
    _system_update_info(model_updates, log)
    return system


def _system_update_info(scenario: ModelUpdates, update_log: list[str]):
    table = Table(title=f"Updates applied to system from scenario '{scenario.name}'")
    table.add_column("Timestamp", justify="right", style="cyan", no_wrap=True)
    table.add_column("Operation", style="magenta")
    table.add_column("UUID", justify="right", style="bright_magenta")
    table.add_column("Component Type", justify="right", style="cyan")
    table.add_column("Component Name", justify="right", style="green")

    for log in update_log:
        table.add_row(*log)

    console = Console()
    console.print(table)
    return
