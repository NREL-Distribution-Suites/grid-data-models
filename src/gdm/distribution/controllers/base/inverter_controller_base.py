from typing import Annotated
from abc import ABC

from infrasys import Component
from pydantic import Field


class InverterControllerBase(Component, ABC):
    """Interface for Inverter controllers."""

    name: Annotated[str, Field("", description="Name of the inverter controller.")]
