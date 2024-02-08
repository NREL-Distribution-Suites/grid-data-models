"""This class contains interface for transmission substation."""

from infrasys.component_models import ComponentWithQuantities
from gdm.transmission.transmission_bus import TransmissionBus


class TransmissionSubstation(ComponentWithQuantities):
    """Interface for transmission substation."""

    bus: TransmissionBus
