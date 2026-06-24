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
    # owner resolves from it, then the meter is registered to that user via
    # meter-service (POST /api/v1/meters) -> claimed_in_iam True (Postgres owner row).
    posted_meter: dict[str, object] = {}

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
        if path.endswith("/v1/meters") and request.method == "POST":
            import json as _json

            posted_meter.update(_json.loads(request.content))
            return httpx.Response(200, json={"id": "meter-1"})
        return httpx.Response(404)

    res = _run_onboard(handler)
    assert res.user_id == "user-123"
    assert res.wallet_address == "WALLET1"
    assert res.claimed_in_iam is True  # meters row written via meter-service
    assert res.on_chain is False
    assert "verify" in res.detail
    assert posted_meter.get("serial_number") == "MTR-1"  # serial == meter_id


def test_onboard_meter_retries_register_on_429():
    # IAM rate-limits register under fleet load (HTTP 429). The client must retry
    # with backoff and still resolve the owner once the limiter lets it through.
    calls = {"register": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/auth/register"):
            calls["register"] += 1
            if calls["register"] <= 2:  # first two attempts rate-limited
                return httpx.Response(429, headers={"Retry-After": "0"}, json={})
            return httpx.Response(200, json={"id": "user-429"})
        if path.endswith("/auth/verify"):
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "wallet_address": "WALLET1",
                    "auth": {
                        "access_token": "tok",
                        "user": {"id": "user-429", "wallet_address": "WALLET1"},
                    },
                },
            )
        if path.endswith("/v1/meters") and request.method == "POST":
            return httpx.Response(200, json={"id": "meter-1"})
        return httpx.Response(404)

    async def run() -> OnboardResult:
        # backoff_base=0 keeps the test instant (no real sleeps between retries).
        client = IamOnboardingClient("http://iam:4001", backoff_base=0.0)
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            return await client.onboard_meter("MTR-429")
        finally:
            await client.close()

    res = asyncio.run(run())
    assert res.user_id == "user-429"  # resolved after the limiter cleared
    assert calls["register"] == 3  # two 429s + one success


def test_onboard_meter_fails_fast_on_headerless_429():
    # A 429 with no Retry-After (IAM's register limiter) must NOT be retried —
    # backoff can't beat an hour-window in one boot, so register is hit once.
    calls = {"register": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/auth/register"):
            calls["register"] += 1
            return httpx.Response(429, json={})  # no Retry-After header
        if path.endswith("/auth/login"):
            return httpx.Response(401)  # account doesn't exist yet
        return httpx.Response(404)

    async def run() -> OnboardResult:
        client = IamOnboardingClient("http://iam:4001", backoff_base=0.0)
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            return await client.onboard_meter("MTR-FF")
        finally:
            await client.close()

    res = asyncio.run(run())
    assert res.user_id is None  # throttled, unresolved this run
    assert calls["register"] == 1  # fail-fast: no futile retries


def test_onboard_meter_resolves_existing_account_via_login_first():
    # Login-first: an already-onboarded (seeded) account logs in immediately, so
    # register/verify are never reached and the register limiter is untouched.
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


# --- persistent owner cache --------------------------------------------------


def test_owner_cache_round_trip(tmp_path):
    from smart_meter_simulator.transport.iam_onboarding import (
        load_owner_cache,
        save_owner_cache,
    )

    path = str(tmp_path / "sub" / "owners.json")  # parent dir auto-created
    save_owner_cache(path, {"M-1": "uid-1", "M-2": "uid-2"})
    assert load_owner_cache(path) == {"M-1": "uid-1", "M-2": "uid-2"}


def test_owner_cache_missing_file_is_empty(tmp_path):
    from smart_meter_simulator.transport.iam_onboarding import load_owner_cache

    assert load_owner_cache(str(tmp_path / "nope.json")) == {}


def test_owner_cache_ignores_garbage(tmp_path):
    from smart_meter_simulator.transport.iam_onboarding import load_owner_cache

    p = tmp_path / "bad.json"
    p.write_text("not json {")
    assert load_owner_cache(str(p)) == {}  # corrupt -> empty, never raises


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
