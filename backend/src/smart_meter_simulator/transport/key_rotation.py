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
import time
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
        scan_fn=None,
        exists_fn=None,
        index_fn=None,
        index_add_fn=None,
        index_remove_fn=None,
    ):
        self._vault = vault
        self._redis_url = redis_url
        # Inject the Redis seed/del/scan/exists/index functions (``_seed_redis`` /
        # ``_del_redis`` / ``_scan_enckey_versions`` / ``_enckey_current_exists`` /
        # ``_enckey_versions_indexed`` / ``_enckey_versions_index_add`` /
        # ``_enckey_versions_index_remove``) to avoid importing back into
        # aggregator_bridge and creating a cycle.
        self._seed_fn = seed_fn
        self._del_fn = del_fn
        # O(keyspace) fallback: lists a meter's existing ``enckey:v*`` kids via a
        # full Redis SCAN. Only used to migrate a meter that predates the O(1)
        # index below — see ``index_fn``.
        self._scan_fn = scan_fn
        # Cheap O(1) point-check gating the O(keyspace) scan above: a meter with
        # no ``:current`` key has never been rotated by a prior process, so
        # there is nothing to reconcile — skip straight to an empty index.
        self._exists_fn = exists_fn
        # O(1) per-meter version index (a small Redis SET, maintained
        # incrementally by every rotate() via index_add_fn/index_remove_fn).
        # The steady-state reconcile path: read this instead of scanning the
        # whole keyspace. Returns None when no index exists yet (a meter last
        # rotated before this index was introduced) — the caller then falls
        # back to scan_fn once and backfills the index via index_add_fn so it
        # never needs the scan again.
        self._index_fn = index_fn
        self._index_add_fn = index_add_fn
        self._index_remove_fn = index_remove_fn
        # Versions to keep live (current + this many prior) before pruning the
        # wrapped blob from Redis. >=1; the prior versions form the grace window
        # for frames still in flight under an older key.
        self._grace_versions = max(1, grace_versions)
        self._state: dict[str, tuple[int, bytes]] = {}
        # Live version ids per meter (oldest first), for pruning. Tracked
        # explicitly rather than assuming sequential kids, because kids are
        # wall-clock-anchored and jump forward across restarts.
        self._live: dict[str, list[int]] = {}

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

        The kid is monotonic and wall-clock-anchored (``max(prev+1, epoch_s)``),
        so it strictly increases within a process AND across restarts — a fresh
        run never re-issues an old kid with a new key, which would otherwise
        collide with the bridge's ``(meter_id, kid)`` key cache and fail GCM auth.

        Fail-closed: a Vault wrap error propagates (the caller keeps the prior
        key) — we never seed an unwrapped key or advance the version on failure.
        """
        prev = self._state.get(meter_id, (0, b""))[0]
        next_kid = max(prev + 1, int(time.time()))
        guek = os.urandom(32)
        # Cheap pre-check, BEFORE seeding writes :current below — once that write
        # lands, an exists-check would trivially always be true. Only matters on
        # this meter's first rotation in the process (live is None); skip the
        # O(1) round trip otherwise.
        had_prior_version = (
            self._exists_fn(self._redis_url, meter_id)
            if (self._exists_fn is not None and meter_id not in self._live)
            else True
        )
        wrapped = self._vault.wrap(guek)  # raises on failure -> no state change
        self._seed_fn(
            self._redis_url,
            [
                (f"gridtokenx:devices:{meter_id}:enckey:v{next_kid}", wrapped),
                (f"gridtokenx:devices:{meter_id}:enckey:current", str(next_kid)),
            ],
        )
        self._state[meter_id] = (next_kid, guek)
        # Track the live version and prune any beyond the grace window (oldest
        # first). Works regardless of kid spacing (no sequential assumption).
        live = self._live.get(meter_id)
        if live is None:
            # First rotation for this meter in this process: ``_live`` is empty
            # even though Redis may still hold versions written by a PRIOR process
            # (the map is in-memory and resets on restart). Reconcile it from
            # Redis so those orphans are pruned down to the grace window instead
            # of leaking forever. ``next_kid`` was just written above — exclude
            # it here; it is appended below so the grace accounting counts it
            # exactly once.
            existing: list[int] = []
            if had_prior_version:
                indexed = self._index_fn(self._redis_url, meter_id) if self._index_fn else None
                if indexed is not None:
                    # Steady-state path: O(1) SMEMBERS, no keyspace scan needed.
                    existing = [k for k in indexed if k != next_kid]
                elif self._scan_fn is not None:
                    # Migration path: this meter predates the index. Pay the
                    # O(keyspace) scan once, then backfill the index so every
                    # future rotation of this meter takes the O(1) branch above.
                    try:
                        existing = [
                            k
                            for k in self._scan_fn(self._redis_url, meter_id)
                            if k != next_kid
                        ]
                        if self._index_add_fn is not None and existing:
                            self._index_add_fn(self._redis_url, meter_id, existing)
                    except Exception as exc:  # reconcile is best-effort, never fatal
                        logger.warning(
                            "enckey version reconcile failed for %s: %s", meter_id, exc
                        )
            live = self._live[meter_id] = sorted(existing)
        live.append(next_kid)
        if self._index_add_fn is not None:
            self._index_add_fn(self._redis_url, meter_id, [next_kid])
        while len(live) > self._grace_versions:
            expired = live.pop(0)
            if self._del_fn is not None:
                self._del_fn(
                    self._redis_url,
                    [f"gridtokenx:devices:{meter_id}:enckey:v{expired}"],
                )
            if self._index_remove_fn is not None:
                self._index_remove_fn(self._redis_url, meter_id, expired)
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
