""" Interface for power system bus."""
# standard imports

# third-party imports
from typing import Optional
from infra_sys.component_models import ComponentWithQuantities

# internal imports
from infra_sys.quantities import Voltage
from powersystem_data_models.enums import Phase


class Node(ComponentWithQuantities):
    """Interface for node."""

    nominal_voltage: Voltage
    phases: Optional[list[Phase]] = None



