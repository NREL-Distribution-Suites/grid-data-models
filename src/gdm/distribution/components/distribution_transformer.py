""" This module contains interface for distribution transformer."""

import math
from typing import Annotated

from infrasys import Component
from infrasys.quantities import Voltage
from pydantic import Field, model_validator

from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.distribution_enum import Phase, VoltageTypes
from gdm.quantities import PositiveVoltage
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.equipment.distribution_transformer_equipment import (
    DistributionTransformerEquipment,
)


def get_phase_voltage_in_kv(
    voltage: Voltage, voltage_type: VoltageTypes, split_phase_secondary: bool = False
) -> Voltage:
    """Function to return phase voltage"""
    kv_voltage = voltage.to("kilovolt")
    factor = math.sqrt(3) if not split_phase_secondary else 2
    return kv_voltage / factor if voltage_type == VoltageTypes.LINE_TO_LINE else kv_voltage


class DistributionTransformer(Component):
    """Interface for distribution transformer."""

    belongs_to: BELONG_TO_TYPE

    buses: Annotated[
        list[DistributionBus],
        Field(
            ...,
            description="List of distribution buses in the same order as windings. ",
        ),
    ]
    winding_phases: Annotated[
        list[list[Phase]],
        Field(
            ...,
            description="""List of phases for each winding, using the winding
            order defined in the DistributionTransformerModel""",
        ),
    ]

    equipment: Annotated[
        DistributionTransformerEquipment,
        Field(..., description="Transformer info object."),
    ]

    def _check_if_voltage_is_on_split_side(self, voltage: Voltage) -> bool:
        """Internal method to check if winding is on split side."""
        if not self.equipment.is_center_tapped:
            return False

        all_voltages = [item.nominal_voltage for item in self.equipment.windings]
        return voltage < max(all_voltages)

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionTransformer":
        """Custom validator for distribution transformer."""
        if len(self.winding_phases) != len(self.equipment.windings):
            msg = (
                f"Number of windings {len(self.equipment.windings)} must be equal to "
                f"numbe of winding phases {len(self.winding_phases)}"
            )
            raise ValueError(msg)

        for wdg, pw_phases in zip(self.equipment.windings, self.winding_phases):
            pw_phases_length = len(pw_phases) - 1 if Phase.N in pw_phases else len(pw_phases)

            if pw_phases_length > wdg.num_phases and pw_phases_length != 2:
                msg = (
                    f"Number of phases in windings {wdg.num_phases=} must be "
                    f"less than or equal to phases {pw_phases=}"
                )
                raise ValueError(msg)
            elif pw_phases_length == 2 and wdg.num_phases != 1:
                msg = (
                    f"For a single phase delta connected transformer, {pw_phases=}"
                    f" inconsistant number of phases provided for winding {wdg.num_phases=}"
                )
                raise ValueError(msg)

        for bus, pw_phases in zip(self.buses, self.winding_phases):
            if not (set(pw_phases) - set(Phase.N)).issubset(bus.phases):
                msg = (
                    f"Winding phases {pw_phases=}"
                    f" must be subset of bus phases ({bus.phases=})."
                )
                raise ValueError(msg)

        for bus, wdg in zip(self.buses, self.equipment.windings):
            bus_phase_voltage = get_phase_voltage_in_kv(
                bus.nominal_voltage,
                bus.voltage_type,
                split_phase_secondary=self._check_if_voltage_is_on_split_side(bus.nominal_voltage),
            )
            wdg_phase_voltage = get_phase_voltage_in_kv(
                wdg.nominal_voltage,
                wdg.voltage_type,
                split_phase_secondary=self._check_if_voltage_is_on_split_side(wdg.nominal_voltage),
            )
            if not (0.85 * bus_phase_voltage <= wdg_phase_voltage <= 1.15 * bus_phase_voltage):
                msg = (
                    f"Nominal voltage of transformer {wdg_phase_voltage}"
                    f" must be within 15% range of"
                    f" bus nominal voltage {bus_phase_voltage}"
                )
                raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "DistributionTransformer":
        """Example for distribution transformer."""
        return DistributionTransformer(
            name="DistributionTransformer1",
            buses=[
                DistributionBus(
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                    name="Bus1",
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
                DistributionBus(
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                    name="Bus2",
                    nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
            ],
            winding_phases=[[Phase.A, Phase.B, Phase.C], [Phase.A, Phase.B, Phase.C]],
            equipment=DistributionTransformerEquipment.example(),
        )
