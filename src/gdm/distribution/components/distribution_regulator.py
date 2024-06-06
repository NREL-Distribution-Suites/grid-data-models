"""This module contains distribution regulator."""

from typing import Annotated

from pydantic import Field, model_validator

from gdm.distribution.components.distribution_transformer import DistributionTransformer
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.controllers.distribution_regulator_controller import RegulatorController
from gdm.distribution.equipment.distribution_transformer_equipment import (
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
        for winding in self.equipment.windings:
            if len(winding.tap_positions) != len(self.controllers):
                msg = (
                    f"Number of tap positions {winding.tap_positions=} "
                    f"should be equal to the number of controllers {self.controllers=}."
                )
                raise ValueError(msg)

    @classmethod
    def example(cls) -> "DistributionRegulator":
        """Example for Voltage Regulator"""
        return DistributionRegulator(
            name="DistributionRegulator1",
            buses=[
                DistributionBus(
                    voltage_type="line-to-ground",
                    name="Regulator-DistBus1",
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    substation=DistributionSubstation.example(),
                    feeder=DistributionFeeder.example(),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
                DistributionBus(
                    voltage_type="line-to-ground",
                    name="Regulator-DistBus2",
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    substation=DistributionSubstation.example(),
                    feeder=DistributionFeeder.example(),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
            ],
            winding_phases=[[Phase.A, Phase.B, Phase.C], [Phase.A, Phase.B, Phase.C]],
            equipment=DistributionTransformerEquipment.example(),
            controllers=[
                RegulatorController.example(),
                RegulatorController.example(),
                RegulatorController.example(),
            ],
        )
