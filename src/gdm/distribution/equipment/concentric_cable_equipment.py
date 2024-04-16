""" This module contains concentric cable equipment."""

from typing import Annotated, Optional

from infrasys import Component
from pydantic import Field, PositiveInt, model_validator

from gdm.quantities import (
    PositiveDistance,
    PositiveCurrent,
    PositiveResistancePULength,
    PositiveVoltage,
)
from gdm.distribution.limitset import ThermalLimitSet
from gdm.constants import PINT_SCHEMA


class ConcentricCableEquipment(Component):
    """Interface for cable catalog."""

    strand_diameter: Annotated[
        PositiveDistance, PINT_SCHEMA, Field(..., description="Diameter of the cable strand.")
    ]
    conductor_diameter: Annotated[
        PositiveDistance,
        PINT_SCHEMA,
        Field(..., description="Diameter of the conductor inside cable."),
    ]
    cable_diameter: Annotated[
        PositiveDistance, PINT_SCHEMA, Field(..., description="Diameter of the cable.")
    ]
    insulation_thickness: Annotated[
        PositiveDistance, PINT_SCHEMA, Field(..., description="Thickness of insulation.")
    ]
    insulation_diameter: Annotated[
        PositiveDistance, PINT_SCHEMA, Field(..., description="Diameter of the insulation.")
    ]
    ampacity: Annotated[
        PositiveCurrent, PINT_SCHEMA, Field(..., description="Ampacity of the conductor.")
    ]
    emergency_ampacity: Annotated[
        PositiveCurrent,
        PINT_SCHEMA,
        Field(..., description="Emergency ampacity of the conductor."),
    ]
    conductor_gmr: Annotated[
        PositiveDistance,
        PINT_SCHEMA,
        Field(..., description="Geometric mean radius of the conductor."),
    ]
    strand_gmr: Annotated[
        PositiveDistance,
        PINT_SCHEMA,
        Field(..., description="Geometric mean radius of the strand."),
    ]
    phase_ac_resistance: Annotated[
        PositiveResistancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length conductor ac resistance."),
    ]
    strand_ac_resistance: Annotated[
        PositiveResistancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length ac resistance of the strand."),
    ]
    num_neutral_strands: Annotated[
        PositiveInt, Field(..., description="Number of neutral strands in the cable.")
    ]
    rated_voltage: Annotated[
        PositiveVoltage, PINT_SCHEMA, Field(..., description="Rated voltage for the cable.")
    ]
    loading_limit: Annotated[
        Optional[ThermalLimitSet],
        Field(None, description="Loading limit set for this conductor."),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "ConcentricCableEquipment":
        """Custom validator for fields."""
        if self.insulation_diameter.to("m") < (
            self.conductor_diameter.to("m") + 2 * self.insulation_thickness.to("m")
        ):
            msg = (
                f"Insulation diameter {self.insulation_diameter} must be greater than "
                f"conductor diameter {self.conductor_diameter} plus two times insulation "
                f"thickness {self.insulation_thickness}"
            )
            raise ValueError(msg)

        if self.cable_diameter < (self.insulation_diameter + 2 * self.strand_diameter):
            msg = (
                f"Cable diameter {self.cable_diameter} must be greater than "
                f"insulation diameter {self.insulation_diameter} plus two times strand diameter "
                f" {self.strand_diameter}"
            )
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "ConcentricCableEquipment":
        """Example for concentric cable."""
        return ConcentricCableEquipment(
            name="2(7×)concentric_cable_1/3",
            strand_diameter=PositiveDistance(0.0641, "in"),
            conductor_diameter=PositiveDistance(0.258, "in"),
            cable_diameter=PositiveDistance(0.98, "in"),
            insulation_thickness=PositiveDistance(0.226, "in"),
            insulation_diameter=PositiveDistance(0.78, "in"),
            ampacity=PositiveCurrent(135, "ampere"),
            emergency_ampacity=PositiveCurrent(135, "ampere"),
            conductor_gmr=PositiveDistance(0.00836, "ft"),
            strand_gmr=PositiveDistance(0.00208, "ft"),
            phase_ac_resistance=PositiveResistancePULength(0.945, "ohm/mi"),
            strand_ac_resistance=PositiveResistancePULength(14.8722, "ohm/mi"),
            num_neutral_strands=2,
            rated_voltage=PositiveVoltage(15, "kilovolt"),
        )
