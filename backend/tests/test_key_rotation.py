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


def test_rotate_reconciles_orphaned_versions_from_redis():
    """A restart leaves the prior process's enckey:v* in Redis but resets the
    in-memory _live map. The first rotate must reconcile via scan_fn and prune
    those orphans down to the grace window — otherwise they leak forever."""
    seeded, seed_fn = _capture_seed()
    deleted = []

    def del_fn(redis_url, keys):
        deleted.extend(keys)
        return len(keys)

    # Simulate 5 versions left in Redis by a previous run (older kids).
    orphans = [1000, 1001, 1002, 1003, 1004]

    def scan_fn(redis_url, meter_id):
        return list(orphans)

    km = MeterKeyManager(
        _FakeVault(),
        "redis://x:6379",
        seed_fn,
        del_fn=del_fn,
        grace_versions=2,
        scan_fn=scan_fn,
    )
    new_kid = km.rotate("M-1")  # first rotate this "process"
    # Keep grace_versions=2 total: the new kid + 1 most-recent orphan; the rest
    # of the orphans (oldest first) are pruned. 5 orphans + new = 6, keep 2.
    assert deleted == [
        f"gridtokenx:devices:M-1:enckey:v{k}" for k in (1000, 1001, 1002, 1003)
    ]
    assert km._live["M-1"] == [1004, new_kid]
    # Reconcile happens only once: a second rotate prunes only the new overflow.
    deleted.clear()
    km.rotate("M-1")
    assert deleted == ["gridtokenx:devices:M-1:enckey:v1004"]


def test_rotate_reconcile_excludes_just_written_kid():
    """If scan_fn (racily) returns the kid just written this rotate, it must not
    be double-counted — it is appended exactly once."""
    seeded, seed_fn = _capture_seed()
    deleted = []
    km = MeterKeyManager(
        _FakeVault(),
        "redis://x:6379",
        seed_fn,
        del_fn=lambda u, k: deleted.extend(k) or len(k),
        grace_versions=3,
        scan_fn=lambda u, mid: list(km._state.get(mid, (0,))[:1]),  # returns [new_kid]
    )
    new_kid = km.rotate("M-1")
    assert km._live["M-1"] == [new_kid]  # not [new_kid, new_kid]
    assert deleted == []


def test_rotate_skips_scan_when_exists_fn_says_no_prior_version():
    """A genuinely new meter (no :current key from any prior process) has
    nothing to reconcile, so exists_fn=False must skip the O(keyspace) scan_fn
    entirely — calling it would defeat the point of the cheap pre-check."""
    seeded, seed_fn = _capture_seed()
    scan_calls = []

    def scan_fn(redis_url, meter_id):
        scan_calls.append(meter_id)
        return [999]  # would be picked up if scan_fn were (wrongly) called

    km = MeterKeyManager(
        _FakeVault(),
        "redis://x:6379",
        seed_fn,
        grace_versions=2,
        scan_fn=scan_fn,
        exists_fn=lambda u, mid: False,
    )
    new_kid = km.rotate("M-new")
    assert scan_calls == []
    assert km._live["M-new"] == [new_kid]


def test_rotate_runs_scan_when_exists_fn_says_prior_version_present():
    """A meter with a :current key from a prior process still gets reconciled —
    exists_fn=True must NOT skip scan_fn."""
    seeded, seed_fn = _capture_seed()
    scan_calls = []

    def scan_fn(redis_url, meter_id):
        scan_calls.append(meter_id)
        return [1000]

    km = MeterKeyManager(
        _FakeVault(),
        "redis://x:6379",
        seed_fn,
        del_fn=lambda u, k: len(k),
        grace_versions=2,
        scan_fn=scan_fn,
        exists_fn=lambda u, mid: True,
    )
    new_kid = km.rotate("M-known")
    assert scan_calls == ["M-known"]
    assert km._live["M-known"] == [1000, new_kid]


def test_rotate_uses_index_fn_and_skips_scan_when_indexed():
    """When index_fn returns a (non-None) list, that O(1) read must be used
    instead of the O(keyspace) scan_fn — even though exists_fn says there is
    prior state to reconcile."""
    seeded, seed_fn = _capture_seed()
    scan_calls = []

    def scan_fn(redis_url, meter_id):
        scan_calls.append(meter_id)
        return [9999]  # would corrupt the result if (wrongly) used

    km = MeterKeyManager(
        _FakeVault(),
        "redis://x:6379",
        seed_fn,
        del_fn=lambda u, k: len(k),
        grace_versions=2,
        scan_fn=scan_fn,
        exists_fn=lambda u, mid: True,
        index_fn=lambda u, mid: [2000],
    )
    new_kid = km.rotate("M-indexed")
    assert scan_calls == []
    assert km._live["M-indexed"] == [2000, new_kid]


def test_rotate_migrates_legacy_meter_from_scan_into_index():
    """index_fn returning None means no index exists yet (a meter rotated
    before the index was introduced) — fall back to scan_fn once, then backfill
    the index via index_add_fn so future rotations never need the scan again."""
    seeded, seed_fn = _capture_seed()
    added = []

    km = MeterKeyManager(
        _FakeVault(),
        "redis://x:6379",
        seed_fn,
        del_fn=lambda u, k: len(k),
        grace_versions=3,
        scan_fn=lambda u, mid: [3000, 3001],
        exists_fn=lambda u, mid: True,
        index_fn=lambda u, mid: None,
        index_add_fn=lambda u, mid, kids: added.append((mid, list(kids))),
    )
    new_kid = km.rotate("M-legacy")
    assert km._live["M-legacy"] == [3000, 3001, new_kid]
    # Backfilled with the scan result, then incrementally with the new kid.
    assert added == [("M-legacy", [3000, 3001]), ("M-legacy", [new_kid])]


def test_rotate_maintains_index_incrementally_across_calls():
    """Every rotate (not just the first/reconcile one) SADDs its new kid, and
    pruning SREMs the expired one — the index stays in sync without ever
    re-scanning."""
    seeded, seed_fn = _capture_seed()
    added = []
    removed = []
    km = MeterKeyManager(
        _FakeVault(),
        "redis://x:6379",
        seed_fn,
        del_fn=lambda u, k: len(k),
        grace_versions=1,
        exists_fn=lambda u, mid: False,  # fresh meter, no scan/index lookup
        index_add_fn=lambda u, mid, kids: added.append(list(kids)),
        index_remove_fn=lambda u, mid, kid: removed.append(kid),
    )
    first = km.rotate("M-fresh")
    second = km.rotate("M-fresh")
    assert added == [[first], [second]]
    assert removed == [first]  # pruned once grace_versions=1 was exceeded


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
