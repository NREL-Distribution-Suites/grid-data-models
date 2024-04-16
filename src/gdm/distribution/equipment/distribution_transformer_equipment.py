""" This module contains interface for distribution transformer."""

from itertools import groupby
from typing import Annotated

from infrasys import Component
from pydantic import Field, model_validator

from gdm.distribution.sequence_pair import SequencePair
from gdm.distribution.distribution_enum import ConnectionType, VoltageTypes
from gdm.quantities import PositiveApparentPower, PositiveVoltage
from gdm.constants import PINT_SCHEMA


class WindingEquipment(Component):
    """Interface for winding."""

    name: Annotated[str, Field("", description="Name of the winding.")]
    resistance: Annotated[
        float,
        Field(
            ..., strict=True, ge=0, le=100, description="Percentage resistance for this winding."
        ),
    ]
    is_grounded: Annotated[bool, Field(..., description="Is this winding grounded or not.")]
    nominal_voltage: Annotated[
        PositiveVoltage,
        PINT_SCHEMA,
        Field(..., description="Nominal voltage rating for this winding."),
    ]
    voltage_type: Annotated[
        VoltageTypes, Field(..., description="Set voltage type for nominal voltage.")
    ]
    rated_power: Annotated[
        PositiveApparentPower,
        PINT_SCHEMA,
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
            voltage_type=VoltageTypes.LINE_TO_LINE,
        )


class TapWindingEquipment(WindingEquipment):
    """Interface for tapped winding equipment."""

    tap_positions: Annotated[
        list[int], Field(..., description="List of tap positions for each phase. Centered at 0.")
    ]
    total_taps: Annotated[
        int, Field(default=32, description="Total number of taps along the bandwidth.")
    ]
    bandwidth: Annotated[
        PositiveVoltage,
        PINT_SCHEMA,
        Field(..., description="The total voltage bandwidth for the controller"),
    ]
    band_center: Annotated[
        PositiveVoltage,
        PINT_SCHEMA,
        Field(..., description="The voltage bandcenter on the controller."),
    ]
    max_step: Annotated[
        int,
        Field(
            ge=0,
            description="Maximum number of steps upwards or downwards that can be made per control iteration.",
        ),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "TapWindingEquipment":
        """Custom validator for winding fields."""
        if not len(self.tap_positions) == self.num_phases:
            msg = (
                f"Number of tap positions {self.tap_positions=}"
                f"should be equal to number of phase {self.num_phases}"
            )
            raise ValueError(msg)
        for tap in self.tap_positions:
            if not abs(tap) <= self.total_taps / 2:
                msg = (
                    f"Tap position {tap=} outside allowable range"
                    f" of [{-1*self.total_taps/2=}-{self.total_taps/2=}] for"
                    f" total taps of {self.total_taps=}."
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
            num_phases=3,
            tap_positions=[0, -1, 2],
            total_taps=32,
            bandwidth=PositiveVoltage(3, "volts"),
            band_center=PositiveVoltage(120, "volts"),
            max_step=4,
            voltage_type=VoltageTypes.LINE_TO_LINE,
        )


class DistributionTransformerEquipment(Component):
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
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                ),
                WindingEquipment(
                    resistance=1,
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
                    rated_power=PositiveApparentPower(56, "kilova"),
                    connection_type=ConnectionType.STAR,
                    num_phases=3,
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                ),
            ],
            coupling_sequences=[SequencePair(0, 1)],
            winding_reactances=[2.3],
        )

    @classmethod
    def example_with_taps(cls) -> "DistributionTransformerEquipment":
        """Example for distribution transformer model."""
        return DistributionTransformerEquipment(
            name="Transformer-Taps1",
            pct_no_load_loss=0.1,
            pct_full_load_loss=1,
            is_center_tapped=False,
            windings=[
                TapWindingEquipment.example(),
                TapWindingEquipment.example(),
            ],
            coupling_sequences=[SequencePair(0, 1)],
            winding_reactances=[2.3],
        )
