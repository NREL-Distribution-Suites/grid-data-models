""" Interface for transmission branch."""

from infrasys.component_models import ComponentWithQuantities
from infrasys.quantities import ActivePower

from gdm.transmission.transmission_bus import TransmissionBus
from gdm.transmission.transmission_component import TransmissionComponent


class TransmissionBranch(ComponentWithQuantities):
    """Interface for transmission branch."""

    belongs_to: TransmissionComponent
    from_bus: TransmissionBus
    to_bus: TransmissionBus
    rate_a: ActivePower
    rate_b: ActivePower
    rate_c: ActivePower
