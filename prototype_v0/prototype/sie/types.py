from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(Enum):
    # Agent lifecycle
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_SANDBOXED = "AGENT_SANDBOXED"
    AGENT_BANNED = "AGENT_BANNED"

    # SPAR phases
    INTENT_SUBMITTED = "INTENT_SUBMITTED"
    INTENT_DENIED = "INTENT_DENIED"

    # Budget
    BUDGET_ALLOCATED = "BUDGET_ALLOCATED"
    BUDGET_DEBITED = "BUDGET_DEBITED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    BUDGET_DEFUNDED = "BUDGET_DEFUNDED"

    # Reputation
    REPUTATION_ADJUSTED = "REPUTATION_ADJUSTED"

    # Tier
    TIER_UPGRADED = "TIER_UPGRADED"
    TIER_DOWNGRADED = "TIER_DOWNGRADED"

    # Escalation
    ESCALATION_DENIED = "ESCALATION_DENIED"

    # Task
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_STEP = "TASK_STEP"
    TASK_SUBMITTED = "TASK_SUBMITTED"
    TASK_VALIDATED = "TASK_VALIDATED"
    TASK_FAILED = "TASK_FAILED"

    # Deception
    DECEPTION_FLAGGED = "DECEPTION_FLAGGED"

    # Influence
    INFLUENCE_REQUESTED = "INFLUENCE_REQUESTED"
    INFLUENCE_PROVIDED = "INFLUENCE_PROVIDED"
    INFLUENCE_FULFILLED = "INFLUENCE_FULFILLED"

    # Violations
    VIOLATION_RECORDED = "VIOLATION_RECORDED"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"

    # Round markers
    ROUND_START = "ROUND_START"
    ROUND_END = "ROUND_END"
    SIMULATION_COMPLETE = "SIMULATION_COMPLETE"


@dataclass(frozen=True)
class Event:
    sequence: int
    timestamp: str
    event_type: EventType
    agent_id: str
    data: dict[str, Any]
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "data": self.data,
            "signature": self.signature,
        }


@dataclass
class AgentState:
    agent_id: str
    budget: float = 0.0
    reputation: float = 0.50
    tier: int = 0
    sandboxed: bool = False
    banned: bool = False
    violation_count: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    steps_taken: int = 0
    current_task_id: str | None = None
    current_task_steps: int = 0
    influence_requests: list[str] = field(default_factory=list)
    influence_provided: list[str] = field(default_factory=list)
    has_received_influence: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "budget": self.budget,
            "reputation": round(self.reputation, 4),
            "tier": self.tier,
            "sandboxed": self.sandboxed,
            "banned": self.banned,
            "violation_count": self.violation_count,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "steps_taken": self.steps_taken,
        }


@dataclass(frozen=True)
class Task:
    task_id: str
    difficulty: str
    required_steps: int
    expected_output: str
    budget_cost_per_step: float
    requires_tier: int = 0
    requires_influence: bool = False


@dataclass(frozen=True)
class IntentPayload:
    action: str
    task_id: str
    detail: str

    def serialize(self) -> bytes:
        return json.dumps(
            {"action": self.action, "task_id": self.task_id, "detail": self.detail},
            sort_keys=True,
        ).encode()
