"""This module contains distribution fuse."""

from gdm.distribution.components.distribution_branch import SwitchedDistributionBranch


class DistributionFuse(SwitchedDistributionBranch):
    """Interface for distribution fuse."""

    @classmethod
    def example(cls) -> "DistributionFuse":
        return DistributionFuse(
            **SwitchedDistributionBranch.example().model_dump(exclude_none=True),
        )
