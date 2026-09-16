"""Explicit Approval Checkpoint Contract for GuardianAI.

Establishes the safety invariant: NO APPROVAL = NO HIGH-IMPACT ACTION.
The AI recommendation engine can propose and explain actions, but only explicit
human user approval authorizes action execution.
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from guardian.core.exceptions import GuardianError


class GuardianApprovalError(GuardianError):
    """Raised when an invalid approval operation or unauthorized execution is attempted."""
    pass


class ApprovalDecision(Enum):
    """Possible decision states for an approval checkpoint."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"


class RiskLevel(Enum):
    """Risk impact classification for proposed actions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class ApprovalCheckpoint:
    """
    Contract representing an approval checkpoint for a specific proposed action.
    
    Attributes:
        approval_id: Unique UUID v4 for this approval checkpoint.
        action_id: Specific identifier of the proposed action (non-transitive).
        description: Readable description of what the proposed action will do.
        risk_level: Risk impact classification.
        decision: Current approval decision state.
        created_at: Timezone-aware UTC creation timestamp.
        correlation_id: Optional correlation ID linking to event/incident chain.
        expires_at: Optional timezone-aware UTC expiration timestamp.
        approved_at: Optional timezone-aware UTC timestamp when approval occurred.
    """
    approval_id: str
    action_id: str
    description: str
    risk_level: RiskLevel
    decision: ApprovalDecision = ApprovalDecision.PENDING
    created_at: datetime = None  # type: ignore
    correlation_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate timestamps and ensure timezone-awareness."""
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
        elif self.created_at.tzinfo is None:
            object.__setattr__(self, "created_at", self.created_at.replace(tzinfo=timezone.utc))

        if self.expires_at is not None and self.expires_at.tzinfo is None:
            object.__setattr__(self, "expires_at", self.expires_at.replace(tzinfo=timezone.utc))

        if self.approved_at is not None and self.approved_at.tzinfo is None:
            object.__setattr__(self, "approved_at", self.approved_at.replace(tzinfo=timezone.utc))

        if not self.approval_id:
            object.__setattr__(self, "approval_id", str(uuid.uuid4()))

        if not self.action_id or not self.action_id.strip():
            raise GuardianApprovalError("ApprovalCheckpoint must specify a valid, non-empty action_id.")

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Check if approval has passed its expiration timestamp."""
        if self.expires_at is None:
            return False
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        return current_time > self.expires_at

    def get_effective_decision(self, now: Optional[datetime] = None) -> ApprovalDecision:
        """Return actual effective decision accounting for expiration."""
        if self.decision == ApprovalDecision.APPROVED and self.is_expired(now):
            return ApprovalDecision.EXPIRED
        if self.decision == ApprovalDecision.PENDING and self.is_expired(now):
            return ApprovalDecision.EXPIRED
        return self.decision

    def is_valid_for_execution(self, requested_action_id: str, now: Optional[datetime] = None) -> bool:
        """
        Evaluate whether this approval authorizes execution of requested_action_id.
        
        Returns True ONLY IF:
        1. Current effective decision is ApprovalDecision.APPROVED.
        2. requested_action_id exactly matches bound action_id.
        3. Checkpoint is not expired.
        """
        if not requested_action_id or requested_action_id != self.action_id:
            return False

        if self.is_expired(now):
            return False

        return self.decision == ApprovalDecision.APPROVED

    def to_dict(self) -> Dict[str, Any]:
        """Convert ApprovalCheckpoint to dictionary representation."""
        return {
            "approval_id": self.approval_id,
            "action_id": self.action_id,
            "correlation_id": self.correlation_id,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "decision": self.decision.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalCheckpoint":
        """Reconstruct ApprovalCheckpoint from dictionary safely."""
        try:
            created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data and data["created_at"] else datetime.now(timezone.utc)
            expires_at = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            approved_at = datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None

            risk_level = RiskLevel(data["risk_level"]) if isinstance(data.get("risk_level"), str) else data["risk_level"]
            decision = ApprovalDecision(data["decision"]) if isinstance(data.get("decision"), str) else data.get("decision", ApprovalDecision.PENDING)

            return cls(
                approval_id=str(data.get("approval_id", str(uuid.uuid4()))),
                action_id=str(data["action_id"]),
                correlation_id=data.get("correlation_id"),
                description=str(data.get("description", "")),
                risk_level=risk_level,
                decision=decision,
                created_at=created_at,
                expires_at=expires_at,
                approved_at=approved_at,
            )
        except Exception as e:
            if isinstance(e, GuardianApprovalError):
                raise
            raise GuardianApprovalError(f"Failed to deserialize ApprovalCheckpoint: {e}") from e

    def to_json(self) -> str:
        """Serialize ApprovalCheckpoint to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ApprovalCheckpoint":
        """Reconstruct ApprovalCheckpoint from JSON string safely."""
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise GuardianApprovalError("JSON payload must resolve to a dictionary.")
            return cls.from_dict(data)
        except Exception as e:
            if isinstance(e, GuardianApprovalError):
                raise
            raise GuardianApprovalError(f"Failed to parse ApprovalCheckpoint from JSON: {e}") from e
