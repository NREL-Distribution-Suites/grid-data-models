"""Equipment model for a series distribution reactor."""

from typing import Annotated

from infrasys import Component

from gdm.constants import PINT_SCHEMA
from gdm.quantities import Reactance
from infrasys.quantities import Resistance
from pydantic import Field


class ReactorEquipment(Component):
    """Scalar series reactor impedance shared by a :class:`DistributionReactor`."""

    resistance: Annotated[
        Resistance,
        PINT_SCHEMA,
        Field(..., description="Series reactor resistance."),
    ]
    reactance: Annotated[
        Reactance,
        PINT_SCHEMA,
        Field(..., description="Series reactor reactance."),
    ]

    @classmethod
    def example(cls) -> "ReactorEquipment":
        return cls(
            name="reactor_equipment",
            resistance=Resistance(0.0, "ohm"),
            reactance=Reactance(1.0, "ohm"),
        )
