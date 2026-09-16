"""Custom exception hierarchy for GuardianAI."""


class GuardianError(Exception):
    """Base exception for all GuardianAI errors."""
    pass


class ConfigError(GuardianError):
    """Raised when configuration loading, parsing, or validation fails."""
    pass


class StateError(GuardianError):
    """Raised when application state transition or state mutation fails."""
    pass


class HealthCheckError(GuardianError):
    """Raised when a health check execution encounters an unhandled failure."""
    pass


class LifecycleError(GuardianError):
    """Raised when application lifecycle state management fails."""
    pass


class EventError(GuardianError):
    """Base exception for event system errors."""
    pass


class EventNormalizationError(EventError):
    """Raised when raw event normalization fails or payload is malformed."""
    pass


class EventBusError(EventError):
    """Raised when event bus operations or handler dispatch encounters an unhandled error."""
    pass
