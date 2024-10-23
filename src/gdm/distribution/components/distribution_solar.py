""" This module contains interface for distribution system capacitor."""

from typing import Annotated

from pydantic import Field

from gdm.quantities import PositiveVoltage
from gdm.distribution.distribution_enum import Phase
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.base.distribution_component_base import (
    DistributionComponentBase,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import (
    DistributionSubstation,
)
from gdm.distribution.controllers.distribution_inverter_controller import (
    VoltVarInverterController,
)
from gdm.distribution.controllers.base.inverter_controller_base import (
    InverterControllerBase,
)
from gdm.distribution.equipment.solar_equipment import SolarEquipment


class DistributionSolar(DistributionComponentBase):
    """Interface for Solar PV system in distribution system models."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this solar array is connected to.",
        ),
    ]
    phases: Annotated[
        list[Phase],
        Field(
            ...,
            description=(
                "List of phases at which this solar array is connected to in the same order."
            ),
        ),
    ]
    controller: Annotated[
        InverterControllerBase,
        Field(
            ...,
            description="The controller which is used for the PV array.",
        ),
    ]

    equipment: Annotated[SolarEquipment, Field(..., description="Solar PV model.")]

    @classmethod
    def aggregate(
        cls,
        instances: list["DistributionSolar"],
        bus: DistributionBus,
        name: str,
        split_phase_mapping: dict[str, set[Phase]],
    ) -> "DistributionSolar":
        phases = set()
        for solar in instances:
            if {Phase.S1, Phase.S2} & set(solar.phases):
                parent_phase = split_phase_mapping[solar.uuid]
                phases = phases.union(set(parent_phase))
            else:
                phases = phases.union(set(solar.phases))

        return DistributionSolar(
            name=name,
            bus=bus,
            phases=list(phases),
            equipment=SolarEquipment(
                name=f"{name}_solar_equipment",
                rated_capacity=sum(inst.equipment.rated_capacity for inst in instances),
                solar_power=sum(inst.equipment.rated_capacity for inst in instances),
                resistance=1
                / sum(
                    (1 / inst.equipment.resistance if inst.equipment.resistance else 0)
                    for inst in instances
                ),
                reactance=1
                / sum(
                    (1 / inst.equipment.reactance if inst.equipment.reactance else 0)
                    for inst in instances
                ),
                cutin_percent=sum(inst.equipment.cutin_percent for inst in instances)
                / len(instances),
                cutout_percent=sum(inst.equipment.cutout_percent for inst in instances)
                / len(instances),
            ),
        )

    @classmethod
    def example(cls) -> "DistributionSolar":
        """Example for a Solar PV"""
        return DistributionSolar(
            name="pv1",
            bus=DistributionBus(
                voltage_type="line-to-ground",
                name="Solar-DistBus1",
                nominal_voltage=PositiveVoltage(400, "volt"),
                phases=[Phase.A, Phase.B, Phase.C],
                substation=DistributionSubstation.example(),
                feeder=DistributionFeeder.example(),
            ),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            phases=[Phase.A, Phase.B, Phase.C],
            equipment=SolarEquipment.example(),
            controller=VoltVarInverterController.example(),
        )
