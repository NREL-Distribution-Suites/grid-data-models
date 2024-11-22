from datetime import datetime
from typing import Annotated, Self

from pydantic import Field
from infrasys import Location

from gdm.quantities import PositiveDistance
from gdm.structural.components.base import _GeoLocatedWithInstalledDateComponent


class Building(_GeoLocatedWithInstalledDateComponent):
    power_system_resource_name: Annotated[
        str,
        Field(..., description="Name of load model used in power system model."),
    ]

    @classmethod
    def example(cls) -> Self:
        return Building(
            name="Customer1",
            location=Location(x=10.0, y=20.0),
            elevation=PositiveDistance(234, "meter"),
            installed_date=datetime(2016, 1, 1, 0, 0, 0),
            power_system_resource_name="Customer1",
        )
