"""Helpers for transferring component graphs between systems."""

from copy import deepcopy
from collections.abc import Iterable

from infrasys import Component


def clone_components(
    components: Iterable[Component],
) -> tuple[list[Component], dict[int, Component]]:
    """Deep-copy components, clear system-local IDs, and map source IDs to clones."""
    component_copies = deepcopy(list(components))
    copies_by_source_id: dict[int, Component] = {}
    visited: set[int] = set()

    def clear_ids(component: Component) -> None:
        identity = id(component)
        if identity in visited:
            return
        visited.add(identity)

        if component.id is not None:
            copies_by_source_id[component.id] = component
        component.id = None

        for field in type(component).model_fields:
            value = getattr(component, field)
            if isinstance(value, Component):
                clear_ids(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, Component):
                        clear_ids(item)

    for component in component_copies:
        clear_ids(component)

    return component_copies, copies_by_source_id


def _rebind_component_list(
    values: list,
    replacements: dict[int, Component],
    visited: set[int],
) -> tuple[list, bool]:
    rebound_values = []
    changed = False
    for item in values:
        if not isinstance(item, Component):
            rebound_values.append(item)
            continue

        replacement = replacements.get(id(item))
        if replacement is None:
            _rebind_component(item, replacements, visited)
            rebound_values.append(item)
            continue

        rebound_values.append(replacement)
        changed = changed or replacement is not item

    return rebound_values, changed


def _rebind_component(
    component: Component,
    replacements: dict[int, Component],
    visited: set[int],
) -> None:
    identity = id(component)
    if identity in visited:
        return
    visited.add(identity)

    for field in type(component).model_fields:
        value = getattr(component, field)
        if isinstance(value, Component):
            replacement = replacements.get(id(value))
            if replacement is None:
                _rebind_component(value, replacements, visited)
            else:
                setattr(component, field, replacement)
        elif isinstance(value, list):
            rebound_values, changed = _rebind_component_list(value, replacements, visited)
            if changed:
                setattr(component, field, rebound_values)


def rebind_component_references(
    components: Iterable[Component],
    replacements: dict[int, Component],
) -> None:
    """Replace references to cloned components while preserving the graph structure."""
    visited: set[int] = set()
    for component in components:
        _rebind_component(component, replacements, visited)
