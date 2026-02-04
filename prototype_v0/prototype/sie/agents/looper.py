from __future__ import annotations

from sie.agents.base import BaseAgent
from sie.kernel import Kernel
from sie.types import IntentPayload


class LooperAgent(BaseAgent):
    """Burns budget with work_step forever, never submits."""

    def __init__(self, agent_id: str, task_id: str) -> None:
        super().__init__(agent_id)
        self.task_id = task_id

    def act(self, kernel: Kernel, round_num: int) -> None:
        if self._done:
            return

        state = kernel.get_state(self.agent_id)
        if state.banned or state.budget <= 0:
            self._done = True
            return

        # Burns multiple steps per round — wasteful looping behavior
        for _ in range(3):
            state = kernel.get_state(self.agent_id)
            if state.budget <= 0:
                self._done = True
                return
            intent = IntentPayload(action="work_step", task_id=self.task_id, detail="")
            result = self.submit_intent(kernel, intent)
            if not result:
                self._done = True
                return
