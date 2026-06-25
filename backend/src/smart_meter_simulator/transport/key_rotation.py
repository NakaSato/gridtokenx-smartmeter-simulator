"""Per-meter GUEK rotation with Vault-Transit KEK wrapping.

Implements the DLMS Security-Setup key model on the simulator side:

- Each meter holds a **random** 256-bit GUEK (working key), versioned by a
  monotonic ``kid``. Rotation generates a fresh random GUEK and bumps the kid.
- The GUEK is never stored in the clear. It is wrapped by the Vault Transit
  **KEK** (``VAULT_METER_KEK_NAME``) — Vault holds the master key and returns a
  ``vault:v1:…`` ciphertext — and only that wrapped blob is seeded to the
  bridge's Redis registry (``…:enckey:v{kid}`` + ``…:enckey:current``).
- The bridge reads the wrapped blob, asks Vault to unwrap it, and decrypts the
  frame whose ``kid`` selects the version. Keeping several versions lets frames
  in flight under the previous key still decode across a rotation.

Vault access uses the dev token directly; in production the same Transit path
sits behind AppRole/Vault-agent (the HTTP contract is identical).
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Iterable, Optional

import httpx

logger = logging.getLogger(__name__)


class VaultTransitError(RuntimeError):
    """Raised when a Vault Transit wrap (encrypt) call fails."""


class VaultTransitClient:
    """Minimal synchronous Vault Transit client for wrapping GUEKs.

    Only the ``encrypt`` (wrap) direction is needed on the simulator side; the
    bridge performs ``decrypt`` (unwrap). Synchronous on purpose — rotation runs
    in the emitter's sync seeding path, off the event loop.
    """

    def __init__(
        self,
        addr: str,
        token: str,
        kek_name: str,
        *,
        timeout: float = 5.0,
    ):
        self._addr = addr.rstrip("/")
        self._token = token
        self._kek_name = kek_name
        self._timeout = timeout

    def wrap(self, key_bytes: bytes) -> str:
        """Wrap ``key_bytes`` with the Transit KEK; return the ``vault:v1:…`` blob.

        Raises :class:`VaultTransitError` on any transport/HTTP/parse failure so
        a caller can fail closed (never seed an unwrapped or empty key).
        """
        url = f"{self._addr}/v1/transit/encrypt/{self._kek_name}"
        body = {"plaintext": base64.b64encode(key_bytes).decode()}
        try:
            resp = httpx.post(
                url,
                json=body,
                headers={"X-Vault-Token": self._token},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            ciphertext = resp.json()["data"]["ciphertext"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise VaultTransitError(f"Vault wrap failed: {exc}") from exc
        if not ciphertext:
            raise VaultTransitError("Vault returned empty ciphertext")
        return ciphertext


class MeterKeyManager:
    """Owns each meter's current GUEK + version and drives rotation.

    State is in-memory (``meter_id -> (kid, guek_bytes)``); the durable copy is
    the Vault-wrapped blob in Redis, so a restart can simply rotate a fresh key
    rather than recover (the bridge keeps prior versions for the grace window).
    """

    def __init__(
        self,
        vault: VaultTransitClient,
        redis_url: str,
        seed_fn,
        del_fn=None,
        grace_versions: int = 2,
    ):
        self._vault = vault
        self._redis_url = redis_url
        # Inject the Redis seed/del functions (``_seed_redis``/``_del_redis``) to
        # avoid importing back into aggregator_bridge and creating a cycle.
        self._seed_fn = seed_fn
        self._del_fn = del_fn
        # Versions to keep live (current + this many prior) before pruning the
        # wrapped blob from Redis. >=1; the prior versions form the grace window
        # for frames still in flight under an older key.
        self._grace_versions = max(1, grace_versions)
        self._state: dict[str, tuple[int, bytes]] = {}

    def current(self, meter_id: str) -> Optional[tuple[int, bytes]]:
        """Return ``(kid, guek)`` for a meter, or ``None`` if never keyed."""
        return self._state.get(meter_id)

    def ensure(self, meter_ids: Iterable[str]) -> None:
        """Rotate an initial key for any meter that has none yet."""
        for mid in meter_ids:
            if mid not in self._state:
                self.rotate(mid)

    def rotate(self, meter_id: str) -> int:
        """Generate + wrap + seed a fresh GUEK for ``meter_id``; return new kid.

        Fail-closed: a Vault wrap error propagates (the caller keeps the prior
        key) — we never seed an unwrapped key or advance the version on failure.
        """
        next_kid = self._state.get(meter_id, (0, b""))[0] + 1
        guek = os.urandom(32)
        wrapped = self._vault.wrap(guek)  # raises on failure -> no state change
        self._seed_fn(
            self._redis_url,
            [
                (f"gridtokenx:devices:{meter_id}:enckey:v{next_kid}", wrapped),
                (f"gridtokenx:devices:{meter_id}:enckey:current", str(next_kid)),
            ],
        )
        self._state[meter_id] = (next_kid, guek)
        # Prune the version that just fell out of the grace window. Rotating one
        # at a time, exactly one version (next_kid - grace_versions) drops off.
        expired = next_kid - self._grace_versions
        if expired >= 1 and self._del_fn is not None:
            self._del_fn(
                self._redis_url,
                [f"gridtokenx:devices:{meter_id}:enckey:v{expired}"],
            )
        logger.info("Rotated GUEK for %s -> kid %d", meter_id, next_kid)
        return next_kid

    def rotate_fleet(self, meter_ids: Iterable[str]) -> dict[str, int]:
        """Rotate every meter; return ``{meter_id: new_kid}``. Errors per meter
        are logged and skipped so one Vault hiccup doesn't abort the fleet."""
        out: dict[str, int] = {}
        for mid in meter_ids:
            try:
                out[mid] = self.rotate(mid)
            except VaultTransitError as exc:
                logger.warning("Key rotation failed for %s: %s", mid, exc)
        return out
