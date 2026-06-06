"""Tests for the Oracle Bridge owner read-back path.

``read_meter_owners_redis`` lets a re-run recover meter->user owners a prior run
already seeded in the bridge's Redis registry (the binding the sim can no longer
re-derive — e.g. an IAM account that exists but is unverified, so login can't
return its user_id). These tests pin the raw-RESP GET pipeline against a tiny
in-process fake server so no real Redis is required.
"""

from __future__ import annotations

import socket
import threading
from contextlib import contextmanager

from smart_meter_simulator.transport.oracle_bridge import read_meter_owners_redis


def _bulk(value: str) -> bytes:
    b = value.encode()
    return b"$" + str(len(b)).encode() + b"\r\n" + b + b"\r\n"


NIL = b"$-1\r\n"


@contextmanager
def _fake_redis(replies: list[bytes], *, expect_auth: bool = False):
    """Serve a fixed ordered sequence of RESP replies on a loopback port.

    The client (:func:`read_meter_owners_redis`) sends GETs in serial order then
    reads back ``len(serials)`` replies in that same order, so the server can
    reply blind with a pre-baked sequence. Prepends ``+OK`` when ``expect_auth``.
    """
    payload = (b"+OK\r\n" if expect_auth else b"") + b"".join(replies)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    host, port = srv.getsockname()

    def _serve() -> None:
        try:
            conn, _ = srv.accept()
        except OSError:
            return
        with conn:
            conn.sendall(payload)
            # Drain the request and wait for the client to close its side.
            conn.settimeout(2.0)
            try:
                while conn.recv(4096):
                    pass
            except OSError:
                pass

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    try:
        yield host, port
    finally:
        srv.close()
        t.join(timeout=2.0)


def test_read_back_all_present():
    with _fake_redis([_bulk("user-1"), _bulk("user-2")]) as (host, port):
        owners = read_meter_owners_redis(f"redis://{host}:{port}", ["M-1", "M-2"])
    assert owners == {"M-1": "user-1", "M-2": "user-2"}


def test_read_back_mixed_nil_omits_missing():
    with _fake_redis([_bulk("user-1"), NIL, _bulk("user-3")]) as (host, port):
        owners = read_meter_owners_redis(
            f"redis://{host}:{port}", ["M-1", "M-2", "M-3"]
        )
    assert owners == {"M-1": "user-1", "M-3": "user-3"}  # M-2 (nil) omitted


def test_read_back_dedupes_serials():
    # Duplicate serials collapse to one GET; only two replies are consumed.
    with _fake_redis([_bulk("user-1"), _bulk("user-2")]) as (host, port):
        owners = read_meter_owners_redis(
            f"redis://{host}:{port}", ["M-1", "M-2", "M-1"]
        )
    assert owners == {"M-1": "user-1", "M-2": "user-2"}


def test_read_back_skips_leading_auth_reply():
    # With a password the server emits +OK first; it must not shift the mapping.
    with _fake_redis([_bulk("user-1")], expect_auth=True) as (host, port):
        owners = read_meter_owners_redis(f"redis://:secret@{host}:{port}", ["M-1"])
    assert owners == {"M-1": "user-1"}


def test_read_back_empty_serials_returns_empty():
    # No serials -> no connection attempt at all.
    assert read_meter_owners_redis("redis://127.0.0.1:1/", []) == {}


def test_read_back_connection_failure_returns_empty():
    # Nothing listening on this port -> contained, returns {} (non-fatal).
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        dead_port = s.getsockname()[1]
    owners = read_meter_owners_redis(f"redis://127.0.0.1:{dead_port}", ["M-1"])
    assert owners == {}
