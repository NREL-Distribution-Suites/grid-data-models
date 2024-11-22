import pytest
from gdm.structural import (
    Building,
    Pole,
    StreetLight,
    CrossArm,
    TreeTrimming,
    CrossSectionalPoleDimension,
    RoundedPoleDimension,
    PVSystem,
    PadMountTransformer,
    PoleMountedTransformer,
    GroundVaultTransformer,
    UndergroundCable,
    UndergroundJunction,
    OverheadLineSegment,
)


STRUCTURAL_COMPONENTS = [
    Building,
    Pole,
    StreetLight,
    CrossArm,
    TreeTrimming,
    CrossSectionalPoleDimension,
    RoundedPoleDimension,
    PVSystem,
    PadMountTransformer,
    PoleMountedTransformer,
    GroundVaultTransformer,
    UndergroundCable,
    UndergroundJunction,
    OverheadLineSegment,
]


@pytest.mark.parametrize("component", STRUCTURAL_COMPONENTS)
def test_examples(component):
    assert component.example()
