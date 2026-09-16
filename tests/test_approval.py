"""Unit tests for guardian.core.approval module."""

import uuid
import pytest
from datetime import datetime, timedelta, timezone

from guardian.core.approval import (
    ApprovalCheckpoint,
    ApprovalDecision,
    GuardianApprovalError,
    RiskLevel,
)


def test_approval_checkpoint_pending_blocks_action():
    """Verify PENDING decision blocks action execution."""
    chk = ApprovalCheckpoint(
        approval_id=str(uuid.uuid4()),
        action_id="RESTART_SERVICE_FOO",
        description="Restart Service Foo",
        risk_level=RiskLevel.MEDIUM,
        decision=ApprovalDecision.PENDING,
    )
    assert chk.is_valid_for_execution("RESTART_SERVICE_FOO") is False


def test_approval_checkpoint_approved_permits_action():
    """Verify APPROVED decision permits execution of matching action_id."""
    chk = ApprovalCheckpoint(
        approval_id=str(uuid.uuid4()),
        action_id="RESTART_SERVICE_FOO",
        description="Restart Service Foo",
        risk_level=RiskLevel.HIGH,
        decision=ApprovalDecision.APPROVED,
        approved_at=datetime.now(timezone.utc),
    )
    assert chk.is_valid_for_execution("RESTART_SERVICE_FOO") is True


def test_approval_checkpoint_denied_blocks_action():
    """Verify DENIED decision blocks execution."""
    chk = ApprovalCheckpoint(
        approval_id=str(uuid.uuid4()),
        action_id="RESTART_SERVICE_FOO",
        description="Restart Service Foo",
        risk_level=RiskLevel.HIGH,
        decision=ApprovalDecision.DENIED,
    )
    assert chk.is_valid_for_execution("RESTART_SERVICE_FOO") is False


def test_approval_checkpoint_expired_blocks_action():
    """Verify expired approval blocks execution even if marked APPROVED."""
    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    chk = ApprovalCheckpoint(
        approval_id=str(uuid.uuid4()),
        action_id="RESTART_SERVICE_FOO",
        description="Restart Service Foo",
        risk_level=RiskLevel.HIGH,
        decision=ApprovalDecision.APPROVED,
        expires_at=past,
    )
    assert chk.is_expired() is True
    assert chk.get_effective_decision() == ApprovalDecision.EXPIRED
    assert chk.is_valid_for_execution("RESTART_SERVICE_FOO") is False


def test_action_id_binding_non_transitive():
    """Verify approval for action_A does NOT permit execution of action_B."""
    chk = ApprovalCheckpoint(
        approval_id=str(uuid.uuid4()),
        action_id="RESTART_CHROME",
        description="Restart Chrome browser",
        risk_level=RiskLevel.LOW,
        decision=ApprovalDecision.APPROVED,
    )

    # Valid for exact bound action
    assert chk.is_valid_for_execution("RESTART_CHROME") is True

    # Invalid for any other action
    assert chk.is_valid_for_execution("INSTALL_SOFTWARE") is False
    assert chk.is_valid_for_execution("MODIFY_REGISTRY") is False
    assert chk.is_valid_for_execution("DELETE_FILES") is False


def test_high_critical_risk_requires_explicit_approved():
    """Verify HIGH and CRITICAL risk actions strictly require APPROVED state."""
    for risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        chk_pending = ApprovalCheckpoint(
            approval_id=str(uuid.uuid4()),
            action_id="CRITICAL_SYS_FIX",
            description="Critical System Repair",
            risk_level=risk,
            decision=ApprovalDecision.PENDING,
        )
        assert chk_pending.is_valid_for_execution("CRITICAL_SYS_FIX") is False

        chk_approved = ApprovalCheckpoint(
            approval_id=str(uuid.uuid4()),
            action_id="CRITICAL_SYS_FIX",
            description="Critical System Repair",
            risk_level=risk,
            decision=ApprovalDecision.APPROVED,
        )
        assert chk_approved.is_valid_for_execution("CRITICAL_SYS_FIX") is True


def test_checkpoint_immutability():
    """Verify ApprovalCheckpoint fields cannot be mutated."""
    chk = ApprovalCheckpoint(
        approval_id=str(uuid.uuid4()),
        action_id="FIX_LOGS",
        description="Clear temporary logs",
        risk_level=RiskLevel.LOW,
    )
    with pytest.raises(AttributeError):
        chk.decision = ApprovalDecision.APPROVED  # type: ignore


def test_empty_action_id_raises_error():
    """Verify empty or blank action_id raises GuardianApprovalError."""
    with pytest.raises(GuardianApprovalError):
        ApprovalCheckpoint(
            approval_id=str(uuid.uuid4()),
            action_id="",
            description="Invalid action",
            risk_level=RiskLevel.LOW,
        )


def test_approval_checkpoint_json_round_trip():
    """Verify serialization to/from JSON."""
    original = ApprovalCheckpoint(
        approval_id=str(uuid.uuid4()),
        action_id="RESTART_APP",
        correlation_id="INCIDENT_999",
        description="Restart application instance",
        risk_level=RiskLevel.MEDIUM,
        decision=ApprovalDecision.APPROVED,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        approved_at=datetime.now(timezone.utc),
    )

    json_str = original.to_json()
    reconstructed = ApprovalCheckpoint.from_json(json_str)

    assert reconstructed.approval_id == original.approval_id
    assert reconstructed.action_id == original.action_id
    assert reconstructed.correlation_id == original.correlation_id
    assert reconstructed.risk_level == RiskLevel.MEDIUM
    assert reconstructed.decision == ApprovalDecision.APPROVED
    assert reconstructed.is_valid_for_execution("RESTART_APP") is True
