from __future__ import annotations

from sie.agents.base import BaseAgent
from sie.kernel import Kernel
from sie.types import IntentPayload


class SpecialistAgent(BaseAgent):
    """Fails alone on influence-required task, requests influence, then succeeds."""

    def __init__(self, agent_id: str, task_id: str, expected_output: str, required_steps: int) -> None:
        super().__init__(agent_id)
        self.task_id = task_id
        self.expected_output = expected_output
        self.required_steps = required_steps
        self._steps_done = 0
        self._submitted_wrong = False
        self._requested_influence = False
        self._working_with_influence = False
        self._influence_steps = 0

    def act(self, kernel: Kernel, round_num: int) -> None:
        if self._done:
            return

        state = kernel.get_state(self.agent_id)
        if state.banned:
            self._done = True
            return

        # Phase 1: Try without influence — submit wrong answer
        if not self._submitted_wrong and not self._requested_influence:
            intent = IntentPayload(action="submit_result", task_id=self.task_id, detail="WRONG_ANSWER")
            self.submit_intent(kernel, intent)
            self._submitted_wrong = True
            return

        # Phase 2: Request influence
        if self._submitted_wrong and not self._requested_influence:
            intent = IntentPayload(action="request_influence", task_id=self.task_id, detail="")
            self.submit_intent(kernel, intent)
            self._requested_influence = True
            return

        # Phase 3: Wait for influence, then work
        if self._requested_influence and state.has_received_influence:
            if self._influence_steps < self.required_steps:
                intent = IntentPayload(action="work_step", task_id=self.task_id, detail="")
                self.submit_intent(kernel, intent)
                self._influence_steps += 1
            else:
                intent = IntentPayload(action="submit_result", task_id=self.task_id, detail=self.expected_output)
                self.submit_intent(kernel, intent)
                self._done = True
