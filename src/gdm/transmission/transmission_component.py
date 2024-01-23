""" This module contains class for managing basic fields for distribution assets."""
from abc import ABC
from typing import Optional

from infrasys.component_models import ComponentWithQuantities


class TransmissionComponent(ComponentWithQuantities, ABC):
    """Interface for simple distribution component."""

    area: Optional[int] = None
    zone: Optional[int] = None
