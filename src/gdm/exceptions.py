""" This module contains all exceptions raised by this package."""


class GDMBaseException(Exception):
    """Base exception class for grid data models package."""


class GDMNotAttachedToSystemError(GDMBaseException):
    """Raises this error if the component is not attached."""


class GDMIncompatibleInstanceError(GDMBaseException):
    """Raises this error if incompatible instance is passed."""


class MultipleOrEmptyVsourceFound(GDMBaseException):
    """Raises this error if multiple or no vsource found."""


class InconsistentTimeseriesAggregation(GDMBaseException):
    """Raises this error if time series data aggregated are inconsistent."""


class FolderAlreadyExistsError(GDMBaseException):
    """Raised if folder already exists which is not suppose to exist."""
