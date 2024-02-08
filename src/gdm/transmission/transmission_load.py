"""This class contains interface for transmission load."""

from gdm.load import PowerSystemLoad
from gdm.transmission.transmission_bus import TransmissionBus
from gdm.transmission.transmission_component import TransmissionComponent


class TransmissionLoad(PowerSystemLoad):
    """Interface for transmission loads."""

    belongs_to: TransmissionComponent
    bus: TransmissionBus
