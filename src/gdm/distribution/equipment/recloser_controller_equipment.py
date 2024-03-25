""" This module stores recloser controller equipment."""

from infrasys.component_models import ComponentWithQuantities


class RecloserControllerEquipment(ComponentWithQuantities):
    """Class interface for recloser controller equipment."""

    @classmethod
    def example(cls) -> "RecloserControllerEquipment":
        """Example for matrix impedance recloser equipment."""
        return RecloserControllerEquipment(name="SEL-5460")
