""" This module contains interface for distribution system capacitor."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.base.distribution_component_base import (
    InServiceDistributionComponentBase,
)
from gdm.distribution.equipment.inverter_equipment import InverterEquipment
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.controllers.distribution_inverter_controller import (
    InverterController
)
from gdm.distribution.equipment.battery_equipment import BatteryEquipment
from gdm.distribution.components.distribution_substation import (
    DistributionSubstation,
)
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import PositiveVoltage

class DistributionBattery(InServiceDistributionComponentBase):
    """Interface for battery system in distribution system models."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this battery is connected to.",
        ),
    ]
    phases: Annotated[
        list[Phase],
        Field(
            ...,
            description=(
                "List of phases at which this battery is connected to in the same order."
            ),
        ),
    ]

    controller: Annotated[
        InverterController | None,
        Field(None, description="Controller settings to control output of the inverter",),
    ]

    inverter: Annotated[
        InverterEquipment, Field(..., description="Inverter equipment for the distribution battery system.")
    ]
    
    equipment: Annotated[BatteryEquipment, Field(..., description="Battery model.")]

    @classmethod
    def aggregate(
        cls,
        instances: list["DistributionBattery"],
        bus: DistributionBus,
        name: str,
        split_phase_mapping: dict[str, set[Phase]],
    ) -> "DistributionBattery":
        phases = set()
        for solar in instances:
            if {Phase.S1, Phase.S2} & set(solar.phases):
                parent_phase = split_phase_mapping[solar.name]
                phases = phases.union(set(parent_phase))
            else:
                phases = phases.union(set(solar.phases))

        return DistributionBattery(
            name=name,
            bus=bus,
            phases=list(phases),
            equipment=BatteryEquipment(
                name=f"{name}_battery_equipment",
                rated_energy=sum(inst.equipment.rated_energy for inst in instances),
                rated_power=sum(inst.equipment.rated_power for inst in instances),
                charging_efficiency=sum(inst.equipment.charging_efficiency for inst in instances) / len(instances),
                discharging_efficiency=sum(inst.equipment.discharging_efficiency for inst in instances) / len(instances),
                idling_efficiency=sum(inst.equipment.idling_efficiency for inst in instances) / len(instances),
            ),
            inverter=InverterEquipment(
                capacity=sum(inst.inverter.capacity for inst in instances) / len(instances),
                rise_limit=None,
                fall_limit=None,
                eff_curve=None,
                cutin_percent=sum(inst.inverter.cutin_percent for inst in instances) / len(instances),
                cutout_percent=sum(
                    inst.inverter.cutout_percent for inst in instances
                ) / len(instances),
            ),
            controller=None,
        )

    @classmethod
    def example(cls) -> "DistributionBattery":
        """Example of a distribution battery system."""
        return DistributionBattery(
            name="pv1",
            bus=DistributionBus(
                voltage_type="line-to-ground",
                name="Battery-DistBus1",
                nominal_voltage=PositiveVoltage(400, "volt"),
                phases=[Phase.A, Phase.B, Phase.C],
                substation=DistributionSubstation.example(),
                feeder=DistributionFeeder.example(),
            ),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            phases=[Phase.A, Phase.B, Phase.C],
            equipment=BatteryEquipment.example(),
            inverter=InverterEquipment.example(),
            controller=None,
        )
