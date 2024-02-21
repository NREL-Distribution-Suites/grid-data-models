""" This module contains interface for distribution transformer."""

from itertools import groupby
from typing import Annotated

from infrasys.component_models import Component, ComponentWithQuantities
from pydantic import Field, model_validator

from gdm.distribution.distribution_common import BELONG_TO_TYPE, SequencePair
from gdm.distribution.distribution_enum import Phase, ConnectionType
from gdm.quantities import PositiveApparentPower, PositiveVoltage
from gdm.distribution.distribution_bus import DistributionBus
from gdm.distribution.distribution_controller import RegulatorController


class WindingEquipment(Component):
    """Interface for winding."""

    resistance: Annotated[
        float,
        Field(..., strict=True, ge=0, le=100, description="Percentage resistance for this winding."),
    ]
    is_grounded: Annotated[bool, Field(..., description="Is this winding grounded or not.")]
    nominal_voltage: Annotated[
        PositiveVoltage,
        Field(..., description="Nominal voltage rating for this winding."),
    ]
    rated_power: Annotated[
        PositiveApparentPower,
        Field(..., description="Rated power for this winding."),
    ]
    num_phases: Annotated[
        int, Field(..., ge=1, le=3, description="Number of phases for this winding.")
    ]
    connection_type: Annotated[
        ConnectionType,
        Field(
            ...,
            description="""Connection type for this winding.""",
        ),
    ]

    @classmethod
    def example(cls) -> "WindingEquipment":
        return WindingEquipment(
            resistance=1,
            is_grounded=False,
            nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
            rated_power=PositiveApparentPower(500, "kilova"),
            connection_type=ConnectionType.STAR,
            num_phases=3,
        )


class TapWindingEquipment(WindingEquipment):
    """Interface for tapped winding equipment."""

    minimum_tap: Annotated[
        PositiveVoltage, Field(..., description="Minimum tap position of a winding.")
    ]
    maximum_tap: Annotated[
        PositiveVoltage, Field(..., description="Maximum tap position of a winding.")
    ]
    tap_positions: Annotated[
        list[int], Field(..., description="List of tap positions for each phases.")
    ]
    allow_neg_tap: Annotated[
        bool,
        Field(
            True,
            description="""If allowed tap position would vary from negative
            half of total taps to positive half of total taps.""",
        ),
    ]
    total_taps: Annotated[int, Field(default=32, description="Maximum tap position of a winding.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "TapWindingEquipment":
        """Custom validator for winding fields."""
        if not len(self.tap_positions) == self.num_phases:
            msg = (
                f"Number of tap positions {self.tap_positions=}"
                f"should be equal to number of phase {self.num_phases}"
            )
            raise ValueError(msg)
        if self.minimum_tap.to("kilovolt") >= self.maximum_tap.to("kilovolt"):
            msg = (
                f"Minimum tap {self.minimum_tap=} must be"
                f" smaller than maximum tap {self.maximum_tap=}"
            )
            raise ValueError(msg)
        for tap in self.tap_positions:
            if self.allow_neg_tap and abs(tap) > self.total_taps / 2:
                msg = f"Invalid tap position {tap=} must be within +- {self.total_taps/2}"
                raise ValueError(msg)
            if not self.allow_neg_tap and (tap > self.total_taps or tap < 0):
                msg = (
                    f"Invalid tap position {tap=} must be less "
                    f"than {self.total_taps} and greater than 0"
                )
                raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "TapWindingEquipment":
        return TapWindingEquipment(
            resistance=1,
            is_grounded=False,
            nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
            rated_power=PositiveApparentPower(500, "kilova"),
            connection_type=ConnectionType.STAR,
            num_phase=3,
            minimum_tap=PositiveVoltage(12.45, "kilovolt"),
            maximum_tap=PositiveVoltage(12.49, "kilovolt"),
            tap_positions=[0, 0, 0],
        )


class DistributionTransformerEquipment(ComponentWithQuantities):
    """Interface for distribution transformer info."""

    pct_no_load_loss: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=0,
            le=100,
            description="Percentage no load losses for this transformer.",
        ),
    ]
    pct_full_load_loss: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=0,
            le=100,
            description="Percentage no load losses for this transformer.",
        ),
    ]
    windings: Annotated[
        list[WindingEquipment],
        Field(..., description="List of windings for this transformer."),
    ]

    coupling_sequences: Annotated[
        list[SequencePair],
        Field(
            ...,
            description="""List of pair
            of sequence numbers for coupling """,
        ),
    ]
    winding_reactances: Annotated[
        list[Annotated[float, Field(strict=True, ge=0, le=100)]],
        Field(
            ...,
            description="""Winding coupling reactances in the
            "same order as coupling sequences.""",
        ),
    ]
    is_center_tapped: Annotated[bool, Field(..., description="Is this transformer center tapped.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionTransformerEquipment":
        """Custom validator for distribution transformer model."""

        for wdg_seq in self.coupling_sequences:
            if wdg_seq.from_index == wdg_seq.to_index:
                msg = (
                    f"From sequence number {wdg_seq.from_index} can not "
                    f"be same as To sequence {wdg_seq.to_index} numbers."
                )
                raise ValueError(msg)

        if len(self.coupling_sequences) != sum(range(len(self.windings))):
            msg = (
                f"Length of winding couplings is invalid."
                f"Phase couplings: {len(self.coupling_sequences)},"
                f"Windings {len(self.windings)}"
            )
            raise ValueError(msg)

        if len(self.coupling_sequences) != len(self.winding_reactances):
            msg = (
                f"Length of coupling sequences {self.coupling_sequences=}"
                f"must be equal to length of winding reactances {self.winding_reactances}"
            )
            raise ValueError(msg)

        if len(list(groupby([set(item) for item in self.coupling_sequences]))) != len(
            self.coupling_sequences
        ):
            msg = f"Invalid sequence numbers in spacing sequences. {self.coupling_sequences=}"
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "DistributionTransformerEquipment":
        """Example for distribution transformer model."""
        return DistributionTransformerEquipment(
            name="Transformer-1",
            pct_no_load_loss=0.1,
            pct_full_load_loss=1,
            is_center_tapped=False,
            windings=[
                WindingEquipment(
                    resistance=1,
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    rated_power=PositiveApparentPower(56, "kilova"),
                    connection_type=ConnectionType.STAR,
                    num_phases=3,
                ),
                WindingEquipment(
                    resistance=1,
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
                    rated_power=PositiveApparentPower(56, "kilova"),
                    connection_type=ConnectionType.STAR,
                    num_phases=3,
                ),
            ],
            coupling_sequences=[SequencePair(0, 1)],
            winding_reactances=[2.3],
        )


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

class DistributionRegulator(ComponentWithQuantities):

    transformer: Annotated[
        DistributionTransformer, Field(...,description="The transformer that a voltage regulator controls")
    ]

    controllers: Annotated[
        list[RegulatorController], Field(...,description="The regulators that are used to conrol voltage on each phase of the transformer")
    ]

    @classmethod
    def example(cls) -> "DistributionRegulator":
        """Example for Voltage Regulator"""
        return DistributionRegulator(
            name="DistributionRegulator1",
            transformer=DistributionTransformer.example(),
            controllers = [
                RegulatorController.example(),
                RegulatorController.example(),
                RegulatorController.example(),
            ]
        )

