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


class NoComponentsFoundError(GDMBaseException):
    """Raised if no components are found when it is expected to present in the system."""


class NoTimeSeriesDataFound(GDMBaseException):
    """Raised if no timeseries data found for a component when it is expected."""


class TimeseriesVariableDoesNotExist(GDMBaseException):
    """Raised if expected time series variable does not exist for a component."""


class UnsupportedVariableError(GDMBaseException):
    """Raised if variable is not supported for some purpose."""
