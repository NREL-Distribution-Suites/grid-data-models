""" This module contains interface for powersystem load."""
from typing import Annotated

from infrasys.component_models import ComponentWithQuantities
from infrasys.quantities import ActivePower
from pydantic import Field

from gdm.quantities import ReactivePower


class PowerSystemLoad(ComponentWithQuantities):
    """Interface for power system load."""

    z_kw: Annotated[
        ActivePower,
        Field(
            default=ActivePower(0, "kilowatt"),
            description="Constant impedance load active component.",
        ),
    ]
    z_kvar: Annotated[
        ReactivePower,
        Field(
            default=ReactivePower(0, "kilovar"),
            description="Constant impedance load reactive component.",
        ),
    ]
    i_kw: Annotated[
        ActivePower,
        Field(
            default=ActivePower(0, "kilowatt"),
            description="Constant current load active component.",
        ),
    ]
    i_kvar: Annotated[
        ReactivePower,
        Field(
            default=ReactivePower(0, "kilovar"),
            description="Constant current load reactive component.",
        ),
    ]
    p_kw: Annotated[
        ActivePower,
        Field(
            default=ActivePower(0, "kilowatt"),
            description="Constant power load active component.",
        ),
    ]
    p_kvar: Annotated[
        ReactivePower,
        Field(
            default=ReactivePower(0, "kilovar"),
            description="Constant power load reactive component.",
        ),
    ]

    @classmethod
    def example(cls) -> "PowerSystemLoad":
        return PowerSystemLoad(
            z_kw=ActivePower(0, "watt"),
            z_kvar=ReactivePower(0, "var"),
            i_kw=ActivePower(0, "watt"),
            i_kvar=ReactivePower(0, "var"),
            p_kw=ActivePower(2.5, "kilowatt"),
            p_kvar=ReactivePower(0, "kilovar"),
            name="PhaseLoad1",
        )
