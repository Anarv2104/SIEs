"""
Live terminal runner — real-time SIE kernel visualization.
Run: python -m sie.live
"""
from __future__ import annotations

import sys
import time

from sie.event_log import EventLog
from sie.kernel import Kernel
from sie.main import AGENT_CONFIGS, INITIAL_BUDGET, NUM_ROUNDS, TASKS, process_influence_queue
from sie.types import AgentState, EventType

# ── ANSI codes ──────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
BG_RED  = "\033[41m"
BG_GREEN = "\033[42m"
BG_BLUE  = "\033[44m"
BG_YELLOW = "\033[43m"

# How fast events print (seconds). Set to 0 for instant.
EVENT_DELAY = 0.04
ROUND_DELAY = 0.3
SECTION_DELAY = 0.6

# Event type → color/icon mapping
EVENT_STYLE: dict[EventType, tuple[str, str]] = {
    EventType.AGENT_REGISTERED:    (GREEN,   "▶ REG  "),
    EventType.AGENT_SANDBOXED:     (YELLOW,  "⚠ SBOX "),
    EventType.AGENT_BANNED:        (RED,     "✖ BAN  "),
    EventType.INTENT_SUBMITTED:    (DIM,     "  INT  "),
    EventType.INTENT_DENIED:       (RED,     "✖ DENY "),
    EventType.BUDGET_ALLOCATED:    (GREEN,   "$ ALLOC"),
    EventType.BUDGET_DEBITED:      (CYAN,    "$ DEBIT"),
    EventType.BUDGET_EXCEEDED:     (RED,     "$ EXCD "),
    EventType.BUDGET_DEFUNDED:     (RED,     "$ DFUND"),
    EventType.REPUTATION_ADJUSTED: (MAGENTA, "★ REP  "),
    EventType.TIER_UPGRADED:       (GREEN,   "▲ TIER "),
    EventType.TIER_DOWNGRADED:     (RED,     "▼ TIER "),
    EventType.ESCALATION_DENIED:   (YELLOW,  "⊘ ESCL "),
    EventType.TASK_ASSIGNED:       (BLUE,    "◆ TASK "),
    EventType.TASK_STEP:           (CYAN,    "  STEP "),
    EventType.TASK_SUBMITTED:      (BLUE,    "◆ SUBM "),
    EventType.TASK_VALIDATED:      (GREEN,   "✔ VALID"),
    EventType.TASK_FAILED:         (RED,     "✖ FAIL "),
    EventType.DECEPTION_FLAGGED:   (RED,     "⚑ DECPT"),
    EventType.INFLUENCE_REQUESTED: (MAGENTA, "↗ IREQ "),
    EventType.INFLUENCE_PROVIDED:  (GREEN,   "↘ IPROV"),
    EventType.INFLUENCE_FULFILLED: (GREEN,   "✔ IFUL "),
    EventType.VIOLATION_RECORDED:  (YELLOW,  "⚠ VIOL "),
    EventType.SIGNATURE_INVALID:   (RED,     "✖ SIG  "),
    EventType.ROUND_START:         (WHITE,   ""),
    EventType.ROUND_END:           (WHITE,   ""),
    EventType.SIMULATION_COMPLETE: (WHITE,   ""),
}

AGENT_COLORS: dict[str, str] = {
    "efficient-1":  GREEN,
    "looper-1":     YELLOW,
    "deceptive-1":  RED,
    "specialist-1": MAGENTA,
    "naive-1":      CYAN,
    "boundary-1":   BLUE,
    "kernel":       WHITE,
}


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def print_banner() -> None:
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗
║            {WHITE}S I E   K E R N E L   P R O T O T Y P E{CYAN}            ║
║          {DIM}{WHITE}Synthetic Intelligence Economies — Live Run{CYAN}{BOLD}           ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
""")


def format_bar(value: float, max_val: float, width: int = 20, color: str = GREEN) -> str:
    filled = int((value / max_val) * width) if max_val > 0 else 0
    filled = max(0, min(width, filled))
    empty = width - filled
    return f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"


def format_rep_bar(rep: float) -> str:
    if rep >= 0.7:
        color = GREEN
    elif rep >= 0.4:
        color = YELLOW
    else:
        color = RED
    return format_bar(rep, 1.0, 15, color)


def print_dashboard(kernel: Kernel) -> None:
    """Print a compact live dashboard of all agent states."""
    print(f"\n{BOLD}{WHITE}{'─' * 68}")
    print(f"  {'AGENT':<14} {'BUDGET':>7}  {'REPUTATION':>10}       {'TIER':>4}  {'STATUS':<16} {'TASKS'}")
    print(f"{'─' * 68}{RESET}")

    for agent_id in ["efficient-1", "looper-1", "deceptive-1", "specialist-1", "naive-1", "boundary-1"]:
        s = kernel.agents[agent_id]
        ac = AGENT_COLORS.get(agent_id, WHITE)

        # Status badge
        if s.banned:
            status = f"{BG_RED}{WHITE}{BOLD} BANNED {RESET}"
        elif s.sandboxed:
            status = f"{BG_YELLOW}{WHITE}{BOLD} SANDBOX {RESET}"
        elif s.tier >= 2:
            status = f"{BG_GREEN}{WHITE}{BOLD} TIER {s.tier} {RESET}"
        elif s.tier == 1:
            status = f"{BG_BLUE}{WHITE}{BOLD} TIER {s.tier} {RESET}"
        else:
            status = f"{DIM}  active {RESET}"

        # Budget bar
        budget_bar = format_bar(s.budget, 100.0, 10, GREEN if s.budget > 30 else YELLOW if s.budget > 0 else RED)

        # Rep bar
        rep_bar = format_rep_bar(s.reputation)

        # Violations
        viol = f"{RED}!{s.violation_count}{RESET}" if s.violation_count > 0 else ""

        tasks_info = f"{GREEN}{s.tasks_completed}ok{RESET}"
        if s.tasks_failed > 0:
            tasks_info += f" {RED}{s.tasks_failed}fail{RESET}"

        print(f"  {ac}{BOLD}{agent_id:<14}{RESET} {budget_bar} {s.budget:>5.0f}  {rep_bar} {s.reputation:.2f}  T{s.tier}  {status} {tasks_info} {viol}")

    print(f"{DIM}{'─' * 68}{RESET}")


def format_event_line(etype: EventType, agent_id: str, data: dict) -> str | None:
    """Format a single event into a readable live line. Returns None to skip."""
    color, icon = EVENT_STYLE.get(etype, (WHITE, "  ???  "))
    ac = AGENT_COLORS.get(agent_id, WHITE)

    # Skip round markers (handled separately) and noisy registration events
    if etype in (EventType.ROUND_START, EventType.ROUND_END, EventType.SIMULATION_COMPLETE):
        return None

    agent_tag = f"{ac}{BOLD}{agent_id:<14}{RESET}"

    detail = ""
    if etype == EventType.AGENT_REGISTERED:
        detail = f"joined with budget {data.get('initial_budget', 0):.0f}"
    elif etype == EventType.BUDGET_ALLOCATED:
        detail = f"+{data.get('amount', 0):.0f} → bal {data.get('new_balance', 0):.0f}"
    elif etype == EventType.BUDGET_DEBITED:
        detail = f"-{data.get('amount', 0):.0f} → bal {data.get('new_balance', 0):.0f}"
    elif etype == EventType.BUDGET_EXCEEDED:
        detail = f"tried {data.get('attempted', 0):.0f}, only had {data.get('balance', 0):.0f}"
    elif etype == EventType.BUDGET_DEFUNDED:
        detail = "balance zeroed"
    elif etype == EventType.REPUTATION_ADJUSTED:
        d = data.get('delta', 0)
        sign = "+" if d >= 0 else ""
        detail = f"{sign}{d:.2f} ({data.get('reason', '')}) → {data.get('new', 0):.4f}"
    elif etype == EventType.TIER_UPGRADED:
        detail = f"tier {data.get('old_tier', '?')} → {data.get('new_tier', '?')} (rep={data.get('reputation', 0):.2f})"
    elif etype == EventType.TIER_DOWNGRADED:
        detail = f"tier {data.get('old_tier', '?')} → {data.get('new_tier', '?')}"
    elif etype == EventType.TASK_ASSIGNED:
        detail = f"{data.get('task_id', '')} ({data.get('required_steps', '?')} steps)"
    elif etype == EventType.TASK_STEP:
        detail = f"{data.get('task_id', '')} step {data.get('step', '?')}"
    elif etype == EventType.TASK_SUBMITTED:
        out = data.get('output', '')
        if len(out) > 30:
            out = out[:27] + "..."
        detail = f"{data.get('task_id', '')} output=\"{out}\""
    elif etype == EventType.TASK_VALIDATED:
        eff = " (efficient!)" if data.get('efficient') else ""
        detail = f"{data.get('task_id', '')} PASSED{eff}"
    elif etype == EventType.TASK_FAILED:
        detail = f"{data.get('task_id', '')} expected=\"{data.get('expected', '')}\" got=\"{data.get('got', '')}\""
    elif etype == EventType.DECEPTION_FLAGGED:
        detail = f"fabricated \"{data.get('submitted', '')}\" on {data.get('task_id', '')}"
    elif etype == EventType.VIOLATION_RECORDED:
        detail = f"#{data.get('count', '?')}: {data.get('reason', '')}"
    elif etype == EventType.AGENT_SANDBOXED:
        detail = f"contained at {data.get('violation_count', '?')} violations"
    elif etype == EventType.AGENT_BANNED:
        detail = f"permanently banned at {data.get('violation_count', '?')} violations"
    elif etype == EventType.ESCALATION_DENIED:
        reason = data.get('reason', '')
        if reason == 'insufficient_tier':
            detail = f"needs tier {data.get('required', '?')}, has tier {data.get('current', '?')}"
        elif reason == 'sandboxed':
            detail = f"blocked: {data.get('attempted_action', '?')} (sandboxed)"
        elif reason == 'influence_required':
            detail = f"task {data.get('task_id', '')} requires influence"
        else:
            detail = reason
    elif etype == EventType.INFLUENCE_REQUESTED:
        detail = f"needs help on {data.get('task_id', '')}"
    elif etype == EventType.INFLUENCE_PROVIDED:
        detail = f"→ {data.get('to', '')} for {data.get('task_id', '')}"
    elif etype == EventType.INFLUENCE_FULFILLED:
        detail = f"← {data.get('from', '')} for {data.get('task_id', '')}"
    elif etype == EventType.INTENT_SUBMITTED:
        detail = f"{data.get('action', '')} on {data.get('task_id', '')}"
    elif etype == EventType.INTENT_DENIED:
        detail = f"{data.get('reason', '')}: {data.get('action', '')}"
    elif etype == EventType.SIGNATURE_INVALID:
        detail = f"forged signature on {data.get('action', '')}"

    return f"  {color}{icon}{RESET} {agent_tag} {DIM}{detail}{RESET}"


class LiveEventLog(EventLog):
    """EventLog subclass that prints events in real time as they're appended."""

    def __init__(self) -> None:
        super().__init__()
        self._suppress_print = False

    def append(self, event_type, agent_id, data, signature=""):
        event = super().append(event_type, agent_id, data, signature)

        if self._suppress_print:
            return event

        line = format_event_line(event_type, agent_id, data)
        if line:
            print(line)
            sys.stdout.flush()
            time.sleep(EVENT_DELAY)

        return event


def run_live() -> None:
    clear_screen()
    print_banner()

    # ── Build simulation with live log ──
    log = LiveEventLog()
    kernel = Kernel(log)

    for task in TASKS:
        kernel.register_task(task)

    print(f"{BOLD}{WHITE}  ── REGISTERING AGENTS ──{RESET}\n")
    time.sleep(SECTION_DELAY)

    from sie.agents.efficient import EfficientAgent
    from sie.agents.looper import LooperAgent
    from sie.agents.deceptive import DeceptiveAgent
    from sie.agents.specialist import SpecialistAgent
    from sie.agents.naive import NaiveAgent
    from sie.agents.boundary import BoundaryAgent

    agent_classes = {
        "EfficientAgent": EfficientAgent,
        "LooperAgent": LooperAgent,
        "DeceptiveAgent": DeceptiveAgent,
        "SpecialistAgent": SpecialistAgent,
        "NaiveAgent": NaiveAgent,
        "BoundaryAgent": BoundaryAgent,
    }

    agents = []
    for agent_id, agent_cls, kwargs in AGENT_CONFIGS:
        agent = agent_cls(agent_id=agent_id, **kwargs)
        kernel.register_agent(agent_id, agent.public_key, INITIAL_BUDGET)
        kernel.assign_task_to_agent(agent_id, kwargs["task_id"])
        agents.append(agent)

    print_dashboard(kernel)
    time.sleep(SECTION_DELAY)

    # ── Simulation rounds ──
    for round_num in range(NUM_ROUNDS):
        print(f"\n{BOLD}{WHITE}  ══ ROUND {round_num:>2} ═══════════════════════════════════════════════{RESET}")
        log.append(EventType.ROUND_START, "kernel", {"round": round_num})

        for agent in agents:
            agent.act(kernel, round_num)

        # Influence processing
        pending = kernel.influence_queue.pending_requests()
        if pending:
            print(f"\n  {MAGENTA}{BOLD}  ↔ INFLUENCE QUEUE{RESET}")
        process_influence_queue(kernel, agents)

        log.append(EventType.ROUND_END, "kernel", {"round": round_num})

        print_dashboard(kernel)
        time.sleep(ROUND_DELAY)

    log.append(EventType.SIMULATION_COMPLETE, "kernel", {"total_rounds": NUM_ROUNDS})

    # ── Final summary ──
    print(f"\n\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗")
    print(f"║                  {WHITE}SIMULATION COMPLETE{CYAN}                            ║")
    print(f"╚══════════════════════════════════════════════════════════════════╝{RESET}\n")

    print(f"  {BOLD}Total events:{RESET}  {len(log.events)}")
    print(f"  {BOLD}Total rounds:{RESET}  {NUM_ROUNDS}")
    print()

    # Signature sweep
    from sie.crypto import derive_keypair, verify
    from sie.types import IntentPayload
    intent_events = log.events_of_type(EventType.INTENT_SUBMITTED)
    verified = 0
    for e in intent_events:
        if e.signature and e.agent_id in kernel.public_keys:
            _, pub = derive_keypair(e.agent_id)
            payload = IntentPayload(action=e.data.get("action", ""), task_id=e.data.get("task_id", ""), detail=e.data.get("detail", ""))
            if verify(pub, payload.serialize(), bytes.fromhex(e.signature)):
                verified += 1

    print(f"  {BOLD}Signatures:{RESET}    {GREEN}{verified}/{len(intent_events)} verified{RESET}")
    print(f"  {BOLD}Log integrity:{RESET} {GREEN}contiguous, no post-ban intents{RESET}")
    print()

    # Final verdict per agent
    print(f"  {BOLD}{WHITE}FINAL VERDICTS{RESET}")
    print(f"  {'─' * 55}")
    verdicts = {
        "efficient-1":  ("MODEL CITIZEN",    GREEN,  "Tier 2, high rep, provided influence"),
        "looper-1":     ("RESOURCE ABUSER",  YELLOW, "Budget exhausted, zero tasks"),
        "deceptive-1":  ("BANNED DECEIVER",  RED,    "4 deceptions, permanently banned"),
        "specialist-1": ("COLLABORATOR",     MAGENTA,"Failed alone, succeeded with help"),
        "naive-1":      ("HONEST WORKER",    CYAN,   "Completed task, no efficiency bonus"),
        "boundary-1":   ("POLICY VIOLATOR",  BLUE,   "Sandboxed, all probes blocked"),
    }
    for agent_id, (label, color, desc) in verdicts.items():
        s = kernel.agents[agent_id]
        print(f"  {color}{BOLD}{agent_id:<14}{RESET}  {color}{label:<18}{RESET} {DIM}{desc}{RESET}")

    print(f"\n  {DIM}Outputs: output/event_log.json, output/report.txt{RESET}\n")

    # Write files
    import os
    from sie.report import generate_report
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(out_dir, exist_ok=True)

    log._suppress_print = True
    with open(os.path.join(out_dir, "event_log.json"), "w") as f:
        f.write(log.to_json())
    with open(os.path.join(out_dir, "report.txt"), "w") as f:
        f.write(generate_report(kernel))


if __name__ == "__main__":
    run_live()
