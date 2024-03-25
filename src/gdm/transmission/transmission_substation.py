"""This class contains interface for transmission substation."""

from infrasys import Component
from gdm.transmission.transmission_bus import TransmissionBus


class TransmissionSubstation(Component):
    """Interface for transmission substation."""

    bus: TransmissionBus
