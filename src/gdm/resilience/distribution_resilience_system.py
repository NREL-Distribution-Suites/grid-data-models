from infrasys import System

import gdm


class DistributionResilenceSystem(System):
    """Class interface for distribution resilience system."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_format_version = gdm.distribution.__version__
