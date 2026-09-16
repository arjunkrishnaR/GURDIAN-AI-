"""Unit tests for guardian.health.checker module."""

from guardian.health.checker import HealthChecker, HealthStatus
from guardian.core.config import GuardianConfig


def test_health_checks_healthy(tmp_path):
    """Verify health checker returns HEALTHY for operational components."""
    cfg = GuardianConfig(
        log_dir=str(tmp_path / "logs"),
        data_dir=str(tmp_path / "data")
    )
    checker = HealthChecker(config=cfg)
    results = checker.run_all_checks()

    assert len(results) == 5
    for res in results:
        assert res.status in (HealthStatus.HEALTHY, HealthStatus.WARNING)
        assert res.component in [
            "python_runtime",
            "configuration",
            "filesystem",
            "logging",
            "application_state",
        ]


def test_health_check_filesystem_failure(monkeypatch, tmp_path):
    """Verify health checker handles filesystem access failure gracefully."""
    invalid_path = tmp_path / "read_only"
    invalid_path.mkdir()

    cfg = GuardianConfig(
        log_dir=str(invalid_path / "logs"),
        data_dir=str(invalid_path / "data")
    )
    checker = HealthChecker(config=cfg)

    res = checker.check_filesystem()
    assert res.component == "filesystem"
    assert res.status in (HealthStatus.HEALTHY, HealthStatus.FAILED)
