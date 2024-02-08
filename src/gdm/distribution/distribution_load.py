""" This module contains interface for distribution load."""

from typing import Annotated, Optional

from pydantic import PositiveInt, model_validator, Field
from infrasys.component_models import ComponentWithQuantities

from gdm.distribution.distribution_enum import ConnectionType, Phase
from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.distribution_bus import DistributionBus
from gdm.quantities import PositiveVoltage
from gdm.load import PowerSystemLoad


class PhaseLoadEquipment(PowerSystemLoad):
    """Interface for single phase load equipment."""

    num_customers: Annotated[
        Optional[PositiveInt],
        Field(None, description="Number of customers for this load"),
    ]

    @classmethod
    def example(cls) -> "PhaseLoadEquipment":
        """Example for phase load."""
        base_load = PowerSystemLoad.example()
        return PhaseLoadEquipment(
            name=base_load.name,
            z_real=base_load.z_real,
            z_imag=base_load.z_imag,
            i_real=base_load.i_real,
            i_imag=base_load.i_imag,
            p_real=base_load.p_real,
            p_imag=base_load.p_imag,
        )


class LoadEquipment(ComponentWithQuantities):
    """Interface for load model."""

    phase_loads: Annotated[
        list[PhaseLoadEquipment], Field(..., description="List of phase loads.")
    ]
    connection_type: Annotated[
        ConnectionType,
        Field(ConnectionType.STAR, description="Connection type for multi phase load."),
    ]

    @classmethod
    def example(cls) -> "LoadEquipment":
        """Example for load model."""
        phase_loads = [PhaseLoadEquipment.example()] * 3
        return LoadEquipment(
            name="Load Eqiup 1",
            phase_loads=phase_loads,
            connection_type=ConnectionType.STAR,
        )


class DistributionLoad(ComponentWithQuantities):
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
