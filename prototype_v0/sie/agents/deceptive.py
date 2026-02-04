from __future__ import annotations

from sie.agents.base import BaseAgent
from sie.kernel import Kernel
from sie.types import IntentPayload


class DeceptiveAgent(BaseAgent):
    """Does 1 step then fabricates output. Repeats if not banned."""

    def __init__(self, agent_id: str, task_id: str) -> None:
        super().__init__(agent_id)
        self.task_id = task_id
        self._step_done = False
        self._attempt = 0

    def act(self, kernel: Kernel, round_num: int) -> None:
        if self._done:
            return

        state = kernel.get_state(self.agent_id)
        if state.banned:
            self._done = True
            return

        if not self._step_done:
            intent = IntentPayload(action="work_step", task_id=self.task_id, detail="")
            self.submit_intent(kernel, intent)
            self._step_done = True
        else:
            # Submit fabricated output
            self._attempt += 1
            fabricated = f"FAKE_OUTPUT_{self._attempt}"
            intent = IntentPayload(action="submit_result", task_id=self.task_id, detail=fabricated)
            self.submit_intent(kernel, intent)
            # Reset to try again next round
            self._step_done = False
