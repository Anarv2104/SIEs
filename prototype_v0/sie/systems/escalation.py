from __future__ import annotations

from sie.event_log import EventLog
from sie.types import AgentState, EventType, Task


def check_tier(state: AgentState, task: Task, log: EventLog) -> bool:
    if state.tier < task.requires_tier:
        log.append(
            EventType.ESCALATION_DENIED,
            state.agent_id,
            {"reason": "insufficient_tier", "required": task.requires_tier, "current": state.tier, "task_id": task.task_id},
        )
        return False
    return True


def check_sandbox(state: AgentState, action: str, log: EventLog) -> bool:
    if state.sandboxed and action not in ("work_step", "submit_result"):
        log.append(
            EventType.ESCALATION_DENIED,
            state.agent_id,
            {"reason": "sandboxed", "attempted_action": action},
        )
        return False
    return True


def check_influence(task: Task, state: AgentState, log: EventLog) -> bool:
    if task.requires_influence and not state.has_received_influence:
        log.append(
            EventType.ESCALATION_DENIED,
            state.agent_id,
            {"reason": "influence_required", "task_id": task.task_id},
        )
        return False
    return True
