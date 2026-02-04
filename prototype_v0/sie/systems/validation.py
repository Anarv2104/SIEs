from __future__ import annotations

from sie.event_log import EventLog
from sie.types import AgentState, EventType, Task


def validate_output(state: AgentState, task: Task, submitted: str, log: EventLog) -> bool:
    log.append(EventType.TASK_SUBMITTED, state.agent_id, {"task_id": task.task_id, "output": submitted})
    if submitted == task.expected_output:
        efficient = state.current_task_steps <= task.required_steps
        state.tasks_completed += 1
        log.append(
            EventType.TASK_VALIDATED,
            state.agent_id,
            {"task_id": task.task_id, "efficient": efficient},
        )
        return True
    else:
        state.tasks_failed += 1
        log.append(
            EventType.TASK_FAILED,
            state.agent_id,
            {"task_id": task.task_id, "expected": task.expected_output, "got": submitted},
        )
        return False
