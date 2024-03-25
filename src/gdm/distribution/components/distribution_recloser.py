"""This module contains distribution recloser."""

from gdm.distribution.components.distribution_branch import SwitchedDistributionBranch


class DistributionRecloser(SwitchedDistributionBranch):
    """Interface for distribution recloser."""

    @classmethod
    def example(cls) -> "DistributionRecloser":
        return DistributionRecloser(
            **SwitchedDistributionBranch.example().model_dump(exclude_none=True),
        )
