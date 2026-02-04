from __future__ import annotations

from sie.event_log import EventLog
from sie.types import AgentState, EventType


def allocate(state: AgentState, amount: float, log: EventLog) -> None:
    state.budget += amount
    log.append(EventType.BUDGET_ALLOCATED, state.agent_id, {"amount": amount, "new_balance": state.budget})


def debit(state: AgentState, amount: float, log: EventLog) -> bool:
    if state.budget < amount:
        log.append(EventType.BUDGET_EXCEEDED, state.agent_id, {"attempted": amount, "balance": state.budget})
        defund(state, log)
        return False
    state.budget -= amount
    log.append(EventType.BUDGET_DEBITED, state.agent_id, {"amount": amount, "new_balance": state.budget})
    return True


def defund(state: AgentState, log: EventLog) -> None:
    state.budget = 0.0
    log.append(EventType.BUDGET_DEFUNDED, state.agent_id, {"new_balance": 0.0})
