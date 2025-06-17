from pathlib import Path


from pydantic import ValidationError
from gdm.distribution import DistributionSystem
from gdm.distribution.upgrade_handler.upgrade_handler import UpgradeHandler, UpgradeSchema

import pytest

base_path = Path(__file__).parent
model_path = base_path / "dataset" / "p5r" / "p5r.json"


def test_version_bump():
    upgrade_handler = UpgradeHandler()
    DistributionSystem.from_json(filename=model_path, upgrade_handler=upgrade_handler.upgrade)


def test_unique_from_version():
    with pytest.raises(ValidationError):
        UpgradeHandler(
            upgrade_schemas=[
                UpgradeSchema(
                    method=lambda x: x,
                    from_version="1.0.0",
                    to_version="2.0.0",
                ),
                UpgradeSchema(
                    method=lambda x: x,
                    from_version="1.0.0",
                    to_version="2.0.0",
                ),
            ]
        )


def test_unique_to_version():
    with pytest.raises(ValidationError):
        UpgradeHandler(
            upgrade_schemas=[
                UpgradeSchema(
                    method=lambda x: x,
                    from_version="1.0.0",
                    to_version="2.0.0",
                ),
                UpgradeSchema(
                    method=lambda x: x,
                    from_version="1.1.0",
                    to_version="2.0.0",
                ),
            ]
        )


def test_version_chain():
    upgrade_handler = UpgradeHandler(
        upgrade_schemas=[
            UpgradeSchema(
                method=lambda x: x,
                from_version="1.0.0",
                to_version="1.1.0",
            ),
            UpgradeSchema(
                method=lambda x: x,
                from_version="1.2.0",
                to_version="2.0.0",
            ),
        ]
    )
    with pytest.raises(ValueError):
        upgrade_handler.upgrade({}, "1.0.0", "2.0.0")


def test_version_chain_start():
    upgrade_handler = UpgradeHandler(
        upgrade_schemas=[
            UpgradeSchema(
                method=lambda x: x,
                from_version="1.0.0",
                to_version="1.1.0",
            ),
            UpgradeSchema(
                method=lambda x: x,
                from_version="1.1.0",
                to_version="2.0.0",
            ),
        ]
    )
    with pytest.raises(ValueError):
        upgrade_handler.upgrade({}, "0.1.0", "2.0.0")


def test_version_chain_end():
    upgrade_handler = UpgradeHandler(
        upgrade_schemas=[
            UpgradeSchema(
                method=lambda x: x,
                from_version="1.0.0",
                to_version="1.1.0",
            ),
            UpgradeSchema(
                method=lambda x: x,
                from_version="1.1.0",
                to_version="2.0.0",
            ),
        ]
    )
    with pytest.raises(ValueError):
        upgrade_handler.upgrade({}, "1.0.0", "3.0.0")


def test_version_chain_valid():
    upgrade_handler = UpgradeHandler(
        upgrade_schemas=[
            UpgradeSchema(
                method=lambda x, y, z: x,
                from_version="1.0.0",
                to_version="1.1.0",
            ),
            UpgradeSchema(
                method=lambda x, y, z: x,
                from_version="1.1.0",
                to_version="2.0.0",
            ),
            UpgradeSchema(
                method=lambda x, y, z: x,
                from_version="2.0.0",
                to_version="3.0.0",
            ),
        ]
    )
    upgrade_handler.upgrade({}, "1.0.0", "3.0.0")
