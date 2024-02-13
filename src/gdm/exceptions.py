""" This module contains all exceptions raised by this package."""


class GDMBaseException(Exception):
    """Base exception class for grid data models package."""


class GDMNotAttachedToSystemError(GDMBaseException):
    """Raises this error if the component is not attached."""


class GDMIncompatibleInstanceError(GDMBaseException):
    """Raises this error if incompatible instance is passed."""
