"""Tests for IAM-driven meter ownership: the onboarding HTTP contract, the
fleet orchestration helper, and the emitter ownership merge it feeds."""

from __future__ import annotations

import asyncio

import httpx

from smart_meter_simulator.transport.iam_onboarding import (
    IamOnboardingClient,
    OnboardResult,
    onboard_fleet,
)
from smart_meter_simulator.transport.aggregator_bridge import AggregatorBridgeEmitter

# --- onboard_meter HTTP contract --------------------------------------------


def _run_onboard(handler, meter_id: str = "MTR-1") -> OnboardResult:
    async def run() -> OnboardResult:
        client = IamOnboardingClient("http://iam:4001")
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            return await client.onboard_meter(meter_id)
        finally:
            await client.close()

    return asyncio.run(run())


def test_onboard_meter_resolves_user_via_verify():
    # register -> verify (dev verify_<email> token) returns an auto-login session;
    # owner resolves from it. No meter claim happens (no IAM endpoint for that).
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/auth/register"):
            return httpx.Response(200, json={"id": "user-123"})
        if path.endswith("/auth/verify"):
            assert request.url.params["token"].startswith("verify_")
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "wallet_address": "WALLET1",
                    "auth": {
                        "access_token": "tok-abc",
                        "user": {"id": "user-123", "wallet_address": "WALLET1"},
                    },
                },
            )
        return httpx.Response(404)

    res = _run_onboard(handler)
    assert res.user_id == "user-123"
    assert res.wallet_address == "WALLET1"
    assert res.claimed_in_iam is False  # no claim path exists
    assert res.on_chain is False
    assert "verify" in res.detail


def test_onboard_meter_falls_back_to_login_when_verify_unavailable():
    # verify disabled (400) -> plain login succeeds (account already verified) ->
    # owner resolves from the login session.
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/auth/register"):
            return httpx.Response(409)  # already exists
        if path.endswith("/auth/verify"):
            return httpx.Response(400, json={"error": "invalid token"})
        if path.endswith("/auth/login"):
            return httpx.Response(
                200,
                json={
                    "access_token": "tok-xyz",
                    "user": {"id": "login-uid-7", "wallet_address": "WALLET2"},
                },
            )
        return httpx.Response(404)

    res = _run_onboard(handler)
    assert res.user_id == "login-uid-7"
    assert res.wallet_address == "WALLET2"
    assert res.claimed_in_iam is False


def test_onboard_meter_falls_back_to_registration_id():
    # New user (register 200 with id) but verify and login both unavailable ->
    # owner still resolves from the registration id.
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/auth/register"):
            return httpx.Response(200, json={"id": "reg-uid-9"})
        if path.endswith("/auth/verify"):
            return httpx.Response(400)
        if path.endswith("/auth/login"):
            return httpx.Response(401)
        return httpx.Response(404)

    res = _run_onboard(handler)
    assert res.user_id == "reg-uid-9"
    assert res.claimed_in_iam is False
    assert "registration id" in res.detail


def test_onboard_meter_no_id_yields_no_user():
    # register 409 (no id) + verify/login both fail -> nothing to attribute.
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/auth/register"):
            return httpx.Response(409)
        if path.endswith("/auth/verify"):
            return httpx.Response(400)
        if path.endswith("/auth/login"):
            return httpx.Response(401)
        return httpx.Response(404)

    res = _run_onboard(handler)
    assert res.user_id is None
    assert res.claimed_in_iam is False


# --- onboard_fleet orchestration --------------------------------------------


def test_onboard_fleet_dedupes_and_filters(monkeypatch):
    seen: list[str] = []

    async def fake_onboard(self, meter_id, *, meter_type=None):
        seen.append(meter_id)
        if meter_id == "M-BAD":
            return OnboardResult(meter_id, None, None, False, False, "no user")
        return OnboardResult(meter_id, f"uid-{meter_id}", None, True, True, "ok")

    monkeypatch.setattr(IamOnboardingClient, "onboard_meter", fake_onboard)

    owners = asyncio.run(
        onboard_fleet("http://iam:4001", ["M-1", "M-2", "M-1", "M-BAD"])
    )
    assert owners == {"M-1": "uid-M-1", "M-2": "uid-M-2"}  # M-BAD filtered
    assert sorted(seen) == ["M-1", "M-2", "M-BAD"]  # M-1 onboarded once (deduped)


def test_onboard_fleet_empty_returns_empty():
    assert asyncio.run(onboard_fleet("http://iam:4001", [])) == {}


def test_onboard_fleet_contains_individual_failure(monkeypatch):
    async def fake_onboard(self, meter_id, *, meter_type=None):
        if meter_id == "M-ERR":
            raise httpx.ConnectError("boom")
        return OnboardResult(meter_id, f"uid-{meter_id}", None, True, True, "ok")

    monkeypatch.setattr(IamOnboardingClient, "onboard_meter", fake_onboard)
    owners = asyncio.run(onboard_fleet("http://iam:4001", ["M-OK", "M-ERR"]))
    assert owners == {"M-OK": "uid-M-OK"}  # error contained, OK survives


# --- emitter ownership merge ------------------------------------------------


def test_add_ownership_merges_and_invalidates_cache():
    em = AggregatorBridgeEmitter(
        "http://bridge:4010",
        redis_url="redis://localhost:6379",
        ownership={"M-1": "static-1"},
    )
    em._key_ids = frozenset({"M-1"})  # pretend already seeded
    em.add_ownership({"M-1": "iam-1", "M-2": "iam-2"})  # M-1 overridden
    assert em._ownership == {"M-1": "iam-1", "M-2": "iam-2"}
    assert em._key_ids == frozenset()  # cache invalidated -> re-seed next emit


def test_add_ownership_noop_on_empty():
    em = AggregatorBridgeEmitter(
        "http://bridge:4010",
        redis_url="redis://localhost:6379",
        ownership={"M-1": "static-1"},
    )
    em._key_ids = frozenset({"M-1"})
    em.add_ownership({})
    assert em._ownership == {"M-1": "static-1"}
    assert em._key_ids == frozenset({"M-1"})  # untouched
