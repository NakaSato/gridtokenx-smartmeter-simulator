"""Tests for per-meter GUEK rotation + Vault-Transit KEK wrapping (sim side)."""

from __future__ import annotations

import base64

import httpx
import pytest

from smart_meter_simulator.transport.aggregator_bridge import AggregatorBridgeEmitter
from smart_meter_simulator.transport.key_rotation import (
    MeterKeyManager,
    VaultTransitClient,
    VaultTransitError,
)

# --- VaultTransitClient.wrap -------------------------------------------------


def test_vault_wrap_posts_plaintext_and_returns_ciphertext(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return httpx.Response(
            200,
            json={"data": {"ciphertext": "vault:v1:ABC123"}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(
        "smart_meter_simulator.transport.key_rotation.httpx.post", fake_post
    )
    client = VaultTransitClient("http://vault:8200", "root", "gridtokenx-meter-kek")
    key = b"\x01" * 32
    ct = client.wrap(key)

    assert ct == "vault:v1:ABC123"
    assert (
        captured["url"] == "http://vault:8200/v1/transit/encrypt/gridtokenx-meter-kek"
    )
    # Plaintext is base64 of the raw key; token in the Vault header.
    assert captured["json"]["plaintext"] == base64.b64encode(key).decode()
    assert captured["headers"]["X-Vault-Token"] == "root"


def test_vault_wrap_raises_on_http_error(monkeypatch):
    def fake_post(url, json, headers, timeout):
        return httpx.Response(
            403,
            json={"errors": ["permission denied"]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(
        "smart_meter_simulator.transport.key_rotation.httpx.post", fake_post
    )
    client = VaultTransitClient("http://vault:8200", "root", "kek")
    with pytest.raises(VaultTransitError):
        client.wrap(b"\x00" * 32)


def test_vault_wrap_raises_on_empty_ciphertext(monkeypatch):
    def fake_post(url, json, headers, timeout):
        return httpx.Response(
            200,
            json={"data": {"ciphertext": ""}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(
        "smart_meter_simulator.transport.key_rotation.httpx.post", fake_post
    )
    client = VaultTransitClient("http://vault:8200", "root", "kek")
    with pytest.raises(VaultTransitError):
        client.wrap(b"\x00" * 32)


# --- MeterKeyManager ---------------------------------------------------------


class _FakeVault:
    def __init__(self):
        self.calls = 0

    def wrap(self, key_bytes: bytes) -> str:
        self.calls += 1
        return f"vault:v1:wrapped-{self.calls}"


def _capture_seed():
    seeded = []

    def seed_fn(redis_url, pairs):
        seeded.append((redis_url, list(pairs)))
        return len(pairs)

    return seeded, seed_fn


def test_rotate_bumps_version_seeds_wrapped_and_holds_guek():
    seeded, seed_fn = _capture_seed()
    km = MeterKeyManager(_FakeVault(), "redis://x:6379", seed_fn)

    kid1 = km.rotate("M-1")
    assert kid1 == 1
    cur = km.current("M-1")
    assert cur is not None and cur[0] == 1 and len(cur[1]) == 32  # (kid, 32-byte guek)

    kid2 = km.rotate("M-1")
    assert kid2 == 2  # version increments
    assert km.current("M-1")[0] == 2
    assert km.current("M-1")[1] != cur[1]  # fresh random GUEK each rotation

    # Seeded the wrapped blob at v{kid} + the current pointer (never the raw key).
    keys = {k for _, pairs in seeded for k, _ in pairs}
    assert "gridtokenx:devices:M-1:enckey:v1" in keys
    assert "gridtokenx:devices:M-1:enckey:v2" in keys
    assert "gridtokenx:devices:M-1:enckey:current" in keys
    vals = {k: v for _, pairs in seeded for k, v in pairs}
    assert vals["gridtokenx:devices:M-1:enckey:current"] == "2"
    assert vals["gridtokenx:devices:M-1:enckey:v2"].startswith("vault:v1:")


def test_ensure_keys_only_new_meters():
    seeded, seed_fn = _capture_seed()
    vault = _FakeVault()
    km = MeterKeyManager(vault, "redis://x:6379", seed_fn)
    km.ensure(["M-1", "M-2"])
    assert vault.calls == 2  # both rotated to v1
    km.ensure(["M-1", "M-2", "M-3"])
    assert vault.calls == 3  # only M-3 newly rotated


def test_emitter_rotate_keys_and_status_delegate():
    _, seed_fn = _capture_seed()
    km = MeterKeyManager(_FakeVault(), "redis://x:6379", seed_fn)
    em = AggregatorBridgeEmitter(
        "http://bridge:4010",
        redis_url="redis://x:6379",
        encrypt_enabled=True,
        key_manager=km,
    )
    em._key_ids = frozenset({"M-1", "M-2"})
    km.ensure(em._key_ids)  # v1 for both

    assert em.key_status() == {"M-1": 1, "M-2": 1}
    # Rotate one meter -> only its kid advances.
    assert em.rotate_keys("M-1") == {"M-1": 2}
    assert em.key_status() == {"M-1": 2, "M-2": 1}
    # Rotate whole fleet.
    out = em.rotate_keys()
    assert out == {"M-1": 3, "M-2": 2}


def test_emitter_rotate_noop_without_key_manager():
    em = AggregatorBridgeEmitter(
        "http://bridge:4010", redis_url="redis://x:6379", encrypt_enabled=True
    )
    assert em.rotate_keys() == {}
    assert em.key_status() == {}


def test_rotate_fleet_skips_meter_on_vault_error():
    class _FlakyVault:
        def wrap(self, key_bytes):
            raise VaultTransitError("vault down")

    seeded, seed_fn = _capture_seed()
    km = MeterKeyManager(_FlakyVault(), "redis://x:6379", seed_fn)
    out = km.rotate_fleet(["M-1", "M-2"])
    assert out == {}  # both failed, contained (no exception)
    assert km.current("M-1") is None  # no state advanced on failure
