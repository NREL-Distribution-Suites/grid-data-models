""" Interface for power system branch. """
from typing import Annotated, Optional

from infrasys.component_models import Component, ComponentWithQuantities
from infrasys.models import InfraSysBaseModel
from infrasys.quantities import Resistance
from pydantic import PlainSerializer, model_validator, Field

from gdm.distribution.distribution_component import DistributionComponent
from gdm.distribution.distribution_bus import DistributionBus
from gdm.distribution.limitset import ThermalLimitSet
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import (
    Capacitance,
    PositiveCurrent,
    PositiveDistance,
    PositiveVoltage,
    Reactance,
)


class Conductor(Component):
    """Interface for phase conductor."""

    ampacity: Annotated[PositiveCurrent, Field(..., description="Ampacity of the conducotr.")]
    phase: Annotated[Phase, Field(..., description="Phase of this conductor.")]
    loading_limit: Annotated[
        Optional[ThermalLimitSet],
        Field(None, description="Loading limit set for this conductor."),
    ]

    @classmethod
    def example(cls) -> "Conductor":
        return Conductor(
            ampacity=PositiveCurrent(90, "ampere"),
            phase=Phase.A,
        )


class DistributionBranch(ComponentWithQuantities):
    """Interface for distribution branch."""

    belongs_to: Annotated[
        Optional[DistributionComponent],
        Field(
            None,
            description="Substation and feeder this branch belongs to.",
        ),
    ]
    from_bus: Annotated[
        DistributionBus,
        Field(..., description="From bus to which this branch is connected to."),
    ]
    to_bus: Annotated[
        DistributionBus,
        Field(..., description="To bus to which this branch is connected to."),
    ]
    length: Annotated[PositiveDistance, Field(..., description="Length of the branch.")]
    conductors: Annotated[
        list[Conductor],
        Field(..., description="List of phase conductors."),
    ]
    is_closed: bool = True

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionBranch":
        for conductor in self.conductors:
            if conductor.phase not in self.from_bus.phases:
                msg = f"Conductor phase ({conductor.phase=})"
                f"does not match bus phases ({self.from_bus.phases=})"
                raise ValueError(msg)

            if conductor.phase not in self.to_bus.phases:
                msg = f"Conductor phase ({conductor.phase=})"
                f"does not match bus phases ({self.to_bus.phases=})"
                raise ValueError(msg)

        if self.to_bus.name == self.from_bus.name:
            msg = f"From bus {self.from_bus.name=} and to bus"
            f"{self.to_bus.name=} should be different."
            raise ValueError(msg)

        if self.to_bus.nominal_voltage != self.from_bus.nominal_voltage:
            msg = f"From bus {self.from_bus.nominal_voltage=}"
            f"and to bus voltage {self.to_bus.nominal_voltage=} rating should be same."
            raise ValueError(msg)

        if len(self.conductors) > len(self.from_bus.phases):
            msg = f"Number of conductors {len(self.conductors)}"
            f"can not exceed number of from bus phases {len(self.from_bus.phases)}"
            raise ValueError(msg)

        if len(self.conductors) > len(self.to_bus.phases):
            msg = f"Number of conductors {len(self.conductors)}"
            f"can not exceed number of to bus phases {len(self.to_bus.phases)}"
            raise ValueError(msg)

        c_phases = [c.phase for c in self.conductors]
        if len(c_phases) != len(set(c_phases)):
            msg = f"Duplicate phases not allowed for conductors {c_phases=}"
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "DistributionBranch":
        from_bus = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus1",
        )
        to_bus = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus2",
        )
        return DistributionBranch(
            from_bus=from_bus,
            to_bus=to_bus,
            length=PositiveDistance(130.2, "meter"),
            conductors=[
                Conductor(phase=Phase.A, ampacity=PositiveCurrent(90, "ampere")),
                Conductor(phase=Phase.B, ampacity=PositiveCurrent(90, "ampere")),
                Conductor(phase=Phase.C, ampacity=PositiveCurrent(90, "ampere")),
            ],
            name="p14u405",
        )


class MatrixType(InfraSysBaseModel):
    data: Annotated[
        list[list[float]],
        Field(..., description="List of list of floats."),
    ]
    el_type: str  # TODO: Remove if not needed later on
    unit: str


def serializer(dtype: str) -> PlainSerializer:
    return PlainSerializer(
        lambda x: MatrixType(
            data=[[float(el.magnitude) for el in arr] for arr in x],
            el_type=dtype,
            unit=str(x[0][0].units),
        ).model_dump(),
        when_used="always",
    )


MatrixResType = Annotated[
    list[list[Resistance]],
    serializer("PositiveResistance"),
    Field(..., description="Resistance matrix for conducotrs."),
]
MatrixReacType = Annotated[
    list[list[Reactance]],
    serializer("Reactance"),
    Field(..., description="Reactance matrix for conductors."),
]
MatrixCapType = Annotated[
    list[list[Capacitance]],
    serializer("Capacitance"),
    Field(..., description="Capacitance matrix for conductors."),
]


class ImpedanceDistributionBranch(DistributionBranch):
    """Interface for impedance based branch."""

    r_matrix: MatrixResType
    x_matrix: MatrixReacType
    c_matrix: MatrixCapType

    @model_validator(mode="before")
    @classmethod
    def parse_values(cls, values):
        req_keys = ["r_matrix", "x_matrix", "c_matrix"]
        if set(req_keys).difference(values):
            msg = f"Keys missing in values {values.keys()=} {req_keys=}"
            raise ValueError(msg)

        for quantity_, key_ in zip([Resistance, Reactance, Capacitance], req_keys):
            val = values[key_]
            if isinstance(val, dict) and "data" in val:
                values[key_] = [[quantity_(el, val["unit"]) for el in arr] for arr in val["data"]]

        return values

    @model_validator(mode="after")
    def validate_fields(self) -> "ImpedanceDistributionBranch":
        for mat in [self.r_matrix, self.x_matrix, self.c_matrix]:
            if len(mat) != len(self.conductors):
                msg = f"Length of matrix {len(mat), mat=} did not"
                f"match length of conductors {len(self.conductors)}"
                raise ValueError(msg)

            for item in mat:
                if len(item) != len(self.conductors):
                    msg = "Length of items in matrix"
                    f"{len(item), item} must be compatible with number"
                    f"of conductors {len(self.conductors)}"
                    raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "ImpedanceDistributionBranch":
        from_bus = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus1",
        )
        to_bus = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus2",
        )
        return ImpedanceDistributionBranch(
            from_bus=from_bus,
            to_bus=to_bus,
            length=PositiveDistance(45, "meter"),
            name="ImpedanceLine1",
            conductors=[
                Conductor(phase=Phase.A, ampacity=PositiveCurrent(90, "ampere")),
            ],
            r_matrix=[[Resistance(1, "ohm")]],
            x_matrix=[[Reactance(1, "ohm")]],
            c_matrix=[[Capacitance(1, "farad")]],
        )


class GeometryDistributionBranch(ImpedanceDistributionBranch):
    """Interface for geometry based lines."""


class Fuse(ImpedanceDistributionBranch):
    """Interface for Fuse element."""


class Switch(ImpedanceDistributionBranch):
    """Interface for switch"""


class Sectionalizer(ImpedanceDistributionBranch):
    """Interface for sectionalizer."""


class Breaker(ImpedanceDistributionBranch):
    """Interface for Breaker."""
