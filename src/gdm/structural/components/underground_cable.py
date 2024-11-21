from datetime import datetime
from typing import Annotated, Self
from pydantic import Field, model_validator

from gdm.structural.components.base import _InstalledDateBaseComponent
from gdm.structural.components.transformer import GroundVaultTransformer, PadMountTransformer
from gdm.structural.components.underground_junction import UndergroundJunction


class UndergroundCable(_InstalledDateBaseComponent):
    power_system_resource_name: Annotated[
        str, Field(..., description="Name of branch used in power system model.")
    ]
    from_component: Annotated[
        UndergroundJunction | GroundVaultTransformer | PadMountTransformer,
        Field(
            ...,
            description="Transformer or underground junction this cable is connected from.",
        ),
    ]
    to_component: Annotated[
        UndergroundJunction | GroundVaultTransformer | PadMountTransformer,
        Field(..., description="Transformer or underground junction this cable is connected to."),
    ]

    @model_validator(mode="after")
    def validate_component_types(self) -> Self:
        if self.from_component.name == self.to_component.name:
            msg = f"{self.from_component.name=} and {self.to_component.name=} can not be the same."
            raise ValueError(msg)

    @classmethod
    def example(cls) -> Self:
        return UndergroundCable(
            name="Cable-1",
            installed_date=datetime(2016, 1, 1, 0, 0, 0),
            power_system_resource_name="Cable-1",
            from_component=GroundVaultTransformer.example(),
            to_component=PadMountTransformer.example().model_copy(update={"name": "Cable-1-to"}),
        )
