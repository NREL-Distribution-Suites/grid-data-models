""" This module contains interface for distribution controllers."""

from typing import Annotated, Optional

from infrasys import Component
from infrasys.quantities import Time
from pydantic import Field

from gdm.quantities import (
    PositiveVoltage,
    PositiveCurrent,
)

from gdm.constants import PINT_SCHEMA


class RegulatorController(Component):
    """Interface for a Regulator Controller."""

    name: Annotated[str, Field("", description="Name of the regulator controller.")]
    delay: Annotated[
        Optional[Time],
        PINT_SCHEMA,
        Field(..., description="Delay for the first tap change operation"),
    ]
    vsetpoint: Annotated[
        PositiveVoltage,
        PINT_SCHEMA,
        Field(
            ...,
            description="The target control voltage for regulator controller.",
        ),
    ]
    pt_ratio: Annotated[
        float,
        Field(
            ...,
            ge=0,
            description="Value of the voltage (potential) transformer ratio used to step down the voltage for the controller.",
        ),
    ]
    ldc_R: Annotated[
        Optional[PositiveVoltage],
        PINT_SCHEMA,
        Field(
            None,
            description="R setting on the line drop compensator of the regulator in Volts.",
        ),
    ]
    ldc_X: Annotated[
        Optional[PositiveVoltage],
        PINT_SCHEMA,
        Field(
            None,
            description="X setting on the line drop compensator of the regulator in Volts.",
        ),
    ]
    ct_primary: Annotated[
        Optional[PositiveCurrent],
        PINT_SCHEMA,
        Field(
            None,
            description="Current at which the line drop compensator voltages match the R and X settings.",
        ),
    ]
    max_step: Annotated[
        int,
        Field(
            ge=0,
            description="Maximum number of steps upwards or downwards that can be made per control iteration.",
        ),
    ]
    bandwidth: Annotated[
        PositiveVoltage,
        PINT_SCHEMA,
        Field(..., description="The total voltage bandwidth for the controller"),
    ]

    @classmethod
    def example(cls) -> "RegulatorController":
        """Example for a Regulator Controller."""
        return RegulatorController(
            delay=Time(10, "seconds"),
            vsetpoint=PositiveVoltage(120, "volts"),
            pt_ratio=60,
            max_step=16,
            bandwidth=PositiveVoltage(3, "volts"),
        )
