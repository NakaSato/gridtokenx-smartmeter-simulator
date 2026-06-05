"""IAM onboarding: bind each simulated meter_serial to a user account (one-time).

The parent ``gridtokenx-iam-service`` is the source of truth for meter ownership.
A meter is claimed by ``POST /api/v1/meters`` (UNIQUE ``serial_number`` → one-time
claim, plus on-chain PDA registration). The endpoint requires a user JWT and is
reached through the APISIX gateway (``:4001``), which injects the ``ApiGateway``
service role the IAM handlers require.

This module registers a user (one per meter), logs in, and claims the meter. The
claim writes the IAM DB row + (when the user is email-verified and walletted) the
on-chain PDA. Because **no service** mirrors that binding into the Oracle Bridge
owner map, the caller must also seed Redis via
:func:`smart_meter_simulator.transport.oracle_bridge.register_meter_owners_redis`
so telemetry is actually attributed.

Credentials are derived deterministically from ``meter_id`` so re-runs reuse the
same account (registration/claim are treated as idempotent).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

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

    async def _claim_meter(
        self,
        token: str,
        serial_number: str,
        meter_type: Optional[str],
        location: Optional[str],
    ) -> tuple[bool, bool, str]:
        """POST /api/v1/meters. Returns (claimed, on_chain, message)."""
        resp = await self._client.post(
            f"{self.base_url}/api/v1/meters",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "serial_number": serial_number,
                "meter_type": meter_type,
                "location": location,
            },
        )
        if resp.status_code != 200:
            return False, False, f"claim HTTP {resp.status_code}: {resp.text[:200]}"
        body = resp.json()
        # success=True only when on-chain onboarding also succeeded; a DB row may
        # still exist with success=False ("saved locally but on-chain failed").
        claimed = body.get("meter") is not None
        on_chain = bool(body.get("success")) and bool(body.get("transaction_signature"))
        return claimed, on_chain, body.get("message", "")

    async def onboard_meter(
        self,
        meter_id: str,
        *,
        meter_type: Optional[str] = None,
        location: Optional[str] = None,
    ) -> OnboardResult:
        """Register a user, log in, and claim ``meter_id`` for that user (one-time)."""
        username, email, _ = derive_credentials(meter_id)
        try:
            await self._register_user(username, email)
        except httpx.HTTPError as exc:
            return OnboardResult(
                meter_id, None, None, False, False, f"register error: {exc}"
            )

        session = await self._login(username)
        if not session or not session.get("access_token"):
            return OnboardResult(
                meter_id,
                session.get("user_id") if session else None,
                None,
                False,
                False,
                "login failed (user may be unverified)",
            )

        try:
            claimed, on_chain, msg = await self._claim_meter(
                session["access_token"], meter_id, meter_type, location
            )
        except httpx.HTTPError as exc:
            claimed, on_chain, msg = False, False, f"claim error: {exc}"

        return OnboardResult(
            meter_id=meter_id,
            user_id=session.get("user_id"),
            wallet_address=session.get("wallet_address"),
            claimed_in_iam=claimed,
            on_chain=on_chain,
            detail=msg,
        )
