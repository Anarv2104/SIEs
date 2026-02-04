from __future__ import annotations

from sie.event_log import EventLog
from sie.types import AgentState, EventType

# Tier thresholds by reputation
TIER_THRESHOLDS = {
    1: 0.55,
    2: 0.70,
    3: 0.85,
}


def evaluate(state: AgentState, log: EventLog) -> None:
    old_tier = state.tier
    new_tier = 0
    for t, threshold in sorted(TIER_THRESHOLDS.items()):
        if state.reputation >= threshold:
            new_tier = t
    if new_tier > old_tier:
        state.tier = new_tier
        log.append(EventType.TIER_UPGRADED, state.agent_id, {"old_tier": old_tier, "new_tier": new_tier, "reputation": round(state.reputation, 4)})
    elif new_tier < old_tier:
        state.tier = new_tier
        log.append(EventType.TIER_DOWNGRADED, state.agent_id, {"old_tier": old_tier, "new_tier": new_tier, "reputation": round(state.reputation, 4)})
