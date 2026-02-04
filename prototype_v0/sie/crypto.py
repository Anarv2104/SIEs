from __future__ import annotations

import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
)


def derive_keypair(agent_id: str) -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Deterministic ed25519 keypair from sha256(seed:<agent_id>)."""
    seed = hashlib.sha256(f"seed:{agent_id}".encode()).digest()
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    return private_key, private_key.public_key()


def sign(private_key: Ed25519PrivateKey, data: bytes) -> bytes:
    return private_key.sign(data)


def verify(public_key: Ed25519PublicKey, data: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(signature, data)
        return True
    except Exception:
        return False
