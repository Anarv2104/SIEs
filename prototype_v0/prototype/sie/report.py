from __future__ import annotations

from sie.crypto import derive_keypair, verify
from sie.kernel import Kernel
from sie.types import EventType


def generate_report(kernel: Kernel) -> str:
    log = kernel.log
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("SIE KERNEL PROTOTYPE v0 — SIMULATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Per-agent outcomes
    lines.append("AGENT OUTCOMES")
    lines.append("-" * 40)
    for agent_id, state in sorted(kernel.agents.items()):
        lines.append(f"\n  Agent: {agent_id}")
        lines.append(f"    Budget:       {state.budget:.2f}")
        lines.append(f"    Reputation:   {state.reputation:.4f}")
        lines.append(f"    Tier:         {state.tier}")
        lines.append(f"    Sandboxed:    {state.sandboxed}")
        lines.append(f"    Banned:       {state.banned}")
        lines.append(f"    Violations:   {state.violation_count}")
        lines.append(f"    Tasks Done:   {state.tasks_completed}")
        lines.append(f"    Tasks Failed: {state.tasks_failed}")
        lines.append(f"    Steps Taken:  {state.steps_taken}")

    lines.append("")
    lines.append("GOVERNANCE EVENTS")
    lines.append("-" * 40)

    for etype in [EventType.AGENT_SANDBOXED, EventType.AGENT_BANNED, EventType.DECEPTION_FLAGGED,
                  EventType.BUDGET_EXCEEDED, EventType.BUDGET_DEFUNDED, EventType.ESCALATION_DENIED,
                  EventType.TIER_UPGRADED, EventType.TIER_DOWNGRADED]:
        events = log.events_of_type(etype)
        if events:
            lines.append(f"\n  {etype.value} ({len(events)} events):")
            for e in events:
                lines.append(f"    seq={e.sequence} agent={e.agent_id} {e.data}")

    # Influence chains
    lines.append("")
    lines.append("INFLUENCE CHAINS")
    lines.append("-" * 40)
    requested = log.events_of_type(EventType.INFLUENCE_REQUESTED)
    provided = log.events_of_type(EventType.INFLUENCE_PROVIDED)
    fulfilled = log.events_of_type(EventType.INFLUENCE_FULFILLED)
    if requested:
        for e in requested:
            lines.append(f"  REQUEST:  seq={e.sequence} agent={e.agent_id} task={e.data.get('task_id')}")
    if provided:
        for e in provided:
            lines.append(f"  PROVIDED: seq={e.sequence} agent={e.agent_id} -> {e.data.get('to')} task={e.data.get('task_id')}")
    if fulfilled:
        for e in fulfilled:
            lines.append(f"  FULFILLED: seq={e.sequence} agent={e.agent_id} <- {e.data.get('from')} task={e.data.get('task_id')}")

    if not requested and not provided and not fulfilled:
        lines.append("  (none)")

    # Signature verification sweep
    lines.append("")
    lines.append("SIGNATURE VERIFICATION SWEEP")
    lines.append("-" * 40)
    intent_events = log.events_of_type(EventType.INTENT_SUBMITTED)
    verified_count = 0
    failed_count = 0
    for e in intent_events:
        if e.signature and e.agent_id in kernel.public_keys:
            _, pub = derive_keypair(e.agent_id)
            # Reconstruct the intent payload
            from sie.types import IntentPayload
            payload = IntentPayload(
                action=e.data.get("action", ""),
                task_id=e.data.get("task_id", ""),
                detail=e.data.get("detail", ""),
            )
            sig_bytes = bytes.fromhex(e.signature)
            if verify(pub, payload.serialize(), sig_bytes):
                verified_count += 1
            else:
                failed_count += 1

    lines.append(f"  Total INTENT_SUBMITTED events: {len(intent_events)}")
    lines.append(f"  Verified:   {verified_count}")
    lines.append(f"  Failed:     {failed_count}")

    # Log integrity
    lines.append("")
    lines.append("LOG INTEGRITY")
    lines.append("-" * 40)
    all_events = log.events
    contiguous = all(all_events[i].sequence == i for i in range(len(all_events)))
    lines.append(f"  Total events:      {len(all_events)}")
    lines.append(f"  Contiguous seqs:   {contiguous}")

    # Check no post-ban events from banned agents
    banned_at: dict[str, int] = {}
    post_ban_events = 0
    for e in all_events:
        if e.event_type == EventType.AGENT_BANNED:
            banned_at[e.agent_id] = e.sequence
    for e in all_events:
        if e.agent_id in banned_at and e.sequence > banned_at[e.agent_id]:
            if e.event_type == EventType.INTENT_SUBMITTED:
                post_ban_events += 1
    lines.append(f"  Post-ban intents:  {post_ban_events}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines)
