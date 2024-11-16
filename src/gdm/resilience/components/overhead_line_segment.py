from typing import Annotated
from infrasys import Component
from pydantic import Field

from gdm.resilience.components.pole import CrossArm


class OverheadLineSegment(Component):
    power_system_resource_name: Annotated[
        str,
        Field(..., description="Name of branch used in power system model."),
    ]
    from_cross_arm: Annotated[
        CrossArm,
        Field(
            ...,
            description="Cross arm to which this segment is connected from.",
        ),
    ]
    to_corss_arm: Annotated[
        CrossArm,
        Field(..., description="Cross arm to which this segment is connected to."),
    ]
