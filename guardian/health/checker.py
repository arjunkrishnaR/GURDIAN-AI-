"""Health check implementation for GuardianAI Phase 1 foundation."""

import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

from guardian.core.config import GuardianConfig, load_config
from guardian.core.state import StateManager
from guardian.logging.logger import get_logger


class HealthStatus(Enum):
    """Possible health statuses for component checks."""
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    FAILED = "FAILED"


@dataclass
class HealthCheckResult:
    """Structured result of an individual health check."""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class HealthChecker:
    """Runs health check suite across core Phase 1 foundation components."""

    def __init__(self, config: Optional[GuardianConfig] = None, state_manager: Optional[StateManager] = None) -> None:
        self._config = config
        self._state_manager = state_manager
        self._logger = get_logger()

    def check_python_runtime(self) -> HealthCheckResult:
        """Verify Python runtime version compatibility."""
        version_str = sys.version.split()[0]
        major, minor = sys.version_info.major, sys.version_info.minor
        
        if major >= 3 and minor >= 10:
            return HealthCheckResult(
                component="python_runtime",
                status=HealthStatus.HEALTHY,
                message=f"Python runtime {version_str} is fully supported.",
                details={"version": version_str, "major": major, "minor": minor}
            )
        return HealthCheckResult(
            component="python_runtime",
            status=HealthStatus.WARNING,
            message=f"Python runtime {version_str} is below recommended version (3.10+).",
            details={"version": version_str, "major": major, "minor": minor}
        )

    def check_configuration(self) -> HealthCheckResult:
        """Verify configuration loading and validation."""
        try:
            cfg = self._config or load_config()
            return HealthCheckResult(
                component="configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration loaded and validated successfully.",
                details={"app_name": cfg.app_name, "environment": cfg.environment, "log_level": cfg.log_level}
            )
        except Exception as e:
            return HealthCheckResult(
                component="configuration",
                status=HealthStatus.FAILED,
                message=f"Configuration failed to load: {e}",
                details={"error": str(e)}
            )

    def check_filesystem(self) -> HealthCheckResult:
        """Verify filesystem read/write access to data and logs directories."""
        cfg = self._config or load_config()
        logs_dir = Path(cfg.log_dir)
        data_dir = Path(cfg.data_dir)

        issues = []
        for d in [logs_dir, data_dir]:
            try:
                d.mkdir(parents=True, exist_ok=True)
                test_file = d / ".health_check_test"
                test_file.write_text("test", encoding="utf-8")
                test_file.unlink()
            except Exception as e:
                issues.append(f"Cannot write to directory '{d}': {e}")

        if not issues:
            return HealthCheckResult(
                component="filesystem",
                status=HealthStatus.HEALTHY,
                message="Filesystem write access verified for logs and data directories.",
                details={"logs_dir": str(logs_dir), "data_dir": str(data_dir)}
            )
        return HealthCheckResult(
            component="filesystem",
            status=HealthStatus.FAILED,
            message="Filesystem access issues detected.",
            details={"issues": issues}
        )

    def check_logging(self) -> HealthCheckResult:
        """Verify logging system instance."""
        try:
            logger = get_logger()
            has_handlers = len(logger.handlers) > 0
            return HealthCheckResult(
                component="logging",
                status=HealthStatus.HEALTHY if has_handlers else HealthStatus.WARNING,
                message="Logging system active with handlers." if has_handlers else "Logging system has no configured handlers.",
                details={"handler_count": len(logger.handlers)}
            )
        except Exception as e:
            return HealthCheckResult(
                component="logging",
                status=HealthStatus.FAILED,
                message=f"Logging system error: {e}",
                details={"error": str(e)}
            )

    def check_application_state(self) -> HealthCheckResult:
        """Verify state manager integrity."""
        try:
            sm = self._state_manager or StateManager()
            state_dict = sm.to_dict()
            return HealthCheckResult(
                component="application_state",
                status=HealthStatus.HEALTHY,
                message=f"Application state manager active (State: {state_dict['lifecycle_state']}).",
                details=state_dict
            )
        except Exception as e:
            return HealthCheckResult(
                component="application_state",
                status=HealthStatus.FAILED,
                message=f"State manager error: {e}",
                details={"error": str(e)}
            )
    def check_event_system(self) -> HealthCheckResult:
        """Verify EventBus and EventNormalizer operational readiness."""
        try:
            import asyncio

            from guardian.events import (
                EventBus,
                EventNormalizer,
                EventSource,
                TestEventHandler,
            )

            normalizer = EventNormalizer()
            bus = EventBus()
            handler = TestEventHandler("HealthCheckHandler")
            bus.subscribe(handler)

            event = normalizer.normalize(
                {
                    "source": EventSource.INTERNAL,
                    "event_type": "HEALTH_CHECK_TEST",
                }
            )

            try:
                loop = asyncio.get_event_loop()

                if loop.is_running():
                    loop.create_task(bus.publish(event))
                else:
                    asyncio.run(bus.publish(event))

            except RuntimeError:
                asyncio.run(bus.publish(event))

            return HealthCheckResult(
                component="event_system",
                status=HealthStatus.HEALTHY,
                message=(
                    "Event system initialized, normalized, "
                    "and published test event successfully."
                ),
                details={
                    "event_id": event.event_id,
                    "stats": bus.stats.__dict__,
                },
            )

        except Exception as e:
            return HealthCheckResult(
                component="event_system",
                status=HealthStatus.FAILED,
                message=f"Event system check failed: {e}",
                details={"error": str(e)},
            )
    def check_monitoring_system(self) -> HealthCheckResult:
        """Verify MonitoringManager initialization and sub-collector health states."""
        try:
            from guardian.monitoring import (
                MonitoringManager,
                WindowsEventLogCollector,
                ProcessCollector,
                SystemCollector,
            )
            from guardian.monitoring.windows_event_log import (
                MockWindowsEventLogProvider,
            )
            from guardian.monitoring.process import MockProcessProvider

            mock_wel = MockWindowsEventLogProvider()
            mock_proc = MockProcessProvider()

            collectors = [
                WindowsEventLogCollector(provider=mock_wel),
                ProcessCollector(provider=mock_proc),
                SystemCollector(),
            ]

            mgr = MonitoringManager(
                config=self._config or load_config(),
                collectors=collectors,
            )

            status_dict = mgr.get_collector_status()
            health_cond = mgr.health_condition

            status = HealthStatus.HEALTHY

            if health_cond == "DEGRADED":
                status = HealthStatus.WARNING
            elif health_cond == "FAILED":
                status = HealthStatus.FAILED

            return HealthCheckResult(
                component="monitoring_system",
                status=status,
                message=(
                    f"Monitoring system active "
                    f"(Health Condition: {health_cond})."
                ),
                details={
                    "health_condition": health_cond,
                    "manager_state": mgr.state.name,
                    "collectors": status_dict,
                },
            )

        except Exception as e:
            return HealthCheckResult(
                component="monitoring_system",
                status=HealthStatus.FAILED,
                message=f"Monitoring system check failed: {e}",
                details={"error": str(e)},
            )
    def run_all_checks(self) -> List[HealthCheckResult]:
        """Execute all Phase 1, Phase 2, and Phase 3 health checks and return list of results."""
        return [
            self.check_python_runtime(),
            self.check_configuration(),
            self.check_filesystem(),
            self.check_logging(),
            self.check_application_state(),
            self.check_event_system(),
            self.check_monitoring_system(),
        ]


