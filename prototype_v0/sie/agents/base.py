from __future__ import annotations

from abc import ABC, abstractmethod

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from sie.crypto import derive_keypair, sign
from sie.kernel import Kernel
from sie.types import IntentPayload


class BaseAgent(ABC):
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self._private_key: Ed25519PrivateKey
        self._public_key: Ed25519PublicKey
        self._private_key, self._public_key = derive_keypair(agent_id)
        self._done = False

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self._public_key

    def submit_intent(self, kernel: Kernel, intent: IntentPayload) -> bool:
        sig = sign(self._private_key, intent.serialize())
        return kernel.process_intent(self.agent_id, intent, sig)

    @abstractmethod
    def act(self, kernel: Kernel, round_num: int) -> None:
        """SPAR loop: sense→plan→act→reflect. Called once per round."""

    @property
    def done(self) -> bool:
        return self._done
