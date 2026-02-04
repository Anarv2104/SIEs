from __future__ import annotations

import json
from typing import Any

from sie.types import Event, EventType

# Fixed deterministic timestamp for reproducibility
FIXED_TIMESTAMP = "2025-01-01T00:00:00Z"


class EventLog:
    def __init__(self) -> None:
        self._events: list[Event] = []
        self._sequence: int = 0

    def append(
        self,
        event_type: EventType,
        agent_id: str,
        data: dict[str, Any],
        signature: str = "",
    ) -> Event:
        event = Event(
            sequence=self._sequence,
            timestamp=FIXED_TIMESTAMP,
            event_type=event_type,
            agent_id=agent_id,
            data=data,
            signature=signature,
        )
        self._events.append(event)
        self._sequence += 1
        return event

    @property
    def events(self) -> list[Event]:
        return list(self._events)

    def to_json(self) -> str:
        return json.dumps(
            [e.to_dict() for e in self._events],
            indent=2,
            sort_keys=False,
        )

    def events_for_agent(self, agent_id: str) -> list[Event]:
        return [e for e in self._events if e.agent_id == agent_id]

    def events_of_type(self, event_type: EventType) -> list[Event]:
        return [e for e in self._events if e.event_type == event_type]
