""" This module contains interface for distribution transformer."""

from typing import Annotated
from gdm.distribution.distribution_transformer_equipment import (
    DistributionTransformerEquipment,
    TapWindingEquipment,
)

from infrasys.component_models import ComponentWithQuantities
from pydantic import Field, model_validator

from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import PositiveVoltage
from gdm.distribution.distribution_bus import DistributionBus
from gdm.distribution.distribution_regulator_controller import RegulatorController


class DistributionTransformer(ComponentWithQuantities):
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

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionTransformer":
        """Custom validator for distribution transformer."""
        if len(self.winding_phases) != len(self.equipment.windings):
            msg = (
                f"Number of windings {len(self.equipment.windings)} must be equal to"
                f"numbe of winding phases {len(self.winding_phases)}"
            )
            raise ValueError(msg)

        for wdg, pw_phases in zip(self.equipment.windings, self.winding_phases):
            if len(pw_phases) > wdg.num_phases:
                msg = (
                    f"Number of phases in windings {wdg.num_phases=} must be"
                    f"greater than or equal to phases {pw_phases=}"
                )
                raise ValueError(msg)

        for bus, pw_phases in zip(self.buses, self.winding_phases):
            if not set(pw_phases).issubset(bus.phases):
                msg = (
                    f"Winding phases {pw_phases=}" f"must be subset of bus phases ({bus.phases=})."
                )
                raise ValueError(msg)

        for bus, wdg in zip(self.buses, self.equipment.windings):
            if not (
                0.85 * bus.nominal_voltage.to("kilovolt")
                <= wdg.nominal_voltage.to("kilovolt")
                <= 1.15 * bus.nominal_voltage.to("kilovolt")
            ):
                msg = (
                    f"Nominal voltage of transformer {wdg.nominal_voltage.to('kilovolt')}"
                    "needs to be within 15% range of"
                    f"bus nominal voltage {bus.nominal_voltage.to('kilovolt')}"
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
                    voltage_type="line-to-ground",
                    name="Bus1",
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
                DistributionBus(
                    voltage_type="line-to-ground",
                    name="Bus2",
                    nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
            ],
            winding_phases=[[Phase.A, Phase.B, Phase.C], [Phase.A, Phase.B, Phase.C]],
            equipment=DistributionTransformerEquipment.example(),
        )


class DistributionRegulator(DistributionTransformer):
    controllers: Annotated[
        list[RegulatorController],
        Field(
            ...,
            description="The regulators that are used to conrol voltage on each phase of the transformer",
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
