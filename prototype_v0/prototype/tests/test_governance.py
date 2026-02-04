"""Assert final agent states match expected governance outcomes."""

from sie.crypto import derive_keypair, verify
from sie.main import build_simulation, run_simulation
from sie.types import EventType, IntentPayload


def _run():
    kernel, agents = build_simulation()
    run_simulation(kernel, agents)
    return kernel


def test_efficient_agent_tier():
    kernel = _run()
    state = kernel.get_state("efficient-1")
    assert state.tier >= 2, f"EfficientAgent should reach tier >= 2, got {state.tier}"
    assert state.tasks_completed >= 1, "EfficientAgent should complete at least 1 task"
    assert not state.banned, "EfficientAgent should not be banned"


def test_deceptive_agent_banned():
    kernel = _run()
    state = kernel.get_state("deceptive-1")
    assert state.banned, "DeceptiveAgent should be banned"
    deception_events = kernel.log.events_of_type(EventType.DECEPTION_FLAGGED)
    deceptive_flags = [e for e in deception_events if e.agent_id == "deceptive-1"]
    assert len(deceptive_flags) >= 2, f"DeceptiveAgent should have >= 2 deception flags, got {len(deceptive_flags)}"


def test_looper_agent_budget():
    kernel = _run()
    state = kernel.get_state("looper-1")
    assert state.budget == 0.0, f"LooperAgent should have 0 budget, got {state.budget}"


def test_specialist_agent_influence():
    kernel = _run()
    state = kernel.get_state("specialist-1")
    assert state.tasks_completed >= 1, "SpecialistAgent should complete at least 1 task"
    influence_fulfilled = [
        e for e in kernel.log.events_of_type(EventType.INFLUENCE_FULFILLED)
        if e.agent_id == "specialist-1"
    ]
    assert len(influence_fulfilled) >= 1, "SpecialistAgent should have received influence"


def test_naive_agent_not_banned():
    kernel = _run()
    state = kernel.get_state("naive-1")
    assert not state.banned, "NaiveAgent should not be banned"
    assert state.tasks_completed >= 1, "NaiveAgent should complete at least 1 task"


def test_boundary_agent_sanctioned():
    kernel = _run()
    state = kernel.get_state("boundary-1")
    assert state.sandboxed or state.banned, "BoundaryAgent should be sandboxed or banned"
    assert state.violation_count >= 2, f"BoundaryAgent should have >= 2 violations, got {state.violation_count}"


def test_signature_sweep():
    kernel = _run()
    intent_events = kernel.log.events_of_type(EventType.INTENT_SUBMITTED)
    assert len(intent_events) > 0, "Should have INTENT_SUBMITTED events"

    for e in intent_events:
        if e.signature and e.agent_id in kernel.public_keys:
            _, pub = derive_keypair(e.agent_id)
            payload = IntentPayload(
                action=e.data.get("action", ""),
                task_id=e.data.get("task_id", ""),
                detail=e.data.get("detail", ""),
            )
            sig_bytes = bytes.fromhex(e.signature)
            assert verify(pub, payload.serialize(), sig_bytes), (
                f"Signature verification failed for event seq={e.sequence} agent={e.agent_id}"
            )


def test_log_integrity():
    kernel = _run()
    events = kernel.log.events
    # Contiguous sequences
    for i, e in enumerate(events):
        assert e.sequence == i, f"Non-contiguous sequence at index {i}: got {e.sequence}"

    # No post-ban INTENT_SUBMITTED
    banned_at: dict[str, int] = {}
    for e in events:
        if e.event_type == EventType.AGENT_BANNED:
            banned_at[e.agent_id] = e.sequence
    for e in events:
        if e.agent_id in banned_at and e.sequence > banned_at[e.agent_id]:
            assert e.event_type != EventType.INTENT_SUBMITTED, (
                f"Post-ban intent from {e.agent_id} at seq={e.sequence}"
            )
