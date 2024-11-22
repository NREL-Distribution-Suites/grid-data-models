from typing import Annotated
from abc import ABC
from datetime import datetime
from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveDistance
from infrasys import Location


class _InstalledDateBaseComponent(Component, ABC):
    installed_date: Annotated[datetime, Field(..., description="Installation date.")]


class _GeoLocatedBaseComponent(Component, ABC):
    elevation: Annotated[PositiveDistance, Field(..., description="Elevation from sea level.")]
    location: Annotated[Location, Field(..., description="Location of the component.")]


class _GeoLocatedWithInstalledDateComponent(_GeoLocatedBaseComponent, ABC):
    installed_date: Annotated[
        datetime, Field(..., description="When the component was installed.")
    ]
