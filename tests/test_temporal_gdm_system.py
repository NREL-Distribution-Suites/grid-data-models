from datetime import datetime
from pathlib import Path
from uuid import UUID
import pytest

from gdm import (
    PhaseCapacitorEquipment, 
    PositiveReactivePower, 
    DistributionSystem, 
    DistributionLoad,
    PhaseLoadEquipment,
    LoadEquipment
)
from infrasys.exceptions import ISNotStored
import gdm
from gdm.time_travel import get_distribution_system_on_date, ModelChange, PropertyEdit




def build_model_updates(system: DistributionSystem)-> list[ModelChange]:
    capacitors =  system.get_components(PhaseCapacitorEquipment)
    capacitor = next(capacitors)

    load1, load2 =  list(system.get_components(DistributionLoad))[:2]
    
    model_changes = [
        ModelChange(
            update_date="2022-01-01",
            edits=[
                PropertyEdit(
                    component_uuid=capacitor.uuid,
                    name="rated_capacity",
                    value=PositiveReactivePower(200, "kvar"),
                )
            ],
        ),
        ModelChange(
            update_date="2023-01-01",
            additions=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        ),
        ModelChange(
            update_date="2024-01-01",
            deletions=[load1.uuid],
        ),
        ModelChange(
            update_date="2025-01-01",
            deletions=[load2.uuid],
        ),
         
    ]
    return model_changes, capacitor.uuid, load1.uuid, load2.uuid


def test_temporal_system(sample_distribution_system_with_timeseries):
    system: DistributionSystem = sample_distribution_system_with_timeseries
    capacitors =  system.get_components(PhaseCapacitorEquipment)
    for capacitor in capacitors:
        capacitor.pprint()
        print(capacitor.uuid)
        break
    
    model_updates, cap_uuid, load_1_uuid, load_2_uuid = build_model_updates(system)

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
        model_changes=model_updates, system=system, catalog=catalog, system_date=system_date
    )

    with pytest.raises(ISNotStored):
        updated_system.get_component_by_uuid(load_1_uuid)
    # # load is added and should exist
    updated_system.get_component_by_uuid(load_2_uuid)
    # #  the model below should exist because we do not apply chages in 2025
    # updated_system.get_component_by_uuid(UUID("53921e63-896b-40fb-930a-cc59446ba1aa"))
    capacitor = updated_system.get_component_by_uuid(cap_uuid)
    assert capacitor.rated_capacity.to("kilovar").magnitude == 200.0
