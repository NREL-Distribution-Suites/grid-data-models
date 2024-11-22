from datetime import datetime
from typing import Annotated, Self
from pydantic import Field

from infrasys import Location
from gdm.quantities import PositiveDistance
from gdm.structural.components.base import _GeoLocatedWithInstalledDateComponent
from gdm.structural.components.building import Building


class PVSystem(_GeoLocatedWithInstalledDateComponent):
    power_system_resource_name: Annotated[
        str,
        Field(..., description="Name of pv system model used in power system model."),
    ]
    building: Annotated[
        None | Building, Field(..., description="Building to which this system belongs to.")
    ]

    @classmethod
    def example(cls) -> Self:
        return PVSystem(
            name="Solar1",
            location=Location(x=10.0, y=20.0),
            elevation=PositiveDistance(234, "meter"),
            installed_date=datetime(2016, 1, 1, 0, 0, 0),
            power_system_resource_name="Solar1",
            building=Building.example(),
        )
