from infrasys import System

import gdm


class SructuralSystem(System):
    """Class interface for structural distribution system."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_format_version = gdm.distribution.__version__
