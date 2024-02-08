"""This class contains interface for transmission bus."""

from gdm.bus import PowerSystemBus
from gdm.transmission.transmission_component import TransmissionComponent


class TransmissionBus(PowerSystemBus):
    """Interface for transmission bus."""

    belongs_to: TransmissionComponent
    number: int
    code: int
    bs: float
    gs: float
    status: bool
