from datetime import datetime
from typing import Annotated

from pydantic import Field

from infrasys import Location
from gdm.quantities import Distance
from gdm.structural.components.base import _GeoLocatedWithInstalledDateComponent


class UndergroundJunction(_GeoLocatedWithInstalledDateComponent):
    depth: Annotated[
        Distance,
        Field(..., description="Depth at which junction is located from the ground.", gt=0),
    ]
    power_system_resource_name: Annotated[
        str, Field(..., description="Name used in power system bus model.")
    ]

    @classmethod
    def example(cls) -> "UndergroundJunction":
        return UndergroundJunction(
            name="UndergroundJunction",
            location=Location(x=10.0, y=20.0),
            elevation=Distance(234, "meter"),
            installed_date=datetime(2016, 1, 1, 0, 0, 0),
            power_system_resource_name="UndergroundJunction",
            depth=Distance(10, "meter"),
        )
