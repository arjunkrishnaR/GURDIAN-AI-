"""Exceptions for GuardianAI monitoring subsystem."""

from guardian.core.exceptions import GuardianError


class MonitoringError(GuardianError):
    """Base exception for all monitoring subsystem errors."""
    pass


class CollectorError(MonitoringError):
    """Raised when an individual telemetry collector encounters an unhandled error."""
    pass


class WindowsEventLogError(CollectorError):
    """Raised when Windows Event Log collection fails."""
    pass


class ProcessMonitoringError(CollectorError):
    """Raised when process lifecycle monitoring encounters an error."""
    pass


class SystemMonitoringError(CollectorError):
    """Raised when system event collection encounters an error."""
    pass
