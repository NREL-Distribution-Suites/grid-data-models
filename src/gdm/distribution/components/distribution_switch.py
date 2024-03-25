""" This module contains distribution switch. """

from gdm.distribution.components.distribution_branch import SwitchedDistributionBranch


class DistributionSwitch(SwitchedDistributionBranch):
    """Interface for distribution switch."""

    @classmethod
    def example(cls) -> "DistributionSwitch":
        return DistributionSwitch(
            **SwitchedDistributionBranch.example().model_dump(exclude_none=True),
        )
