""" This module contains interface for distribution load."""

from typing import Annotated

from pydantic import model_validator, Field
from infrasys import Component

from gdm.distribution.distribution_enum import Phase
from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.quantities import PositiveVoltage
from gdm.distribution.equipment.load_equipment import LoadEquipment


class DistributionLoad(Component):
    """Interface for distribution load."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this load is connected to.",
        ),
    ]
    belongs_to: BELONG_TO_TYPE
    phases: Annotated[
        list[Phase],
        Field(..., description="Phases to which this load is connected to."),
    ]
    equipment: Annotated[LoadEquipment, Field(..., description="Load model.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionLoad":
        """Custom validator for fields in distribution load."""
        if not set(self.phases).issubset(set(self.bus.phases)):
            msg = f"Loads phases {self.phases=} must be subset of bus phases. {self.bus.phases}"
            raise ValueError(msg)

        if len(self.phases) != len(self.equipment.phase_loads):
            msg = (
                f"Number of phases {self.phases=} did not "
                f"match number of phase loads {self.equipment.phase_loads=}"
            )
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "DistributionLoad":
        """Example for distribution load."""
        return DistributionLoad(
            name="DistributionLoad1",
            bus=DistributionBus(
                voltage_type="line-to-ground",
                name="Bus1",
                phases=[Phase.A, Phase.B, Phase.C],
                nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
            ),
            phases=[Phase.A, Phase.B, Phase.C],
            equipment=LoadEquipment.example(),
        )
