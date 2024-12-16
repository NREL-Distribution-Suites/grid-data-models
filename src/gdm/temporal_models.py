from datetime import date
from typing import Any

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


class ModelChange(Component):
    name: str = ""
    update_date: date
    additions: list[UUID] = []
    edits: list[PropertyEdit] = []
    deletions: list[UUID] = []


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
    model_changes: list[ModelChange],
    system: DistributionSystem,
    catalog: DistributionSystem,
    system_date: date,
) -> DistributionSystem:
    """
    Updates the distribution system based on a list of model changes up to a specified date.

    Parameters
    ----------
    model_changes : list[ModelChange]
        List of changes to apply to the system.
    system : DistributionSystem
        The system to update.
    catalog : DistributionSystem
        Catalog from which components can be added.
    system_date : date
        The date up to which changes should be applied.

    Returns
    -------
    DistributionSystem
        Updated distribution system.
    """
    log = []  # Initialize a log for tracking updates.
    # Sort model changes by update date in ascending order.
    log = []
    model_changes = sorted(model_changes, key=lambda x: x.update_date, reverse=False)
    # Filter changes that occurred on or before the specified date.
    filtered_model_changes = list(filter(lambda x: x.update_date <= system_date, model_changes))

    for model_update in filtered_model_changes:
        logger.info(f"Modification applied at timestamp: {model_update.update_date}")

        # Process additions: Add new components from the catalog to the system.
        for model_uuid in model_update.additions:
            component = catalog.get_component_by_uuid(model_uuid)
            system.add_component(component)
            _update_temporal_table(log, model_update.update_date, "Addition", component)

        # Process deletions: Remove components from the system.
        for model_uuid in model_update.deletions:
            component = system.get_component_by_uuid(model_uuid)
            system.remove_component(component)
            print(f"Deletion: {model_uuid}")
            _update_temporal_table(log, model_update.update_date, "Deletion", component)

        # Process edits: Update component attributes.
        for edit_model in model_update.edits:
            component = system.get_component_by_uuid(edit_model.component_uuid)
            if not hasattr(component, edit_model.name):
                raise AttributeError(
                    f"{component.label} does not have a property called {edit_model.name}"
                )
            setattr(component, edit_model.name, edit_model.value)
            _update_temporal_table(log, model_update.update_date, "Edit", component)

    # Log the system updates.
    _system_update_info("", log)
    return system


def _system_update_info(scenario_name: str, update_log: list[str]):
    table = Table(title=f"Updates applied to system from scenario '{scenario_name}'")
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
