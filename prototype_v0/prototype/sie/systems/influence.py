from __future__ import annotations

from sie.event_log import EventLog
from sie.types import AgentState, EventType


class InfluenceQueue:
    def __init__(self) -> None:
        self._requests: list[dict[str, str]] = []

    def request(self, requester: AgentState, task_id: str, log: EventLog) -> None:
        self._requests.append({"requester_id": requester.agent_id, "task_id": task_id})
        requester.influence_requests.append(task_id)
        log.append(EventType.INFLUENCE_REQUESTED, requester.agent_id, {"task_id": task_id})

    def pending_requests(self) -> list[dict[str, str]]:
        return list(self._requests)

    def fulfill(
        self,
        provider: AgentState,
        requester: AgentState,
        task_id: str,
        log: EventLog,
    ) -> None:
        log.append(
            EventType.INFLUENCE_PROVIDED,
            provider.agent_id,
            {"to": requester.agent_id, "task_id": task_id},
        )
        provider.influence_provided.append(task_id)
        requester.has_received_influence = True
        # Remove the fulfilled request
        self._requests = [
            r for r in self._requests
            if not (r["requester_id"] == requester.agent_id and r["task_id"] == task_id)
        ]
        log.append(
            EventType.INFLUENCE_FULFILLED,
            requester.agent_id,
            {"from": provider.agent_id, "task_id": task_id},
        )
