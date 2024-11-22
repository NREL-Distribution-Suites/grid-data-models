from typing import Annotated, Self
from datetime import datetime
from abc import ABC
from enum import Enum
from pydantic import Field

from infrasys import Location
from gdm.quantities import PositiveDistance
from gdm.structural.components.base import _GeoLocatedWithInstalledDateComponent
from gdm.structural.components.pole import Pole


class InsulationClass(str, Enum):
    NEMA_A = "NEMA_A"
    NEMA_B = "NEMA_B"
    NEMA_F = "NEMA_F"
    NEMA_H = "NEMA_H"
    NEMA_N = "NEMA_N"
    NEMA_R = "NEMA_R"
    NEMA_S = "NEMA_S"
    IEC_Y = "IEC_Y"
    IEC_E = "IEC_E"


class _BaseTransformer(_GeoLocatedWithInstalledDateComponent, ABC):
    power_system_resource_name: Annotated[
        str, Field(..., description="Name used in power system model.")
    ]
    insulation_class: Annotated[
        InsulationClass,
        Field(..., description="Insulation class for base transformer."),
    ]


class PoleMountedTransformer(_BaseTransformer):
    mounting_height: Annotated[
        PositiveDistance, Field(..., description="Mounting height from ground.")
    ]
    pole: Annotated[
        Pole,
        Field(..., description="Pole to which this transformer is attached to."),
    ]

    @classmethod
    def example(cls):
        return PoleMountedTransformer(
            name="Transformer-1",
            location=Location(x=10.0, y=20.0),
            elevation=PositiveDistance(234, "meter"),
            installed_date=datetime(2016, 1, 1, 0, 0, 0),
            power_system_resource_name="Transformer-1",
            insulation_class=InsulationClass.NEMA_A,
            mounting_height=PositiveDistance(10, "meter"),
            pole=Pole.example(),
        )


class PadMountTransformer(_BaseTransformer):
    @classmethod
    def example(cls) -> Self:
        return PadMountTransformer(
            name="Transformer-2",
            location=Location(x=10.0, y=20.0),
            elevation=PositiveDistance(234, "meter"),
            installed_date=datetime(2016, 1, 1, 0, 0, 0),
            power_system_resource_name="Transformer-2",
            insulation_class=InsulationClass.NEMA_A,
        )


class GroundVaultTransformer(_BaseTransformer):
    @classmethod
    def example(cls) -> Self:
        return GroundVaultTransformer(
            name="Transformer-3",
            location=Location(x=10.0, y=20.0),
            elevation=PositiveDistance(234, "meter"),
            installed_date=datetime(2016, 1, 1, 0, 0, 0),
            power_system_resource_name="Transformer-3",
            insulation_class=InsulationClass.NEMA_A,
        )
