"""This module contains distribution regulator."""

from typing import Annotated

from pydantic import Field, model_validator

from gdm.distribution.components.distribution_transformer import DistributionTransformer
from gdm.distribution.controllers.distribution_regulator_controller import RegulatorController
from gdm.distribution.equipment.distribution_transformer_equipment import (
    TapWindingEquipment,
    DistributionTransformerEquipment,
)
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import PositiveVoltage


class DistributionRegulator(DistributionTransformer):
    controllers: Annotated[
        list[RegulatorController],
        Field(
            ...,
            description="The regulators that are used to control voltage on each phase of the transformer",
        ),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionRegulator":
        """Custom validator for voltage regulator."""
        has_tap_winding = False
        for winding in self.equipment.windings:
            if isinstance(winding, TapWindingEquipment):
                has_tap_winding = True
                if len(winding.tap_positions) != len(self.controllers):
                    msg = (
                        f"Number of tap positions {winding.tap_positions=} "
                        f"should be equal to the number of controllers {self.controllers=}."
                    )
                    raise ValueError(msg)
                for controller in self.controllers:
                    if controller.regulator_setting > winding.band_center + winding.bandwidth / 2:
                        msg = (
                            f"Controller setpoint {controller.regulator_setting=} is "
                            f"larger than the upper controller range of {winding.band_center+winding.bandwidth/2=}."
                            f"using bandwidth {winding.bandwidth=} around band center {winding.band_center=}."
                        )
                        raise ValueError(msg)
                    if controller.regulator_setting < winding.band_center - winding.bandwidth / 2:
                        msg = (
                            f"Controller setpoint {controller.regulator_setting=} is "
                            f"less than the lower controller range of {winding.band_center-winding.bandwidth/2=} "
                            f"using bandwidth {winding.bandwidth=} around band center {winding.band_center=}."
                        )
                        raise ValueError(msg)

        if not has_tap_winding:
            msg = f"No winding with taps found on regulator in {self.equipment.windings=}."
            raise ValueError(msg)

    @classmethod
    def example(cls) -> "DistributionRegulator":
        """Example for Voltage Regulator"""
        return DistributionRegulator(
            name="DistributionRegulator1",
            buses=[
                DistributionBus(
                    voltage_type="line-to-ground",
                    name="Bus1",
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
                DistributionBus(
                    voltage_type="line-to-ground",
                    name="Bus2",
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
            ],
            winding_phases=[[Phase.A, Phase.B, Phase.C], [Phase.A, Phase.B, Phase.C]],
            equipment=DistributionTransformerEquipment.example_with_taps(),
            controllers=[
                RegulatorController.example(),
                RegulatorController.example(),
                RegulatorController.example(),
            ],
        )
