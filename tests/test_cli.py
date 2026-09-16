"""Unit tests for guardian.cli.commands module."""

from guardian.cli.commands import cli_main


def test_cli_version(capsys):
    """Verify version command output."""
    code = cli_main(["version"])
    assert code == 0
    captured = capsys.readouterr()
    assert "GuardianAI v0.1.0" in captured.out


def test_cli_status(capsys):
    """Verify status command output."""
    code = cli_main(["status"])
    assert code == 0
    captured = capsys.readouterr()
    assert "GuardianAI Application Status" in captured.out
    assert "Lifecycle State : STOPPED" in captured.out


def test_cli_health(capsys, tmp_path, monkeypatch):
    """Verify health command output."""
    monkeypatch.setenv("GUARDIAN_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("GUARDIAN_DATA_DIR", str(tmp_path / "data"))
    code = cli_main(["health"])
    assert code == 0
    captured = capsys.readouterr()
    assert "OVERALL HEALTH: PASSED" in captured.out


def test_cli_start(capsys, tmp_path, monkeypatch):
    """Verify start command output."""
    monkeypatch.setenv("GUARDIAN_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("GUARDIAN_DATA_DIR", str(tmp_path / "data"))
    code = cli_main(["start"])
    assert code == 0
    captured = capsys.readouterr()
    assert "started successfully" in captured.out


def test_cli_no_args(capsys):
    """Verify CLI behavior when invoked without arguments."""
    code = cli_main([])
    assert code == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "guardian" in captured.out.lower()
