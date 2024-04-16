""" This module contains interface for powersystem load."""

from typing import Annotated

from infrasys import Component
from infrasys.quantities import ActivePower
from pydantic import Field

from gdm.quantities import ReactivePower
from gdm.constants import PINT_SCHEMA


class PowerSystemLoad(Component):
    """Interface for power system load."""

    z_real: Annotated[
        ActivePower,
        PINT_SCHEMA,
        Field(
            default=ActivePower(0, "kilowatt"),
            description="Constant impedance load real component.",
        ),
    ]
    z_imag: Annotated[
        ReactivePower,
        PINT_SCHEMA,
        Field(
            default=ReactivePower(0, "kilovar"),
            description="Constant impedance load imaginary component.",
        ),
    ]
    i_real: Annotated[
        ActivePower,
        PINT_SCHEMA,
        Field(
            default=ActivePower(0, "kilowatt"),
            description="Constant current load real component.",
        ),
    ]
    i_imag: Annotated[
        ReactivePower,
        PINT_SCHEMA,
        Field(
            default=ReactivePower(0, "kilovar"),
            description="Constant current load imaginary component.",
        ),
    ]
    p_real: Annotated[
        ActivePower,
        PINT_SCHEMA,
        Field(
            default=ActivePower(0, "kilowatt"),
            description="Constant power load real component.",
        ),
    ]
    p_imag: Annotated[
        ReactivePower,
        PINT_SCHEMA,
        Field(
            default=ReactivePower(0, "kilovar"),
            description="Constant power load imaginary component.",
        ),
    ]

    @classmethod
    def example(cls) -> "PowerSystemLoad":
        return PowerSystemLoad(
            z_real=ActivePower(0, "watt"),
            z_imag=ReactivePower(0, "var"),
            i_real=ActivePower(0, "watt"),
            i_imag=ReactivePower(0, "var"),
            p_real=ActivePower(2.5, "kilowatt"),
            p_imag=ReactivePower(0, "kilovar"),
            name="PhaseLoad1",
        )
