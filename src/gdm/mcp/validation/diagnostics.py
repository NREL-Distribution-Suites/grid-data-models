"""Diagnostic tools for identifying validation errors in distribution systems."""

import traceback
from typing import Any
from uuid import UUID

from gdm.distribution import DistributionSystem

from gdm.hashing_utils import hash_model

from gdm.mcp.schemas import (
    ErrorType,
    ValidationIssue,
    ValidationReport,
)


def _run_core_validators(component: Any) -> None:
    """Run the library's core validation hooks on a live component.

    Delegates to the pydantic ``model_validator`` methods that the library
    defines on its component classes (e.g. ``validate_fields``,
    ``validate_fields_base``, ``validate_controller_types``). These are the
    authoritative semantic checks for components; they raise ``ValueError`` for
    invalid components.
    """
    for klass in type(component).__mro__:
        for method_name, method in vars(klass).items():
            if not method_name.startswith("validate"):
                continue
            if not getattr(method, "__module__", "").startswith("gdm"):
                continue
            getattr(component, method_name)()


def diagnose_system(system: DistributionSystem) -> ValidationReport:
    """
    Diagnose a distribution system for validation errors.

    Validation is delegated to the library's core validation instead of a
    hand-rolled policy: every component is checked through the library's own
    pydantic ``model_validator`` hooks (e.g. ``validate_fields`` /
    ``validate_fields_base``) via :func:`_run_core_validators`. Components that
    are stored more than once (identical full content, including name and uuid)
    are reported using :func:`gdm.hashing_utils.hash_model`.

    Args:
        system: DistributionSystem to diagnose

    Returns:
        ValidationReport with all identified issues
    """
    issues: list[ValidationIssue] = []
    total_components = 0
    valid_components = 0
    seen_full_hashes: set[int] = set()

    for component in system.iter_all_components():
        total_components += 1
        component_uuid = (
            component.uuid if isinstance(component.uuid, UUID) else UUID(component.uuid)
        )
        component_type = component.__class__.__name__
        component_name = component.name

        try:
            # Library core validation.
            _run_core_validators(component)

            # Duplicate check via the library hashing utility: a repeating
            # full-content hash (including name and uuid) means the same
            # component is stored more than once in the system.
            full_hash = hash_model(component, key_names=[])
            if full_hash in seen_full_hashes:
                issues.append(
                    ValidationIssue(
                        component_uuid=component_uuid,
                        component_type=component_type,
                        component_name=component_name,
                        field_path="",
                        error_type=ErrorType.INVALID_VALUE,
                        message=(
                            f"Duplicate component detected: {component_type} "
                            f"'{component_name}' is stored more than once in the system"
                        ),
                    )
                )
            else:
                seen_full_hashes.add(full_hash)
                valid_components += 1

        except ValueError as e:
            # The library core validators raise ValueError on invalid components.
            issues.append(
                ValidationIssue(
                    component_uuid=component_uuid,
                    component_type=component_type,
                    component_name=component_name,
                    field_path="",
                    error_type=ErrorType.PYDANTIC_VALIDATION,
                    message=str(e),
                )
            )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    component_uuid=component_uuid,
                    component_type=component_type,
                    component_name=component_name,
                    field_path="unknown",
                    error_type=ErrorType.OTHER,
                    message=f"Unexpected error: {str(e)}\n{traceback.format_exc()}",
                )
            )

    return ValidationReport(
        system_name=system.name,
        total_components=total_components,
        valid_components=valid_components,
        invalid_components=total_components - valid_components,
        issues=issues,
    )
