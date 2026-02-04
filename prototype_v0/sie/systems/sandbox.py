from __future__ import annotations

from sie.event_log import EventLog
from sie.types import AgentState, EventType

SANDBOX_THRESHOLD = 2
BAN_THRESHOLD = 4


def record_violation(state: AgentState, reason: str, log: EventLog) -> None:
    state.violation_count += 1
    log.append(EventType.VIOLATION_RECORDED, state.agent_id, {"count": state.violation_count, "reason": reason})

    if state.violation_count >= BAN_THRESHOLD and not state.banned:
        state.banned = True
        log.append(EventType.AGENT_BANNED, state.agent_id, {"violation_count": state.violation_count})
    elif state.violation_count >= SANDBOX_THRESHOLD and not state.sandboxed:
        state.sandboxed = True
        log.append(EventType.AGENT_SANDBOXED, state.agent_id, {"violation_count": state.violation_count})
