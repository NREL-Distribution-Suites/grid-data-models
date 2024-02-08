"""This class contains interface for transmission capacitor."""

from gdm.capacitor import PowerSystemCapacitor
from gdm.transmission.transmission_bus import TransmissionBus
from gdm.transmission.transmission_component import TransmissionComponent


class TransmissionCapacitor(PowerSystemCapacitor):
    """Interface for representing capacitor in transmission system."""

    belongs_to: TransmissionComponent
    bus: TransmissionBus
