from __future__ import annotations

from sie.event_log import EventLog
from sie.types import AgentState, EventType

# Reputation adjustments
TASK_SUCCESS = 0.10
EFFICIENCY_BONUS = 0.05
TASK_FAIL = -0.05
DECEPTION = -0.30
BUDGET_ABUSE = -0.15
PROVIDE_INFLUENCE = 0.08
BOUNDARY_VIOLATION = -0.10


def adjust(state: AgentState, delta: float, reason: str, log: EventLog) -> None:
    old = state.reputation
    state.reputation = max(0.0, min(1.0, state.reputation + delta))
    log.append(
        EventType.REPUTATION_ADJUSTED,
        state.agent_id,
        {"old": round(old, 4), "new": round(state.reputation, 4), "delta": delta, "reason": reason},
    )
