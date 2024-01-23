"""This module contains interface for power distribution system model"""
from typing import Optional, Annotated
from enum import Enum

from infrasys.component_models import ComponentWithQuantities
from infrasys.quantities import Resistance
from pydantic import PositiveInt, Field

from gdm.distribution.distribution_voltage_source import PhaseVoltageSource
from gdm.load import PowerSystemLoad
from gdm.quantities import (
    PositiveApparentPower,
    PositiveDistance,
    PositiveCurrent,
    PositiveVoltage,
    Capacitance,
    Percentage,
    Reactance,
)
from gdm.distribution.distribution_branch import (
    ImpedanceDistributionBranch,
    GeometryDistributionBranch,
    Sectionalizer,
    Conductor,
    Breaker,
    Switch,
    Phase,
    Fuse,
)
from gdm.distribution.distribution_voltage_source import DistributionVoltageSource
from gdm.distribution.distribution_transformer import (
    DistributionTransformer,
    WindingCoupling,
    DistributionBus,
    ConnectionType,
    PhaseWinding,
    Winding,
)
from gdm.distribution.distribution_capacitor import DistributionCapacitor
from gdm.distribution.distribution_load import DistributionLoad, PhaseLoad


class DistributionModel(ComponentWithQuantities):
    """Interface for distribution model."""

    voltage_sources: Annotated[
        list[DistributionVoltageSource],
        Field(..., description="Slack for this distribution model"),
    ]
    buses: Annotated[
        list[DistributionBus],
        Field(..., description="List of distribution system buses for this model."),
    ]
    ac_lines: Annotated[
        list[ImpedanceDistributionBranch | GeometryDistributionBranch],
        Field(..., description="List of AC line segments for this model."),
    ]
    transformers: Annotated[
        list[DistributionTransformer],
        Field([], description="List of transformers for this model."),
    ]
    loads: Annotated[
        list[DistributionLoad],
        Field([], description="List of distribution system loads for this model."),
    ]
    switches: Annotated[list[Switch], Field([], description="List of switches for this model.")]
    fuses: Annotated[list[Fuse], Field([], description="List of fuses for this model.")]
    sectionalizers: Annotated[
        list[Sectionalizer],
        Field([], description="List of sectionalizers for this model."),
    ]
    breakers: Annotated[list[Breaker], Field([], description="List of breakers for this models.")]
    capacitors: Annotated[
        list[DistributionCapacitor],
        Field([], description="List of capacitors for this model."),
    ]
    year: Annotated[
        Optional[PositiveInt], Field(None, description="Year to which this model belongs to.")
    ]

    @classmethod
    def example(cls) -> "DistributionModel":
        bus1 = DistributionBus(
            voltage_type="line-to-ground",
            name="Bus1",
            nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
            phases=[Phase.A, Phase.B, Phase.C],
        )
        bus2 = DistributionBus(
            voltage_type="line-to-ground",
            name="Bus2",
            nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
            phases=[Phase.A, Phase.B, Phase.C],
        )
        bus3 = DistributionBus(
            voltage_type="line-to-ground",
            name="Bus3",
            nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
            phases=[Phase.A],
        )
        ac_line1 = ImpedanceDistributionBranch(
            name="Line1",
            from_bus=bus2,
            to_bus=bus3,
            length=PositiveDistance(23.5, "meter"),
            conductors=[Conductor(ampacity=PositiveCurrent(90, "ampere"), phase=Phase.A)],
            r_matrix=[[Resistance(0.4, "ohm")]],
            x_matrix=[[Reactance(0.4, "ohm")]],
            c_matrix=[[Capacitance(1, "nanofarad")]],
        )
        load1 = DistributionLoad(
            name="Load1",
            bus=bus3,
            phase_loads=[PhaseLoad(phase=Phase.A, load=PowerSystemLoad.example())],
        )
        ph_wdgs = [
            PhaseWinding(phase=Phase.A, tap_position=0),
            PhaseWinding(phase=Phase.B, tap_position=0),
            PhaseWinding(phase=Phase.C, tap_position=0),
        ]
        transformer1 = DistributionTransformer(
            name="DistributionTransformer1",
            no_load_loss=Percentage(0.1, "dimensionless"),
            full_load_loss=Percentage(1, "dimensionless"),
            windings=[
                Winding(
                    phase_wdgs=ph_wdgs,
                    resistance=Percentage(3.4, "dimensionless"),
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
            is_center_tapped=False,
            wdg_couplings=[
                WindingCoupling(
                    to_wdg_seq_num=1,
                    from_wdg_seq_num=2,
                    reactance=Percentage(5, "dimensionless"),
                )
            ],
        )

        return DistributionModel(
            name="DistributionModel1",
            voltage_sources=[
                DistributionVoltageSource(
                    name="Slack1", bus=bus1, phase_voltage_sources=[PhaseVoltageSource.example()]
                )
            ],
            buses=[bus1, bus2, bus3],
            transformers=[transformer1],
            ac_lines=[ac_line1],
            loads=[load1],
            year=2023,
        )


class BreakerArrangment(str, Enum):
    """Types of bus bar arrangements."""

    BREAKER_AND_A_HALF = "Breaker and a half"
    TRANSFER_BUS = "Transfer bus"
    SINGLE_BUS = "Single bus"
    RING = "Ring"


class DistributionSubstation(ComponentWithQuantities):
    """Interface for substation model.

    Args:
        ComponentWithQuantities (component): component type
    """

    hv_breaker_arrangement: BreakerArrangment
    lv_breaker_arrangement: BreakerArrangment
    transformer: DistributionTransformer
    feeders: list[DistributionModel] = []
    voltage_sources: [DistributionVoltageSource]

    @classmethod
    def example(cls) -> "DistributionSubstation":
        """Returns example instance of the DistributionSubstation

        Returns:
            DistributionSubstation: Substation model instance
        """
        return DistributionSubstation(
            name="substation_1",
            transformer=DistributionTransformer.example(),
            voltage_sources=[DistributionVoltageSource.example()],
            feeders=[
                DistributionModel.example(),
            ],
            hv_breaker_arrangement=BreakerArrangment.BREAKER_AND_A_HALF,
            lv_breaker_arrangement=BreakerArrangment.BREAKER_AND_A_HALF,
        )
