"""Tests de la vérification HMAC des webhooks PDP."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest

from apps.einvoicing.webhooks import (
    DEFAULT_TOLERANCE_SECONDS,
    parse_b2brouter_signature,
    verify_b2brouter_signature,
)


SECRET = "whsec_test_value"


def _sign(body: bytes, ts: int, secret: str = SECRET) -> str:
    payload = f"{ts}.".encode("utf-8") + body
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"t={ts},s={sig}"


class TestParseSignature:
    def test_valid_header(self) -> None:
        ts, sig = parse_b2brouter_signature("t=1700000000,s=" + ("a" * 64))
        assert ts == 1700000000
        assert sig == "a" * 64

    def test_invalid_header_returns_none(self) -> None:
        assert parse_b2brouter_signature("") == (None, None)
        assert parse_b2brouter_signature("garbage") == (None, None)
        assert parse_b2brouter_signature("t=,s=") == (None, None)


class TestVerifySignature:
    def test_valid_signature_passes(self) -> None:
        body = b'{"event":"invoice.delivered"}'
        ts = int(time.time())
        header = _sign(body, ts)
        assert verify_b2brouter_signature(body=body, header=header, secret=SECRET, now=ts)

    def test_tampering_detected(self) -> None:
        body = b'{"event":"invoice.delivered"}'
        tampered_body = b'{"event":"invoice.paid"}'
        ts = int(time.time())
        header = _sign(body, ts)
        assert not verify_b2brouter_signature(
            body=tampered_body, header=header, secret=SECRET, now=ts
        )

    def test_wrong_secret_fails(self) -> None:
        body = b'{}'
        ts = int(time.time())
        header = _sign(body, ts)
        assert not verify_b2brouter_signature(
            body=body, header=header, secret="other", now=ts
        )

    def test_replay_outside_tolerance_fails(self) -> None:
        body = b'{}'
        ts = int(time.time()) - DEFAULT_TOLERANCE_SECONDS - 10
        header = _sign(body, ts)
        assert not verify_b2brouter_signature(
            body=body, header=header, secret=SECRET, now=int(time.time())
        )

    def test_no_secret_configured_rejects(self) -> None:
        body = b'{}'
        ts = int(time.time())
        header = _sign(body, ts)
        # secret vide
        assert not verify_b2brouter_signature(
            body=body, header=header, secret="", now=ts
        )
