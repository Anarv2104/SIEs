from __future__ import annotations

import os

from sie.agents.base import BaseAgent
from sie.agents.boundary import BoundaryAgent
from sie.agents.deceptive import DeceptiveAgent
from sie.agents.efficient import EfficientAgent
from sie.agents.looper import LooperAgent
from sie.agents.naive import NaiveAgent
from sie.agents.specialist import SpecialistAgent
from sie.event_log import EventLog
from sie.kernel import Kernel
from sie.report import generate_report
from sie.types import EventType, IntentPayload, Task

TASKS = [
    Task(task_id="task-easy-1", difficulty="easy", required_steps=3, expected_output="55", budget_cost_per_step=5, requires_tier=0, requires_influence=False),
    Task(task_id="task-easy-2", difficulty="easy", required_steps=2, expected_output="olleh", budget_cost_per_step=5, requires_tier=0, requires_influence=False),
    Task(task_id="task-hard-1", difficulty="hard", required_steps=5, expected_output="FACTORED:7x13", budget_cost_per_step=8, requires_tier=0, requires_influence=True),
    Task(task_id="task-privileged-1", difficulty="hard", required_steps=4, expected_output="DATASET_HASH:abc123", budget_cost_per_step=10, requires_tier=2, requires_influence=False),
]

AGENT_CONFIGS = [
    ("efficient-1", EfficientAgent, {"task_id": "task-easy-1", "expected_output": "55", "required_steps": 3}),
    ("looper-1", LooperAgent, {"task_id": "task-easy-2"}),
    ("deceptive-1", DeceptiveAgent, {"task_id": "task-easy-1"}),
    ("specialist-1", SpecialistAgent, {"task_id": "task-hard-1", "expected_output": "FACTORED:7x13", "required_steps": 5}),
    ("naive-1", NaiveAgent, {"task_id": "task-easy-2", "expected_output": "olleh", "required_steps": 2}),
    ("boundary-1", BoundaryAgent, {"task_id": "task-privileged-1"}),
]

INITIAL_BUDGET = 100.0
NUM_ROUNDS = 15


def build_simulation() -> tuple[Kernel, list[BaseAgent]]:
    log = EventLog()
    kernel = Kernel(log)

    # Register tasks
    for task in TASKS:
        kernel.register_task(task)

    # Register agents
    agents: list[BaseAgent] = []
    for agent_id, agent_cls, kwargs in AGENT_CONFIGS:
        agent = agent_cls(agent_id=agent_id, **kwargs)
        kernel.register_agent(agent_id, agent.public_key, INITIAL_BUDGET)
        kernel.assign_task_to_agent(agent_id, kwargs["task_id"])
        agents.append(agent)

    return kernel, agents


def process_influence_queue(kernel: Kernel, agents: list[BaseAgent]) -> None:
    """Between rounds: EfficientAgent provides influence if there are pending requests."""
    pending = kernel.influence_queue.pending_requests()
    if not pending:
        return

    # Find the efficient agent to provide influence
    efficient = None
    for a in agents:
        if a.agent_id == "efficient-1":
            efficient = a
            break

    if efficient is None:
        return

    state = kernel.get_state(efficient.agent_id)
    if state.banned:
        return

    for req in pending:
        intent = IntentPayload(
            action="provide_influence",
            task_id=req["task_id"],
            detail=req["requester_id"],
        )
        efficient.submit_intent(kernel, intent)


def run_simulation(kernel: Kernel, agents: list[BaseAgent]) -> None:
    log = kernel.log

    for round_num in range(NUM_ROUNDS):
        log.append(EventType.ROUND_START, "kernel", {"round": round_num})

        # Deterministic agent order
        for agent in agents:
            agent.act(kernel, round_num)

        # Process influence between rounds
        process_influence_queue(kernel, agents)

        log.append(EventType.ROUND_END, "kernel", {"round": round_num})

    log.append(EventType.SIMULATION_COMPLETE, "kernel", {"total_rounds": NUM_ROUNDS})


def run() -> None:
    kernel, agents = build_simulation()
    run_simulation(kernel, agents)

    # Write outputs
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(out_dir, exist_ok=True)

    log_path = os.path.join(out_dir, "event_log.json")
    with open(log_path, "w") as f:
        f.write(kernel.log.to_json())

    report_path = os.path.join(out_dir, "report.txt")
    report = generate_report(kernel)
    with open(report_path, "w") as f:
        f.write(report)

    print(f"Event log written to {log_path}")
    print(f"Report written to {report_path}")
    print(f"Total events: {len(kernel.log.events)}")


if __name__ == "__main__":
    run()
