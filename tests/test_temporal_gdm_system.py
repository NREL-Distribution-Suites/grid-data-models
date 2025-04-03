from datetime import datetime
from uuid import UUID
import pytest

from gdm.distribution.components import DistributionLoad
from gdm.quantities import PositiveReactivePower
from gdm.distribution import DistributionSystem
from gdm.distribution.equipment import (
    PhaseCapacitorEquipment,
    LoadEquipment,
)
from infrasys.exceptions import ISNotStored
from gdm.temporal_models import (
    get_distribution_system_on_date,
    SystemModification,
    UpdateScenario,
    PropertyEdit,
)


def build_model_updates(system: DistributionSystem) -> UpdateScenario:
    capacitor = next(system.get_components(PhaseCapacitorEquipment))

    load1, load2 = list(system.get_components(DistributionLoad))[:2]
    update_scenario = UpdateScenario(
        name="Test scenario",
        modifications=[
            SystemModification(
                update_date="2022-01-01",
                edits=[
                    PropertyEdit(
                        component_uuid=capacitor.uuid,
                        name="rated_reactive_power",
                        value=PositiveReactivePower(200, "kvar"),
                    )
                ],
            ),
            SystemModification(
                update_date="2023-01-01",
                additions=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
            ),
            SystemModification(
                update_date="2024-01-01",
                deletions=[load1.uuid],
            ),
            SystemModification(
                update_date="2025-01-01",
                deletions=[load2.uuid],
            ),
        ],
    )

    return update_scenario, capacitor.uuid, load1.uuid, load2.uuid


def test_temporal_system(distribution_system_with_single_timeseries):
    system: DistributionSystem = distribution_system_with_single_timeseries

    update_scenario, cap_uuid, load_1_uuid, load_2_uuid = build_model_updates(system)

    catalog = DistributionSystem(auto_add_composed_components=True)
    load_equipment = LoadEquipment.example().model_copy(
        update={
            "uuid": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            "name": "added_phase_load_model",
        }
    )
    catalog.add_component(load_equipment)

    system_date = datetime.strptime("2024-1-1", "%Y-%m-%d").date()
    updated_system = get_distribution_system_on_date(
        update_scenario=update_scenario, system=system, catalog=catalog, system_date=system_date
    )

    with pytest.raises(ISNotStored):
        updated_system.get_component_by_uuid(load_1_uuid)
    # load is added and should exist
    updated_system.get_component_by_uuid(load_2_uuid)
    #  the model below should exist because we do not apply chages in 2025
    updated_system.get_component_by_uuid(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    capacitor = updated_system.get_component_by_uuid(cap_uuid)
    assert capacitor.rated_reactive_power.to("kilovar").magnitude == 200.0
