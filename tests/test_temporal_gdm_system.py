from datetime import datetime
from pathlib import Path
from uuid import UUID
import pytest

from gdm import DistributionSystem, PositiveReactivePower, LoadEquipment
from infrasys.exceptions import ISNotStored
import gdm
from gdm.time_travel import get_distribution_system_on_date, ModelChange, PropertyEdit


gdm_path = Path(gdm.__file__).parent.parent.parent
model_path = gdm_path / "tests" / "data" / "p10_gdm.json"

model_updates = [
    ModelChange(
        update_date="2022-01-01",
        edits=[
            PropertyEdit(
                component_uuid="e4e4d756-d52c-4e9a-9110-d3b008cec42a",
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
        deletions=["03ff2c0a-348c-43fe-a79a-48557a8be23e"],
    ),
    ModelChange(
        update_date="2025-01-01",
        deletions=["53921e63-896b-40fb-930a-cc59446ba1aa"],
    ),
]


def test_temporal_system():
    system = DistributionSystem.from_json(filename=model_path, auto_add_composed_components=True)

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
        updated_system.get_component_by_uuid(UUID("03ff2c0a-348c-43fe-a79a-48557a8be23e"))
    # load is added and should exist
    updated_system.get_component_by_uuid(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    #  the model below should exist because we do not apply chages in 2025
    updated_system.get_component_by_uuid(UUID("53921e63-896b-40fb-930a-cc59446ba1aa"))
    capacitor = updated_system.get_component_by_uuid(UUID("e4e4d756-d52c-4e9a-9110-d3b008cec42a"))
    assert capacitor.rated_capacity.to("kilovar").magnitude == 200.0
