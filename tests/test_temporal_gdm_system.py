from datetime import datetime
from uuid import uuid4, UUID
from pathlib import Path
import pytest

from gdm.temporal_models import (
    ModelUpdates,
    TemporalUpdates,
    AdditionModel,
    DeletionModel,
    EditModel,
)
from gdm import DistributionSystem, PositiveReactivePower, DistributionLoad

from infrasys.exceptions import ISNotStored

import gdm


gdm_path = Path(gdm.__file__).parent.parent.parent
model_path = gdm_path / "tests" / "data" / "p10_gdm.json"

model_updates = ModelUpdates(
    name="update_scnenario_1",
    updates=[
        TemporalUpdates(
            date="2022-01-01",
            deletions=[DeletionModel(component_uuid="6468a8aa-47cf-4a66-bd4c-e2d6e9815959")],
        ),
        TemporalUpdates(
            date="2023-01-01",
            edits=[
                EditModel(
                    component_uuid="e4e4d756-d52c-4e9a-9110-d3b008cec42a",
                    component_parameters={
                        "rated_capacity": PositiveReactivePower(value=200.0, units="kilovar")
                    },
                )
            ],
        ),
        TemporalUpdates(
            date="2024-01-01",
            deletions=[DeletionModel(component_uuid="f8c440fe-d661-41f2-8f77-cc397e931fee")],
        ),
        TemporalUpdates(
            date="2025-01-01",
            deletions=[DeletionModel(component_uuid="8cbd036f-1b27-4881-9134-4cb69fd08924")],
        ),
    ],
)


def test_temporal_system():
    system = DistributionSystem.from_json(model_path, auto_add_composed_components=True)
    system.info()
    system.add_component(model_updates)

    load_component = system.get_component_by_uuid(UUID("44d1ffde-cd54-44a4-ab40-b13ada4af68d"))
    load_component = load_component.copy(update={"name": "test_load", "uuid": uuid4()})

    model_updates.updates[-2].additions.append(AdditionModel(component=load_component))
    model_date = datetime.strptime("2024-1-1", "%Y-%m-%d").date()
    system.apply_updates_at_timestamp(date=model_date, update_scenario="update_scnenario_1")

    with pytest.raises(ISNotStored):
        system.get_component_by_uuid(UUID("6468a8aa-47cf-4a66-bd4c-e2d6e9815959"))
        system.get_component_by_uuid(UUID("f8c440fe-d661-41f2-8f77-cc397e931fee"))
    #  the model below should exist because we do not apply chages in 2025
    system.get_component_by_uuid(UUID("8cbd036f-1b27-4881-9134-4cb69fd08924"))
    # load is added and should exist
    system.get_component(DistributionLoad, "test_load")

    capacitor = system.get_component_by_uuid(UUID("e4e4d756-d52c-4e9a-9110-d3b008cec42a"))
    assert capacitor.rated_capacity.to("kilovar").magnitude == 200.0
