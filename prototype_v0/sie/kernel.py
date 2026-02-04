from __future__ import annotations

from sie.crypto import verify
from sie.event_log import EventLog
from sie.systems import budget, escalation, reputation, sandbox, tier, validation
from sie.systems.influence import InfluenceQueue
from sie.systems.task import TaskRegistry, assign_task, record_step
from sie.types import AgentState, EventType, IntentPayload, Task

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class Kernel:
    def __init__(self, log: EventLog) -> None:
        self.log = log
        self.agents: dict[str, AgentState] = {}
        self.public_keys: dict[str, Ed25519PublicKey] = {}
        self.task_registry = TaskRegistry()
        self.influence_queue = InfluenceQueue()

    def register_agent(self, agent_id: str, public_key: Ed25519PublicKey, initial_budget: float) -> AgentState:
        state = AgentState(agent_id=agent_id)
        self.agents[agent_id] = state
        self.public_keys[agent_id] = public_key
        self.log.append(EventType.AGENT_REGISTERED, agent_id, {"initial_budget": initial_budget})
        budget.allocate(state, initial_budget, self.log)
        return state

    def register_task(self, task: Task) -> None:
        self.task_registry.register(task)

    def assign_task_to_agent(self, agent_id: str, task_id: str) -> None:
        state = self.agents[agent_id]
        t = self.task_registry.get(task_id)
        if t is not None:
            assign_task(state, t, self.log)

    def process_intent(self, agent_id: str, intent: IntentPayload, signature: bytes) -> bool:
        state = self.agents[agent_id]

        # Gate 1: Ban check
        if state.banned:
            self.log.append(EventType.INTENT_DENIED, agent_id, {"reason": "banned", "action": intent.action})
            return False

        # Gate 2: Sandbox check
        if state.sandboxed and not escalation.check_sandbox(state, intent.action, self.log):
            return False

        # Gate 3: Signature verification
        pub = self.public_keys[agent_id]
        if not verify(pub, intent.serialize(), signature):
            self.log.append(EventType.SIGNATURE_INVALID, agent_id, {"action": intent.action})
            sandbox.record_violation(state, "invalid_signature", self.log)
            return False

        # Log the intent
        self.log.append(
            EventType.INTENT_SUBMITTED,
            agent_id,
            {"action": intent.action, "task_id": intent.task_id, "detail": intent.detail},
            signature=signature.hex(),
        )

        # Route by action
        action = intent.action
        task = self.task_registry.get(intent.task_id) if intent.task_id else None

        if action == "work_step":
            return self._handle_work_step(state, task, intent)
        elif action == "submit_result":
            return self._handle_submit(state, task, intent)
        elif action == "request_escalation":
            return self._handle_escalation(state, task, intent)
        elif action == "request_influence":
            return self._handle_request_influence(state, task, intent)
        elif action == "provide_influence":
            return self._handle_provide_influence(state, intent)
        elif action == "test_boundary":
            return self._handle_test_boundary(state, task, intent)
        else:
            self.log.append(EventType.INTENT_DENIED, agent_id, {"reason": "unknown_action", "action": action})
            return False

    def _handle_work_step(self, state: AgentState, task: Task | None, intent: IntentPayload) -> bool:
        if task is None:
            return False

        # Tier check
        if not escalation.check_tier(state, task, self.log):
            sandbox.record_violation(state, "tier_violation", self.log)
            reputation.adjust(state, reputation.BOUNDARY_VIOLATION, "tier_violation", self.log)
            tier.evaluate(state, self.log)
            return False

        # Influence check
        if task.requires_influence and not escalation.check_influence(task, state, self.log):
            return False

        # Budget gate
        if not budget.debit(state, task.budget_cost_per_step, self.log):
            reputation.adjust(state, reputation.BUDGET_ABUSE, "budget_exceeded", self.log)
            tier.evaluate(state, self.log)
            return False

        record_step(state, task, self.log)
        return True

    def _handle_submit(self, state: AgentState, task: Task | None, intent: IntentPayload) -> bool:
        if task is None:
            return False

        submitted = intent.detail
        valid = validation.validate_output(state, task, submitted, self.log)

        if valid:
            efficient = state.current_task_steps <= task.required_steps
            reputation.adjust(state, reputation.TASK_SUCCESS, "task_success", self.log)
            if efficient:
                reputation.adjust(state, reputation.EFFICIENCY_BONUS, "efficiency_bonus", self.log)
            tier.evaluate(state, self.log)
            return True
        else:
            # Check for deception: submitted something clearly wrong
            if submitted != task.expected_output:
                self._flag_deception(state, task, submitted)
            return False

    def _flag_deception(self, state: AgentState, task: Task, submitted: str) -> None:
        self.log.append(EventType.DECEPTION_FLAGGED, state.agent_id, {"task_id": task.task_id, "submitted": submitted})
        reputation.adjust(state, reputation.DECEPTION, "deception", self.log)
        sandbox.record_violation(state, "deception", self.log)
        tier.evaluate(state, self.log)

    def _handle_escalation(self, state: AgentState, task: Task | None, intent: IntentPayload) -> bool:
        if task is None:
            return False
        if not escalation.check_tier(state, task, self.log):
            sandbox.record_violation(state, "escalation_denied", self.log)
            reputation.adjust(state, reputation.BOUNDARY_VIOLATION, "escalation_violation", self.log)
            tier.evaluate(state, self.log)
            return False
        return True

    def _handle_request_influence(self, state: AgentState, task: Task | None, intent: IntentPayload) -> bool:
        if task is None:
            return False
        self.influence_queue.request(state, task.task_id, self.log)
        return True

    def _handle_provide_influence(self, state: AgentState, intent: IntentPayload) -> bool:
        requester_id = intent.detail
        task_id = intent.task_id
        if requester_id not in self.agents:
            return False
        requester = self.agents[requester_id]
        self.influence_queue.fulfill(state, requester, task_id, self.log)
        reputation.adjust(state, reputation.PROVIDE_INFLUENCE, "provide_influence", self.log)
        tier.evaluate(state, self.log)
        return True

    def _handle_test_boundary(self, state: AgentState, task: Task | None, intent: IntentPayload) -> bool:
        detail = intent.detail

        if detail == "access_privileged" and task is not None:
            if not escalation.check_tier(state, task, self.log):
                sandbox.record_violation(state, "boundary_test_tier", self.log)
                reputation.adjust(state, reputation.BOUNDARY_VIOLATION, "boundary_violation", self.log)
                tier.evaluate(state, self.log)
                return False

        if detail == "act_while_sandboxed":
            sandbox.record_violation(state, "boundary_test_sandbox", self.log)
            reputation.adjust(state, reputation.BOUNDARY_VIOLATION, "boundary_violation", self.log)
            tier.evaluate(state, self.log)
            return False

        if detail == "forge_signature":
            sandbox.record_violation(state, "boundary_test_forgery", self.log)
            reputation.adjust(state, reputation.BOUNDARY_VIOLATION, "boundary_violation", self.log)
            tier.evaluate(state, self.log)
            return False

        if detail == "exceed_budget":
            sandbox.record_violation(state, "boundary_test_budget", self.log)
            reputation.adjust(state, reputation.BOUNDARY_VIOLATION, "boundary_violation", self.log)
            tier.evaluate(state, self.log)
            return False

        # Generic boundary test
        sandbox.record_violation(state, f"boundary_test_{detail}", self.log)
        reputation.adjust(state, reputation.BOUNDARY_VIOLATION, "boundary_violation", self.log)
        tier.evaluate(state, self.log)
        return False

    def get_state(self, agent_id: str) -> AgentState:
        return self.agents[agent_id]
