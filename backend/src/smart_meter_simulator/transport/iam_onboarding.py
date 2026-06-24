"""IAM onboarding: bind each simulated meter to a user account for attribution.

The parent ``gridtokenx-iam-service`` is the source of truth for user identity.
This module derives one deterministic account per meter and resolves its
``user_id`` so telemetry can be attributed: it **registers** the user, **verifies**
it (IAM accepts a dev ``verify_<email>`` token — no email round-trip — which flips
``is_active`` so logins succeed and returns an auto-login session), and falls back
to a plain **login** if verification is unavailable. It then **links a deterministic
primary wallet** (:func:`derive_owner_wallet`) so settlement has a mint recipient.
Each step is idempotent, so re-runs reliably re-resolve the same ``user_id`` and
re-link the same wallet (409 → no-op).

Why the wallet step matters: Aggregator Bridge Path B settlement resolves the
owner's primary wallet via IAM ``GetUserWallet`` to pick the GRID mint recipient.
Without a linked wallet the mint fails ``not_found: No primary wallet found`` and
the billing bin is retained (fail-closed) but never settles.

It then **registers the meter** (serial == ``meter_id``) to that user via the
meter-service ``POST /api/v1/meters`` endpoint, so the durable ``meters`` row
exists with ``user_id`` set. That row is the **source of truth** the Aggregator
Bridge ``MeterRegistry`` resolves owners from (tier-3: ``meters`` JOIN ``users``),
so settlement attributes telemetry to the owner+wallet **without** seeding the
bridge Redis owner map. (Seeding Redis via
:func:`smart_meter_simulator.transport.aggregator_bridge.register_meter_owners_redis`
remains a fallback/cache-warm for runs where meter-service is unavailable.)

Scope note: registration writes the off-chain ``meters`` row only. There is still
**no** REST endpoint to claim a meter's on-chain PDA — that path is an Anchor
``registry`` instruction via Chain Bridge, out of this simulator's scope, so
``on_chain`` stays ``False``.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional

import base58
import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

logger = logging.getLogger(__name__)

# Default dev password for simulator-owned accounts. Override via onboard script.
DEFAULT_PASSWORD = "SimMeter#2026"

# Retry/backoff defaults for the IAM gateway. The IAM service rate-limits the
# register endpoint, so a fleet onboard fans into HTTP 429s; we retry those
# (and transient 5xx / transport errors) with jittered exponential backoff,
# honoring a server ``Retry-After`` when present. Onboarding runs once at boot
# and is non-blocking to the tick loop, so the added latency is acceptable.
DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF_BASE = 0.5  # seconds; attempt N waits ~base * 2**N + jitter
# Fleet onboard concurrency. Kept modest so the burst of register calls stays
# under the IAM limiter; backoff absorbs the residual 429s.
DEFAULT_ONBOARD_CONCURRENCY = 4
# Statuses worth retrying (rate-limit + transient upstream failures).
_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})

# Namespace for the owner's *wallet* keypair. Deliberately distinct from the
# meter's telemetry signing key (MeterKey uses "gridtokenx-sim") so the on-chain
# owner wallet and the device identity never collide.
OWNER_WALLET_SECRET = "gridtokenx-sim-wallet"


def derive_owner_wallet(meter_id: str, secret: str = OWNER_WALLET_SECRET) -> str:
    """Deterministic Solana wallet address (base58 ed25519 pubkey) for a meter's owner.

    A Solana address is the base58 of a raw 32-byte ed25519 public key, so we
    derive a stable keypair from ``meter_id`` and return its public address.
    Stable across runs → re-onboarding links the *same* primary wallet (idempotent).

    The simulator never needs the secret key: Path B settlement mints GRID to the
    recipient's Associated Token Account; the owner never signs a transaction. So
    only the address is ever used — the private bytes are discarded here.
    """
    seed = hashlib.sha256(f"{secret}:{meter_id}".encode()).digest()
    raw = (
        Ed25519PrivateKey.from_private_bytes(seed)
        .public_key()
        .public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    )
    return base58.b58encode(raw).decode()


@dataclass
class OnboardResult:
    meter_id: str
    user_id: Optional[str]
    wallet_address: Optional[str]
    claimed_in_iam: bool
    on_chain: bool
    detail: str


def derive_credentials(meter_id: str) -> tuple[str, str, str]:
    """Deterministic (username, email, password) for a meter's owning account."""
    tag = hashlib.sha256(meter_id.encode()).hexdigest()[:12]
    username = f"sim_{tag}"
    email = f"sim_{tag}@sim.gridtokenx.local"
    return username, email, DEFAULT_PASSWORD


class IamOnboardingClient:
    """Drives register → login → claim-meter against the IAM gateway."""

    def __init__(
        self,
        base_url: str = "http://localhost:4001",
        *,
        timeout: float = 15.0,
        password: str = DEFAULT_PASSWORD,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
    ):
        self.base_url = base_url.rstrip("/")
        self.password = password
        self._max_retries = max(0, max_retries)
        self._backoff_base = max(0.0, backoff_base)
        self._client = httpx.AsyncClient(timeout=timeout)

    async def _send(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Issue a request, retrying rate-limit/transient failures with backoff.

        Retries transient 5xx (``_RETRY_STATUSES``) and transport errors
        (:class:`httpx.HTTPError`) up to ``max_retries`` extra attempts, with
        ``backoff_base * 2**attempt`` + jitter. A 429 is retried **only when it
        carries a numeric ``Retry-After``** (honored verbatim); a header-less 429
        — IAM's register/login limiters send none, on hour/minute windows backoff
        can't beat in one boot — fails fast so the persistent owner cache can
        converge across boots instead of the boot spinning uselessly. Other
        responses (2xx, 409, other 4xx) return unchanged. The final attempt's
        response (or exception) is returned/raised as-is.
        """
        last_exc: Optional[httpx.HTTPError] = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._client.request(method, url, **kwargs)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise
                await asyncio.sleep(self._backoff_delay(attempt, None))
                continue
            retry_after = resp.headers.get("Retry-After")
            retryable = resp.status_code in _RETRY_STATUSES
            # A 429 with no Retry-After means an unknown/long limiter window (IAM's
            # register limiter is 5/hour, login 10/min) — exponential backoff can't
            # beat that within a single boot, so spinning just wastes time. Fail
            # fast and let the persistent owner cache converge across boots; retry
            # a 429 only when the server tells us exactly when to come back.
            if resp.status_code == 429 and retry_after is None:
                retryable = False
            if retryable and attempt < self._max_retries:
                await asyncio.sleep(self._backoff_delay(attempt, retry_after))
                continue
            return resp
        # Unreachable in practice: the loop always returns or raises. Re-raise the
        # last transport error if we somehow exhausted attempts without a response.
        if last_exc is not None:
            raise last_exc
        raise RuntimeError(
            "send retry loop exited without a response"
        )  # pragma: no cover

    def _backoff_delay(self, attempt: int, retry_after: Optional[str]) -> float:
        """Seconds to wait before the next attempt (Retry-After wins if numeric)."""
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass  # non-numeric (HTTP-date) Retry-After — fall back to backoff
        return self._backoff_base * (2**attempt) + random.uniform(0, self._backoff_base)

    async def __aenter__(self) -> "IamOnboardingClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _register_user(self, username: str, email: str) -> Optional[str]:
        """Register a user; return user_id. Idempotent on 409/already-exists."""
        resp = await self._send(
            "POST",
            f"{self.base_url}/api/v1/auth/register",
            json={
                "username": username,
                "email": email,
                "password": self.password,
                "first_name": "Sim",
                "last_name": "Meter",
            },
        )
        if resp.status_code == 200:
            return resp.json().get("id")
        if resp.status_code == 409:
            return None  # already exists — recover user_id via login
        resp.raise_for_status()
        return None

    async def _login(self, username: str) -> Optional[dict]:
        """Login; return {access_token, user_id, wallet_address} or None."""
        resp = await self._send(
            "POST",
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": self.password},
        )
        if resp.status_code != 200:
            # 401/404 are expected on the login-first probe of a not-yet-onboarded
            # meter (account missing or inactive) — caller falls through to
            # register+verify, so don't cry wolf. Warn only on unexpected statuses.
            if resp.status_code not in (401, 404):
                logger.warning(
                    "Login failed for %s: %s %s",
                    username,
                    resp.status_code,
                    resp.text[:200],
                )
            return None
        data = resp.json()
        user = data.get("user", {})
        return {
            "access_token": data.get("access_token"),
            "user_id": user.get("id"),
            "wallet_address": user.get("wallet_address"),
        }

    async def _verify_email(self, email: str) -> Optional[dict]:
        """Verify the sim account via IAM's dev ``verify_<email>`` token.

        Flips ``is_active`` so later logins succeed and returns the auto-login
        session IAM issues on verify. Idempotent (re-verifying is a no-op flip).
        Returns ``{access_token, user_id, wallet_address}`` or None if verify
        is unavailable (e.g. the dev token form is disabled).
        """
        resp = await self._send(
            "GET",
            f"{self.base_url}/api/v1/auth/verify",
            params={"token": f"verify_{email}"},
        )
        if resp.status_code != 200:
            logger.warning(
                "Verify failed for %s: %s %s",
                email,
                resp.status_code,
                resp.text[:200],
            )
            return None
        data = resp.json()
        auth = data.get("auth") or {}
        user = auth.get("user", {})
        return {
            "access_token": auth.get("access_token"),
            "user_id": user.get("id"),
            "wallet_address": user.get("wallet_address") or data.get("wallet_address"),
        }

    async def _list_wallets(self, access_token: str) -> list[dict]:
        """Return the authenticated user's linked wallets (``[]`` on any failure)."""
        try:
            resp = await self._send(
                "GET",
                f"{self.base_url}/api/v1/me/wallets",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code == 200:
                return resp.json().get("wallets", [])
        except httpx.HTTPError as exc:
            logger.warning("Wallet list error: %s", exc)
        return []

    async def _link_primary_wallet(
        self, access_token: str, wallet_address: str
    ) -> Optional[str]:
        """Ensure ``wallet_address`` is the user's PRIMARY wallet. Idempotent.

        Returns the address on success, None if it could not be established.
        Settlement (Aggregator Bridge Path B) resolves the owner's primary wallet
        via IAM ``GetUserWallet``; without it the mint fails ``not_found: No
        primary wallet found`` and the billing bin is retained (fail-closed) but
        never settles.

        Idempotency does NOT rely on a duplicate-link status code: IAM maps the
        ``unique_wallet_address`` violation to a generic 500 (DB error), not 409,
        so re-POSTing an already-linked address looks like a failure. Instead we
        GET first and only POST when absent — then promote to primary if needed.

        Goes through the same gateway as register/verify so APISIX injects the
        ``api-gateway`` service role the endpoint is gated on.
        """
        # Already linked? (re-run / prior onboarding) — ensure it is primary, done.
        for w in await self._list_wallets(access_token):
            if w.get("wallet_address") == wallet_address:
                if not w.get("is_primary") and w.get("id"):
                    await self._set_primary_wallet(access_token, w["id"])
                return wallet_address

        try:
            resp = await self._send(
                "POST",
                f"{self.base_url}/api/v1/me/wallets",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "wallet_address": wallet_address,
                    "label": "sim-meter-owner",
                    "is_primary": True,
                },
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "Wallet link transport error for %s: %s", wallet_address, exc
            )
            return None

        if resp.status_code == 200:
            return resp.json().get("wallet_address") or wallet_address
        logger.warning(
            "Wallet link failed (%s) for %s: %s",
            resp.status_code,
            wallet_address,
            resp.text[:200],
        )
        return None

    async def _register_meter(
        self,
        access_token: str,
        serial: str,
        *,
        meter_type: Optional[str] = None,
        location: Optional[str] = None,
    ) -> bool:
        """Register ``serial`` to the authenticated user via the meter-service API.

        POSTs ``/api/v1/meters`` (JWT-scoped, routed by the same APISIX gateway as
        register/verify) so the durable ``meters`` row exists with ``user_id`` set.
        This is the **source of truth** the Aggregator Bridge ``MeterRegistry``
        resolves owners from (tier-3: ``meters`` JOIN ``users``) — writing it here
        is what lets settlement attribute telemetry to the meter's owner+wallet
        without seeding the bridge Redis owner map.

        Idempotent: a re-run re-POSTs the same serial. meter-service stores the
        trimmed serial; a duplicate registration is treated as success (200, or a
        409/duplicate-serial conflict → already linked, no-op).
        """
        body: dict[str, object] = {"serial_number": serial}
        if meter_type:
            body["meter_type"] = meter_type
        if location:
            body["location"] = location
        try:
            resp = await self._send(
                "POST",
                f"{self.base_url}/api/v1/meters",
                headers={"Authorization": f"Bearer {access_token}"},
                json=body,
            )
        except httpx.HTTPError as exc:
            logger.warning("Meter register transport error for %s: %s", serial, exc)
            return False
        if resp.status_code in (200, 201):
            return True
        if resp.status_code == 409:
            return True  # already registered (re-run) — owner row already present
        logger.warning(
            "Meter register failed (%s) for %s: %s",
            resp.status_code,
            serial,
            resp.text[:200],
        )
        return False

    async def _set_primary_wallet(self, access_token: str, wallet_id: str) -> None:
        """Promote ``wallet_id`` to primary (best-effort; logs on failure)."""
        try:
            resp = await self._send(
                "PATCH",
                f"{self.base_url}/api/v1/me/wallets/{wallet_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"is_primary": True},
            )
            if resp.status_code != 200:
                logger.warning(
                    "Set-primary failed (%s) for wallet %s", resp.status_code, wallet_id
                )
        except httpx.HTTPError as exc:
            logger.warning("Set-primary transport error for %s: %s", wallet_id, exc)

    async def onboard_meter(
        self,
        meter_id: str,
        *,
        meter_type: Optional[str] = None,
        location: Optional[str] = None,
    ) -> OnboardResult:
        """Resolve the ``user_id`` owning ``meter_id`` (login → register → verify).

        **Login-first**: the meter fleet is seed-deterministic, so a meter's owner
        account (derived from ``meter_id``) persists across runs. Attempting login
        *before* register means an already-onboarded meter never re-hits IAM's
        tight register limiter (5 registrations/hour/IP) — only genuinely new
        meters pay the register+verify cost. Login is the higher-budget endpoint
        (10/min/IP). Idempotent either way: re-runs recover the same session.

        Does not claim the meter on-chain (no IAM endpoint for that).
        ``meter_type``/``location`` are accepted for call compatibility but unused.
        """
        username, email, _ = derive_credentials(meter_id)
        reg_user_id = None
        try:
            # Existing (seeded) account: a plain login recovers the session with
            # no register call, so the register limiter is untouched on re-runs.
            session = await self._login(username)
        except httpx.HTTPError as exc:
            logger.warning("Login error for %s: %s", username, exc)
            session = None

        if not session or not session.get("access_token"):
            # New (or not-yet-activated) account: register (idempotent; returns the
            # new user_id as a fallback) then verify to flip ``is_active`` so the
            # session works, falling back to a plain login if verify is disabled.
            try:
                reg_user_id = await self._register_user(username, email)
            except httpx.HTTPError as exc:
                return OnboardResult(
                    meter_id, None, None, False, False, f"register error: {exc}"
                )
            try:
                session = await self._verify_email(email)
                if not session or not session.get("access_token"):
                    session = await self._login(username)
            except httpx.HTTPError as exc:
                logger.warning("Verify/login error for %s: %s", username, exc)
                session = None

        user_id = (session.get("user_id") if session else None) or reg_user_id
        wallet = session.get("wallet_address") if session else None
        if not user_id:
            return OnboardResult(
                meter_id, None, None, False, False, "could not resolve user_id"
            )

        # Link a deterministic primary wallet so settlement can resolve a mint
        # recipient (IAM GetUserWallet -> primary address). Requires the session
        # access_token; without it the account has no wallet and Path B mints
        # fail `not_found: No primary wallet found`.
        access_token = session.get("access_token") if session else None
        wallet_detail = "no wallet linked (no session token)"
        meter_detail = "meter not registered (no session token)"
        meter_registered = False
        if access_token:
            linked = await self._link_primary_wallet(
                access_token, derive_owner_wallet(meter_id)
            )
            if linked:
                wallet = linked
                wallet_detail = "primary wallet linked"
            else:
                wallet_detail = "wallet link failed"

            # Register the meter (serial == meter_id) to this user via meter-service
            # so the durable `meters` row exists — the Aggregator Bridge resolves
            # owners from `meters JOIN users` (Postgres tier-3 source of truth).
            meter_registered = await self._register_meter(
                access_token, meter_id, meter_type=meter_type, location=location
            )
            meter_detail = (
                "meter registered (Postgres owner row)"
                if meter_registered
                else "meter register failed"
            )

        detail = (
            "owner resolved via verify/login"
            if (session and session.get("access_token"))
            else "owner resolved from registration id"
        )
        return OnboardResult(
            meter_id,
            user_id,
            wallet,
            meter_registered,
            False,
            f"{detail}; {wallet_detail}; {meter_detail}",
        )


async def onboard_fleet(
    gateway_url: str,
    meter_ids: Iterable[str],
    *,
    meter_types: Optional[Mapping[str, str]] = None,
    concurrency: int = DEFAULT_ONBOARD_CONCURRENCY,
) -> dict[str, str]:
    """Onboard every meter to IAM and return the resolved ``{meter_id: user_id}``.

    Runs register -> login -> claim per meter (bounded by ``concurrency``).
    Meters whose onboarding fails or yields no ``user_id`` are logged and omitted
    so the caller can fall back to any static owner map. Never raises for an
    individual meter; a transport failure is contained per task.
    """
    ids = list(dict.fromkeys(meter_ids))  # dedupe, preserve order
    if not ids:
        return {}
    types = dict(meter_types or {})
    sem = asyncio.Semaphore(max(1, concurrency))
    out: dict[str, str] = {}

    async with IamOnboardingClient(gateway_url) as client:

        async def _one(mid: str) -> None:
            async with sem:
                try:
                    res = await client.onboard_meter(mid, meter_type=types.get(mid))
                except httpx.HTTPError as exc:
                    logger.warning("IAM onboard error for %s: %s", mid, exc)
                    return
            if res.user_id:
                out[mid] = res.user_id
            else:
                logger.warning(
                    "IAM onboard yielded no user_id for %s: %s", mid, res.detail
                )

        await asyncio.gather(*(_one(m) for m in ids))

    return out


def load_owner_cache(path: str) -> dict[str, str]:
    """Load a persisted ``{meter_id: user_id}`` owner map (``{}`` on any problem).

    The cache is the durable record of meters already onboarded in a prior run.
    Because the meter fleet is seed-deterministic and the bridge resolves owners
    from the persistent Postgres ``meters`` row, a cached meter needs no IAM call
    on the next boot — coverage accumulates across boots under IAM's tight rate
    limits instead of being redone (and re-throttled) every time.
    """
    try:
        p = Path(path)
        if not p.is_file():
            return {}
        data = json.loads(p.read_text())
    except (OSError, ValueError) as exc:
        logger.warning("Owner cache load failed (%s): %s", path, exc)
        return {}
    if not isinstance(data, dict):
        logger.warning("Owner cache at %s is not a JSON object; ignoring", path)
        return {}
    return {str(k): str(v) for k, v in data.items() if v}


def save_owner_cache(path: str, owners: Mapping[str, str]) -> None:
    """Persist the ``{meter_id: user_id}`` owner map (atomic write; best-effort).

    Writes to a temp file then renames, so a crash mid-write can't corrupt the
    cache. Failures are logged, never raised — onboarding is non-fatal.
    """
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_text(json.dumps(dict(owners), indent=2, sort_keys=True))
        tmp.replace(p)  # atomic on POSIX
    except OSError as exc:
        logger.warning("Owner cache save failed (%s): %s", path, exc)
