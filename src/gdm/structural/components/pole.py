from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Self

from infrasys import Component, Location
from pydantic import Field

from gdm.quantities import PositiveActivePower, PositiveDistance
from gdm.structural.components.base import _GeoLocatedWithInstalledDateComponent


class PoleMaterial(str, Enum):
    ALUMINUM = "ALUMINUM"
    ALUMINUM_DAVIT = "ALUMINUM_DAVIT"
    FIBERGLASS = "FIBERGLASS"
    GALVANIZED_DAVIT = "GALVANIZED_DAVIT"
    GALVANIZED = "GALVANIZED"
    STEEL_DAVIT_PRIMED = "STEEL_DAVIT_PRIMED"
    STEEL_DAVIT = "STEEL_DAVIT"
    STEEL_STANDARD_PRIMED = "STEEL_STANDARD_PRIMED"
    WOOD_TREATED = "WOOD_TREATED"
    WOOD_HARD = "WOOD_HARD"
    WOOD_SALT_TREATED = "WOOD_SALT_TREATED"
    WOOD_SOFT = "WOOD_SOFT"
    CONCRETE = "CONCRETE"
    WOOD = "WOOD"
    STEEL = "STEEL"
    COMPOSITE = "COMPOSITE"
    STEEL_TUBULAR = "STEEL_TUBULAR"
    IRON = "IRON"
    OTHER = "OTHER"


class PoleClassification(str, Enum):
    CLASS_1 = "1"
    CLASS_2 = "2"
    CLASS_3 = "3"
    CLASS_4 = "4"
    CLASS_5 = "5"
    CLASS_6 = "6"
    CLASS_7 = "7"
    CLASS_H1 = "H1"
    CLASS_H2 = "H2"
    OTHER = "OTHER"


class CrossArmMaterial(str, Enum):
    FIBERGLASS = "FIBERGLASS"
    TREATED_WOOD = "TREATED_WOOD"
    STEEL = "STEEL"
    COMPOSITE = "COMPOSITE"
    ALUMINUM = "ALUMINUM"


class CrossArmType(str, Enum):
    HORIZONTAL = "HORIZONTAL"
    VSHAPED = "VSHAPED"
    DOUBLE = "DOUBLE"
    SIDEARM = "SIDEARM"


class CrossArm(Component):
    """Interface for cross arm."""

    material: Annotated[CrossArmMaterial, Field(..., description="Cross arm material.")]
    arm_type: Annotated[
        CrossArmType,
        Field(..., description="Cross arm type used for the pole."),
    ]
    height: Annotated[PositiveDistance, Field(..., description="Height from the ground.")]
    power_system_resource_name: Annotated[
        str, Field(..., description="Name used in power system bus model.")
    ]

    @classmethod
    def example(cls) -> Self:
        return CrossArm(
            name="CrossArm-1",
            material=CrossArmMaterial.ALUMINUM,
            arm_type=CrossArmType.HORIZONTAL,
            height=PositiveDistance(7.2, "m"),
            power_system_resource_name="Bus-1",
        )


class RoundedPoleDimension(Component):
    """Interface for rounded dimension of pole."""

    name: Annotated[str, Field("", description="Name of the dimension.")]
    ground_diameter: Annotated[
        PositiveDistance, Field(..., description="Pole diameter at the ground.")
    ]
    tip_diameter: Annotated[PositiveDistance, Field(..., description="Pole diameter at the tip.")]

    @classmethod
    def example(cls) -> Self:
        return RoundedPoleDimension(
            ground_diameter=PositiveDistance(20, "inch"), tip_diameter=PositiveDistance(14, "inch")
        )


class CrossSectionalPoleDimension(Component):
    """Interface for rounded dimension of pole."""

    name: Annotated[str, Field("", description="Name of the dimension.")]
    ground_width: Annotated[
        PositiveDistance, Field(..., description="Pole ground width dimension.")
    ]
    tip_width: Annotated[PositiveDistance, Field(..., description="Pole tip width dimension.")]
    ground_depth: Annotated[
        PositiveDistance, Field(..., description="Pole ground depth dimension.")
    ]
    tip_depth: Annotated[PositiveDistance, Field(..., description="Pole tip depth dimension.")]

    @classmethod
    def example(cls) -> Self:
        return CrossSectionalPoleDimension(
            ground_width=PositiveDistance(10, "inch"),
            tip_width=PositiveDistance(8, "inch"),
            ground_depth=PositiveDistance(6, "inch"),
            tip_depth=PositiveDistance(4, "inch"),
        )


class TreeTrimming(Component):
    name: Annotated[str, Field("", description="Name of the dimension.")]
    trimming_cycle: Annotated[timedelta, Field(..., description="How often tree is trimmed.")]
    last_time_trimmed: Annotated[
        datetime,
        Field(..., description="Last time tree is trimmed for this pole."),
    ]

    @classmethod
    def example(cls) -> Self:
        return TreeTrimming(
            trimming_cycle=timedelta(days=180), last_time_trimmed=datetime(2024, 1, 1, 14, 0, 0)
        )


class StreetLight(Component):
    power_rating: Annotated[
        PositiveActivePower,
        Field(..., description="Power rating of the light."),
    ]

    @classmethod
    def example(cls) -> Self:
        return StreetLight(name="StreetLight-1", power_rating=PositiveActivePower(30, "watts"))


class Pole(_GeoLocatedWithInstalledDateComponent):
    """Interface for electric pole."""

    material: Annotated[PoleMaterial, Field(..., description="Pole material type.")]
    height: Annotated[
        PositiveDistance,
        Field(
            ...,
            description="Height of the pole including undergrounded portion.",
        ),
    ]
    dimension: Annotated[
        RoundedPoleDimension | CrossSectionalPoleDimension,
        Field(..., description="Pole dimension."),
    ]
    classification: Annotated[PoleClassification, Field(..., description="Pole class.")]
    cross_arm: Annotated[
        list[CrossArm],
        Field(..., description="Cross arm model for electric pole."),
    ]
    trimming: Annotated[
        TreeTrimming | None,
        Field(None, description="Tree trimming applicable or not."),
    ]
    street_lights: Annotated[
        list[StreetLight],
        Field([], description="Street lights attached to this pole."),
    ]

    @classmethod
    def example(cls) -> Self:
        return Pole(
            name="Pole-P12341",
            elevation=PositiveDistance(300, "meter"),
            location=Location(x=141.00, y=30.0),
            installed_date=datetime(1993, 6, 21, 15, 45, 0),
            material=PoleMaterial.WOOD_TREATED,
            height=PositiveDistance(15, "ft"),
            dimension=RoundedPoleDimension.example(),
            classification=PoleClassification.CLASS_4,
            cross_arm=[CrossArm.example()],
            trimming=TreeTrimming.example(),
            street_lights=[StreetLight.example()],
        )
