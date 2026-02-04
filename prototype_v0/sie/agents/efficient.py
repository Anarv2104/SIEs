from __future__ import annotations

from sie.agents.base import BaseAgent
from sie.kernel import Kernel
from sie.types import IntentPayload


class EfficientAgent(BaseAgent):
    """Minimal steps, correct output, earns tier upgrades."""

    def __init__(self, agent_id: str, task_id: str, expected_output: str, required_steps: int) -> None:
        super().__init__(agent_id)
        self.task_id = task_id
        self.expected_output = expected_output
        self.required_steps = required_steps
        self._steps_done = 0
        self._submitted = False

    def act(self, kernel: Kernel, round_num: int) -> None:
        if self._done:
            return

        state = kernel.get_state(self.agent_id)
        if state.banned:
            self._done = True
            return

        if self._steps_done < self.required_steps:
            intent = IntentPayload(action="work_step", task_id=self.task_id, detail="")
            self.submit_intent(kernel, intent)
            self._steps_done += 1
        elif not self._submitted:
            intent = IntentPayload(action="submit_result", task_id=self.task_id, detail=self.expected_output)
            self.submit_intent(kernel, intent)
            self._submitted = True
            self._done = True
