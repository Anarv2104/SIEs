from __future__ import annotations

from sie.event_log import EventLog
from sie.types import AgentState, EventType, Task


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def register(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)


def assign_task(state: AgentState, task: Task, log: EventLog) -> None:
    state.current_task_id = task.task_id
    state.current_task_steps = 0
    log.append(EventType.TASK_ASSIGNED, state.agent_id, {"task_id": task.task_id, "required_steps": task.required_steps})


def record_step(state: AgentState, task: Task, log: EventLog) -> None:
    state.current_task_steps += 1
    state.steps_taken += 1
    log.append(EventType.TASK_STEP, state.agent_id, {"task_id": task.task_id, "step": state.current_task_steps})
