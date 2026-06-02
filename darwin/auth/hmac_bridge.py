"""Experimental HMAC bridge helpers for simulator-only auth scenarios.

This module uses Python standard-library HMAC-SHA256 to move selected tests and
scenarios from symbolic booleans toward deterministic tag verification. It is
not production cryptography and does not provide key exchange or secure storage.
"""

from __future__ import annotations

import hashlib
import hmac
import json

from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
from darwin.models.security import HmacVerificationResult


def canonical_json(data: object) -> str:
    """Return deterministic JSON used as simulator HMAC input."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_hmac_tag(secret: str | bytes, data: object) -> str:
    """Compute an experimental HMAC-SHA256 tag for canonicalized simulator data."""
    return hmac.new(
        _secret_bytes(secret),
        canonical_json(data).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_hmac_tag(secret: str | bytes, data: object, expected_tag: str) -> bool:
    """Verify an experimental HMAC-SHA256 tag with constant-time comparison."""
    if not expected_tag:
        return False
    actual_tag = compute_hmac_tag(secret, data)
    return hmac.compare_digest(actual_tag, expected_tag)


def packet_auth_material(packet: object) -> dict[str, object]:
    """Return deterministic packet fields covered by experimental HMAC auth."""
    return {
        "packet_id": getattr(packet, "packet_id", None),
        "packet_class": getattr(packet, "packet_class", None),
        "packet_type": getattr(packet, "packet_type", None),
        "source_device_id": getattr(packet, "source_device_id", None),
        "target_device_id": getattr(packet, "target_device_id", None),
        "source_hub_id": getattr(packet, "source_hub_id", None),
        "target_hub_hint": getattr(packet, "target_hub_hint", None),
        "lane_id": getattr(packet, "lane_id", None),
        "sequence_number": getattr(packet, "sequence_number", None),
        "payload": getattr(packet, "payload", None),
    }


def checkpoint_auth_material(checkpoint_packet: object) -> dict[str, object]:
    """Return deterministic checkpoint fields covered by experimental HMAC auth."""
    return {
        "packet_id": getattr(checkpoint_packet, "packet_id", None),
        "packet_class": getattr(checkpoint_packet, "packet_class", None),
        "packet_type": getattr(checkpoint_packet, "packet_type", None),
        "source_device_id": getattr(checkpoint_packet, "source_device_id", None),
        "source_hub_id": getattr(checkpoint_packet, "source_hub_id", None),
        "state": getattr(checkpoint_packet, "state", None),
        "checkpoint_tier": getattr(checkpoint_packet, "checkpoint_tier", None),
        "created_at": getattr(checkpoint_packet, "created_at", None),
        "active_lane_count": getattr(checkpoint_packet, "active_lane_count", None),
        "battery_level": getattr(checkpoint_packet, "battery_level", None),
        "payload": getattr(checkpoint_packet, "payload", None),
    }


def rolling_proof_material(
    device_id: str,
    hub_id: str,
    session_id: str,
    counter: int,
    nonce: str,
    capability: str,
) -> dict[str, object]:
    """Return deterministic rolling-proof fields for experimental HMAC tests."""
    return {
        "device_id": device_id,
        "hub_id": hub_id,
        "session_id": session_id,
        "counter": counter,
        "nonce": nonce,
        "capability": capability,
    }


def verify_rolling_proof_tag(
    secret: str | bytes,
    *,
    device_id: str,
    hub_id: str,
    session_id: str,
    counter: int,
    nonce: str,
    capability: str,
    expected_tag: str,
) -> HmacVerificationResult:
    """Verify an experimental rolling-proof HMAC tag."""
    material = rolling_proof_material(
        device_id=device_id,
        hub_id=hub_id,
        session_id=session_id,
        counter=counter,
        nonce=nonce,
        capability=capability,
    )
    success = verify_hmac_tag(secret, material, expected_tag)
    return HmacVerificationResult(
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
        success=success,
        reason=None if success else "invalid_auth_tag",
    )


def _secret_bytes(secret: str | bytes) -> bytes:
    if isinstance(secret, bytes):
        return secret
    return secret.encode("utf-8")
