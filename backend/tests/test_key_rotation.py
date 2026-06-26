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
    cur = km.current("M-1")
    assert cur is not None and cur[0] == kid1 and len(cur[1]) == 32  # (kid, 32B guek)

    kid2 = km.rotate("M-1")
    assert kid2 == kid1 + 1  # strictly increments within a run
    assert km.current("M-1")[0] == kid2
    assert km.current("M-1")[1] != cur[1]  # fresh random GUEK each rotation

    # Seeded the wrapped blob at v{kid} + the current pointer (never the raw key).
    keys = {k for _, pairs in seeded for k, _ in pairs}
    assert f"gridtokenx:devices:M-1:enckey:v{kid1}" in keys
    assert f"gridtokenx:devices:M-1:enckey:v{kid2}" in keys
    assert "gridtokenx:devices:M-1:enckey:current" in keys
    vals = {k: v for _, pairs in seeded for k, v in pairs}
    assert vals["gridtokenx:devices:M-1:enckey:current"] == str(kid2)
    assert vals[f"gridtokenx:devices:M-1:enckey:v{kid2}"].startswith("vault:v1:")


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
    km.ensure(em._key_ids)  # initial key for both (same second -> same base kid)

    base = em.key_status()["M-1"]
    assert em.key_status() == {"M-1": base, "M-2": base}
    # Rotate one meter -> only its kid advances.
    assert em.rotate_keys("M-1") == {"M-1": base + 1}
    assert em.key_status() == {"M-1": base + 1, "M-2": base}
    # Rotate whole fleet -> each advances past its own current.
    out = em.rotate_keys()
    assert out == {"M-1": base + 2, "M-2": base + 1}


def test_emitter_rotate_noop_without_key_manager():
    em = AggregatorBridgeEmitter(
        "http://bridge:4010", redis_url="redis://x:6379", encrypt_enabled=True
    )
    assert em.rotate_keys() == {}
    assert em.key_status() == {}


def test_rotate_prunes_version_past_grace_window():
    seeded, seed_fn = _capture_seed()
    deleted = []

    def del_fn(redis_url, keys):
        deleted.extend(keys)
        return len(keys)

    km = MeterKeyManager(
        _FakeVault(), "redis://x:6379", seed_fn, del_fn=del_fn, grace_versions=2
    )
    # First two versions: nothing pruned yet (within grace).
    k1 = km.rotate("M-1")
    k2 = km.rotate("M-1")
    assert deleted == []
    # 3rd -> oldest (k1) falls out of the 2-version grace window.
    km.rotate("M-1")
    assert deleted == [f"gridtokenx:devices:M-1:enckey:v{k1}"]
    # 4th -> next-oldest (k2) pruned.
    km.rotate("M-1")
    assert deleted == [
        f"gridtokenx:devices:M-1:enckey:v{k1}",
        f"gridtokenx:devices:M-1:enckey:v{k2}",
    ]


def test_rotate_no_prune_without_del_fn():
    seeded, seed_fn = _capture_seed()
    km = MeterKeyManager(_FakeVault(), "redis://x:6379", seed_fn, grace_versions=1)
    last = 0
    for _ in range(4):
        last = km.rotate("M-1")  # must not raise without a del_fn
    assert km.current("M-1")[0] == last


def test_rotate_fleet_skips_meter_on_vault_error():
    class _FlakyVault:
        def wrap(self, key_bytes):
            raise VaultTransitError("vault down")

    seeded, seed_fn = _capture_seed()
    km = MeterKeyManager(_FlakyVault(), "redis://x:6379", seed_fn)
    out = km.rotate_fleet(["M-1", "M-2"])
    assert out == {}  # both failed, contained (no exception)
    assert km.current("M-1") is None  # no state advanced on failure
