""" This module contains interface for distribution transformer."""
from typing import Annotated, Optional

from infrasys.component_models import Component, ComponentWithQuantities
from pydantic import Field, PositiveInt, model_validator

from gdm.distribution.distribution_component import DistributionComponent
from gdm.distribution.distribution_enum import Phase, ConnectionType
from gdm.distribution.distribution_bus import DistributionBus
from gdm.quantities import (
    PositiveApparentPower,
    PositiveVoltage,
    Percentage,
)


class PhaseWinding(Component):
    """Interface for phase winding."""

    phase: Annotated[Phase, Field(..., description="Phase for this phase winding.")]
    tap_position: Annotated[float, Field(..., description="Tap position for this phase winding.")]

    @classmethod
    def example(cls) -> "PhaseWinding":
        return PhaseWinding(phase=Phase.A, tap_position=0)


class Winding(Component):
    """Interface for winding."""

    phase_wdgs: Annotated[list[PhaseWinding], Field(..., description="List of phase windings.")]
    resistance: Annotated[Percentage, Field(..., description="Resistance for this winding.")]
    is_grounded: Annotated[bool, Field(..., description="Is this winding grounded or not.")]
    nominal_voltage: Annotated[
        PositiveVoltage, Field(..., description="Nominal voltage rating for this transformer.")
    ]
    bus: Annotated[
        DistributionBus,
        Field(..., description="Distribution bus to which this winding is connected to."),
    ]
    rated_power: Annotated[
        PositiveApparentPower, Field(..., description="Rated power for this transformer.")
    ]
    connection_type: Annotated[
        ConnectionType, Field(..., description="Connection type for this winding.")
    ]
    sequence_number: Annotated[
        PositiveInt, Field(..., description="Sequence Identifier for this winding.")
    ]
    minimum_tap: Annotated[
        float, Field(default=0.9, description="Minimum tap position of a winding.")
    ]
    maximum_tap: Annotated[
        float, Field(default=1.1, description="Maximum tap position of a winding.")
    ]
    total_taps: Annotated[int, Field(default=32, description="Maximum tap position of a winding.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "Winding":
        pw_phases = [pw.phase for pw in self.phase_wdgs]

        if not set(pw_phases).issubset(self.bus.phases):
            msg = f"Winding phases {pw_phases=}"
            f"must be subset of bus phases ({self.bus.phases=})."
            raise ValueError(msg)

        if not (
            0.85 * self.bus.nominal_voltage.to("kilovolt")
            <= self.nominal_voltage.to("kilovolt")
            <= 1.15 * self.bus.nominal_voltage.to("kilovolt")
        ):
            msg = f"Nominal voltage of transformer {self.nominal_voltage.to('kilovolt')} needs to be within 15% range of"
            f"bus nominal voltage {self.bus.nominal_voltage.to('kilovolt')}"
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "Winding":
        return Winding(
            phase_wdgs=[
                PhaseWinding(phase=Phase.A, tap_position=0),
                PhaseWinding(phase=Phase.B, tap_position=0),
                PhaseWinding(phase=Phase.C, tap_position=0),
            ],
            resistance=Percentage(1, "dimensionless"),
            is_grounded=False,
            nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
            bus=DistributionBus(
                voltage_type="line-to-ground",
                name="Bus-1",
                nominal_voltage=PositiveVoltage(12.3, "kilovolt"),
                phases=[Phase.A, Phase.B, Phase.C],
            ),
            rated_power=PositiveApparentPower(500, "kilova"),
            connection_type=ConnectionType.STAR,
            sequence_number=1,
        )


class WindingCoupling(Component):
    to_wdg_seq_num: Annotated[PositiveInt, Field(..., description="To winding sequence number.")]
    from_wdg_seq_num: Annotated[
        PositiveInt, Field(..., description="From winding sequence number.")
    ]
    reactance: Annotated[Percentage, Field(..., description="Winding coouling reactance")]

    @classmethod
    def example(cls) -> "WindingCoupling":
        return WindingCoupling(
            to_wdg_seq_num=1,
            from_wdg_seq_num=2,
            reactance=Percentage(2.3, "dimensionless"),
        )


class DistributionTransformer(ComponentWithQuantities):
    """Interface for distribution transformer."""

    belongs_to: Annotated[
        Optional[DistributionComponent],
        Field(None, description="Provides info about substation and feeder."),
    ]
    windings: Annotated[
        list[Winding], Field(..., description="List of windings for this transformer.")
    ]
    no_load_loss: Annotated[
        Percentage,
        Field(..., description="Percentage no load losses for this transformer."),
    ]
    full_load_loss: Annotated[
        Percentage,
        Field(..., description="Percentage no load losses for this transformer."),
    ]
    wdg_couplings: Annotated[
        list[WindingCoupling],
        Field(..., description="List of winding couplings for this transformer."),
    ]
    is_center_tapped: Annotated[bool, Field(..., description="Is this transformer center tapped.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionTransformer":
        wdg_seq_numbers = [wdg.sequence_number for wdg in self.windings]
        to_seq_nums = [wdg.to_wdg_seq_num for wdg in self.wdg_couplings]
        from_seq_nums = [wdg.from_wdg_seq_num for wdg in self.wdg_couplings]

        if not set(to_seq_nums).issubset(wdg_seq_numbers):
            msg = f"Set of To sequence numbers {to_seq_nums=} "
            f"must be same as set of winding sequence numbers {wdg_seq_numbers=}"
            raise ValueError(msg)

        if not set(from_seq_nums).issubset(wdg_seq_numbers):
            msg = f"Set of From sequence numbers {from_seq_nums=} "
            f"must be same as set winding sequence numbers {wdg_seq_numbers=}"
            raise ValueError(msg)

        for wdg in self.wdg_couplings:
            if wdg.to_wdg_seq_num == wdg.from_wdg_seq_num:
                msg = "From sequence number can not be same as To sequence numbers."
                raise ValueError(msg)

        if len(self.wdg_couplings) != sum(range(len(self.windings))):
            msg = (
                f"Length of winding couplings is invalid. Phase couplings: {len(self.wdg_couplings)},"
                f"Windings {len(self.windings)}"
            )
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "DistributionTransformer":
        ph_wdgs = [
            PhaseWinding(phase=Phase.A, tap_position=0),
            PhaseWinding(phase=Phase.B, tap_position=0),
            PhaseWinding(phase=Phase.C, tap_position=0),
        ]
        return DistributionTransformer(
            name="DistributionTransformer1",
            windings=[
                Winding(
                    phase_wdgs=ph_wdgs,
                    resistance=Percentage(1, "dimensionless"),
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    bus=DistributionBus(
                        voltage_type="line-to-ground",
                        name="Bus1",
                        nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                        phases=[Phase.A, Phase.B, Phase.C],
                    ),
                    rated_power=PositiveApparentPower(56, "kilova"),
                    connection_type=ConnectionType.STAR,
                    sequence_number=1,
                ),
                Winding(
                    phase_wdgs=ph_wdgs,
                    resistance=Percentage(1, "dimensionless"),
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
                    bus=DistributionBus(
                        voltage_type="line-to-ground",
                        name="Bus2",
                        nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
                        phases=[Phase.A, Phase.B, Phase.C],
                    ),
                    rated_power=PositiveApparentPower(56, "kilova"),
                    connection_type=ConnectionType.STAR,
                    sequence_number=2,
                ),
            ],
            no_load_loss=Percentage(0.1, "dimensionless"),
            full_load_loss=Percentage(1, "dimensionless"),
            is_center_tapped=False,
            wdg_couplings=[
                WindingCoupling(
                    to_wdg_seq_num=1,
                    from_wdg_seq_num=2,
                    reactance=Percentage(4.7, "dimensionless"),
                )
            ],
        )
