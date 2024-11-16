from typing import Annotated

from infrasys import Component, Location
from pydantic import Field

from gdm.quantities import PositiveDistance


class UndergroundJunction(Component):
    depth: Annotated[
        PositiveDistance,
        Field(
            ...,
            description="Depth at which junction is located from the ground.",
        ),
    ]
    location: Annotated[Location, Field(..., description="Physical location of the junction.")]
    elevation: Annotated[PositiveDistance, Field(..., description="Elevation from sea level.")]
    power_system_resource_name: Annotated[
        str, Field(..., description="Name used in power system bus model.")
    ]
