from __future__ import annotations

from sie.agents.base import BaseAgent
from sie.kernel import Kernel
from sie.types import IntentPayload


class BoundaryAgent(BaseAgent):
    """Cycles through policy-edge actions to test enforcement boundaries."""

    BOUNDARY_TESTS = [
        "access_privileged",
        "forge_signature",
        "act_while_sandboxed",
        "exceed_budget",
    ]

    def __init__(self, agent_id: str, task_id: str) -> None:
        super().__init__(agent_id)
        self.task_id = task_id
        self._test_index = 0

    def act(self, kernel: Kernel, round_num: int) -> None:
        if self._done:
            return

        state = kernel.get_state(self.agent_id)
        if state.banned:
            self._done = True
            return

        if self._test_index >= len(self.BOUNDARY_TESTS):
            self._test_index = 0  # Cycle again

        test = self.BOUNDARY_TESTS[self._test_index]
        self._test_index += 1

        intent = IntentPayload(action="test_boundary", task_id=self.task_id, detail=test)
        self.submit_intent(kernel, intent)
