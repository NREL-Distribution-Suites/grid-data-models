from datetime import datetime
from enum import Enum
from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveAngle, PositiveDistance, PositiveWeight


class PoleMaterial(str, Enum):
    CONCRETE = "CONCRETE"
    WOOD = "WOOD"
    STEEL = "STEEL"
    COMPOSITE = "COMPOSITE"
    STEEL_TUBULAR = "STEEL_TUBULAR"
    IRON = "IRON"
    OTHER = "OTHER"


class FoundationType(str, Enum):
    DIRECT_EMBEDMENT = "DIRECT_EMBEDMENT"
    ANCHOR = "ANCHOR"


class GuyWireMaterial(str, Enum):
    GALVANIZED_STEEL = "GALVANIZED_STEEL"
    STAINLESS_STEEL = "STAINLESS_STEEL"


class CrossArmMaterial(str, Enum):
    FIBERGLASS = "FIBERGLASS"
    TREATED_WOOD = "TREATED_WOOD"
    STEEL = "STEEL"
    COMPOSITE = "COMPOSITE"
    ALUMINUM = "ALUMINUM"


class CrossArm(Component):
    """Interface for cross arm."""

    material: Annotated[CrossArmMaterial, Field(..., description="Cross arm material.")]
    weight: Annotated[PositiveWeight, Field(..., description="Weight of cross arm.")]


class HorizontalCrossArm(CrossArm):
    length: Annotated[PositiveDistance, Field(..., description="Length of cross arm.")]
    width: Annotated[PositiveDistance, Field(..., description="Width of cross arm.")]
    thickness: Annotated[PositiveDistance, Field(..., description="Thickness of cross arm.")]
    height: Annotated[
        PositiveDistance, Field(..., description="Height of cross arm from base of pole.")
    ]


class VShapedCrossArm(HorizontalCrossArm):
    span_width: Annotated[PositiveDistance, Field(..., description="Distance between arms.")]
    apex_angle: Annotated[
        PositiveAngle, Field(..., description="Angle between two v shaped arms.")
    ]


class DoubleCrossArm(CrossArm):
    upper_arm: Annotated[HorizontalCrossArm, Field(..., description="Upper cross arm.")]
    lower_arm: Annotated[HorizontalCrossArm, Field(..., description="Lower cross arm.")]
    separation: Annotated[
        PositiveDistance, Field(..., description="Separation between cross arms.")
    ]


class SideArmedCrossArm(HorizontalCrossArm):
    pass


class GuyWire(Component):
    """Interface for Guy wire."""

    anchor_radius: Annotated[
        PositiveDistance,
        Field(
            ...,
            description="Horizontal distance from base of the pole to anchor.",
        ),
    ]
    attachement_angle: Annotated[
        PositiveAngle, Field(..., description="Angle relative to the pole.")
    ]
    diameter: Annotated[PositiveDistance, Field(..., description="Diameter of the giy wire.")]
    material: Annotated[GuyWireMaterial, Field(..., description="Material used for guy wire.")]


class RoundedPoleDimension(Component):
    """Interface for rounded dimension of pole."""

    ground_diameter: Annotated[
        PositiveDistance, Field(..., description="Pole diameter at the ground.")
    ]
    tip_diameter: Annotated[PositiveDistance, Field(..., description="Pole diameter at the tip.")]


class CrossSectionalPoleDimension(Component):
    """Interface for rounded dimension of pole."""

    ground_width: Annotated[
        PositiveDistance, Field(..., description="Pole ground width dimension.")
    ]
    tip_width: Annotated[PositiveDistance, Field(..., description="Pole tip width dimension.")]
    ground_depth: Annotated[
        PositiveDistance, Field(..., description="Pole ground depth dimension.")
    ]
    tip_deth: Annotated[PositiveDistance, Field(..., description="Pole tip depth dimension.")]


class ElectricPole(Component):
    """Interface for electric pole."""

    material: Annotated[PoleMaterial, Field(..., description="Pole material type.")]
    height: Annotated[
        PositiveDistance,
        Field(..., description="Height of the pole from ground."),
    ]
    dimension: Annotated[
        RoundedPoleDimension | CrossSectionalPoleDimension,
        Field(..., description="Pole dimension."),
    ]
    foundation_type: Annotated[FoundationType, Field(..., description="Type of foundation used.")]
    foundation_depth: Annotated[PositiveDistance, Field(..., description="Depth of foundation.")]
    installed_date: Annotated[datetime, Field(..., description="When the pole was installed.")]
    weight: Annotated[PositiveWeight, Field(..., description="Total weight of the pole.")]
    guy_wires: Annotated[
        list[GuyWire],
        Field(..., description="List of guy wires used to support pole."),
    ]
    guy_wire_spacings: Annotated[
        list[PositiveAngle],
        Field(..., description="Angle of separation between guy wires."),
    ]
    cross_arm: Annotated[
        list[CrossArm], Field(..., description="Cross arm model for electric pole.")
    ]
