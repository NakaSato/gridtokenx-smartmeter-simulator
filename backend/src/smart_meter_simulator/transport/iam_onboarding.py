"""IAM onboarding: bind each simulated meter to a user account for attribution.

The parent ``gridtokenx-iam-service`` is the source of truth for user identity.
This module derives one deterministic account per meter and resolves its
``user_id`` so telemetry can be attributed: it **registers** the user, **verifies**
it (IAM accepts a dev ``verify_<email>`` token — no email round-trip — which flips
``is_active`` so logins succeed and returns an auto-login session), and falls back
to a plain **login** if verification is unavailable. Each step is idempotent, so
re-runs reliably re-resolve the same ``user_id``.

Scope note: there is **no** IAM REST endpoint to claim a meter / register its
on-chain PDA — that path is an Anchor ``registry`` instruction via Chain Bridge,
out of this simulator's scope. So onboarding resolves ownership only; it does not
claim meters on-chain (``claimed_in_iam``/``on_chain`` stay ``False``).

Because **no service** mirrors the meter→owner binding into the Aggregator Bridge owner
map, the caller must seed Redis via
:func:`smart_meter_simulator.transport.aggregator_bridge.register_meter_owners_redis`
so telemetry is actually attributed.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

import httpx

logger = logging.getLogger(__name__)

# Default dev password for simulator-owned accounts. Override via onboard script.
DEFAULT_PASSWORD = "SimMeter#2026"


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
    ):
        self.base_url = base_url.rstrip("/")
        self.password = password
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "IamOnboardingClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _register_user(self, username: str, email: str) -> Optional[str]:
        """Register a user; return user_id. Idempotent on 409/already-exists."""
        resp = await self._client.post(
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
        resp = await self._client.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": self.password},
        )
        if resp.status_code != 200:
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
        resp = await self._client.get(
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

    async def onboard_meter(
        self,
        meter_id: str,
        *,
        meter_type: Optional[str] = None,
        location: Optional[str] = None,
    ) -> OnboardResult:
        """Resolve the ``user_id`` owning ``meter_id`` (register → verify → login).

        Idempotent: registration returns the new id (kept as a fallback), email
        verification activates the account so logins work, and a plain login
        recovers the session on re-runs. Does not claim the meter on-chain (no IAM
        endpoint for that). ``meter_type``/``location`` are accepted for call
        compatibility but unused.
        """
        username, email, _ = derive_credentials(meter_id)
        try:
            # Registration returns the new user_id directly; keep it as an owner
            # fallback in case both verify and login are unavailable this run.
            reg_user_id = await self._register_user(username, email)
        except httpx.HTTPError as exc:
            return OnboardResult(
                meter_id, None, None, False, False, f"register error: {exc}"
            )

        # Verify (idempotent) so login works on every run, then fall back to a
        # plain login if the dev verify token form is unavailable.
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
        detail = (
            "owner resolved via verify/login"
            if (session and session.get("access_token"))
            else "owner resolved from registration id"
        )
        return OnboardResult(meter_id, user_id, wallet, False, False, detail)


async def onboard_fleet(
    gateway_url: str,
    meter_ids: Iterable[str],
    *,
    meter_types: Optional[Mapping[str, str]] = None,
    concurrency: int = 8,
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
