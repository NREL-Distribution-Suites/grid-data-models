""" This module contains class for managing basic fields for distribution assets."""

from abc import ABC
from typing import Optional

from infrasys import Component


class TransmissionComponent(Component, ABC):
    """Interface for simple distribution component."""

    area: Optional[int] = None
    zone: Optional[int] = None
