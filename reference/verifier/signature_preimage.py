#!/usr/bin/env python3
"""AIFC strongest-grade Ed25519 signature preimage compiler v1.

This module deliberately does NOT perform Ed25519 cryptography. It freezes the
exact bytes that a later crypto gate must sign/verify.

Preimage:
    ASCII("AIFC:SIGNATURE_PREIMAGE:v1") || 0x00
    || frame(tag=1,  receipt_schema UTF-8)
    || frame(tag=2,  protocol_version UTF-8)
    || frame(tag=3,  signature_profile_id UTF-8)
    || frame(tag=4,  scope_kind UTF-8)
    || frame(tag=5,  experiment_id UTF-8)
    || frame(tag=6,  trial-index marker/value)
    || frame(tag=7,  logical_position or transition role UTF-8)
    || frame(tag=8,  content_schema UTF-8)
    || frame(tag=9,  content_hash raw 32 bytes)
    || frame(tag=10, registry_hash raw 32 bytes)
    || frame(tag=11, registry_sequence u64_be)
    || frame(tag=12, witness_id UTF-8)
    || frame(tag=13, key_id UTF-8)
    || frame(tag=14, timestamp_present 0x00/0x01)
    || frame(tag=15, timestamp UTF-8 or empty)

Each frame is:
    u8(type_tag) || u64_be(payload_length) || payload

Ed25519 must later sign these bytes directly (no separate prehash).
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from canonical import CanonicalizationError, validate_value
from schema_runtime import RuntimeSchemaError, validate_protocol_object


class SignaturePreimageError(ValueError):
    pass


DOMAIN = b"AIFC:SIGNATURE_PREIMAGE:v1"
PROFILE_ID = "AIFC-ED25519-DIRECT-TYPED-V1"
POLICY_ID = "AIFC-ED25519-SIGNATURE-PREIMAGE-POLICY-V1"

TAG = {
    "receipt_schema": 1,
    "protocol_version": 2,
    "signature_profile_id": 3,
    "scope_kind": 4,
    "experiment_id": 5,
    "trial_index_or_absent": 6,
    "logical_position_or_transition_role": 7,
    "content_schema": 8,
    "content_hash": 9,
    "registry_hash": 10,
    "registry_sequence": 11,
    "witness_id": 12,
    "key_id": 13,
    "timestamp_present": 14,
    "timestamp_utf8": 15,
}

HEX_32 = re.compile(r"^[0-9a-f]{64}$")

RECEIPT_PROFILES = {
    "AIFC/witness-receipt/v1": {
        "policy_name": "trial_witness",
        "scope_kind": "TRIAL",
        "position_field": "logical_position",
        "content_hash_field": "content_hash",
        "registry_hash_field": "registry_hash",
        "trial_scoped": True,
    },
    "AIFC/experiment-plan-receipt/v1": {
        "policy_name": "experiment_plan",
        "scope_kind": "EXPERIMENT",
        "position_field": "logical_position",
        "content_hash_field": "content_hash",
        "registry_hash_field": "registry_hash",
        "trial_scoped": False,
    },
    "AIFC/registry-transition-receipt/v1": {
        "policy_name": "registry_transition",
        "scope_kind": "EXPERIMENT",
        "position_field": "role",
        "content_hash_field": "transition_body_hash",
        "registry_hash_field": "signing_registry_hash",
        "trial_scoped": False,
    },
}


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise SignaturePreimageError(code)


def _u64(value: Any, label: str) -> bytes:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{label}:NOT_INTEGER")
    _require(0 <= value <= 0xFFFFFFFFFFFFFFFF, f"{label}:OUT_OF_U64_RANGE")
    return value.to_bytes(8, "big")


def _utf8(value: Any, label: str) -> bytes:
    _require(isinstance(value, str), f"{label}:NOT_STRING")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise SignaturePreimageError(f"{label}:INVALID_UTF8") from exc
    return encoded


def _hex32(value: Any, label: str) -> bytes:
    _require(isinstance(value, str) and HEX_32.fullmatch(value) is not None, f"{label}:NOT_CANONICAL_HEX32")
    return bytes.fromhex(value)


def frame(tag: int, payload: bytes) -> bytes:
    _require(isinstance(tag, int) and 1 <= tag <= 255, "FRAME_TAG_OUT_OF_RANGE")
    _require(isinstance(payload, bytes), "FRAME_PAYLOAD_NOT_BYTES")
    _require(len(payload) <= 0xFFFFFFFFFFFFFFFF, "FRAME_PAYLOAD_TOO_LARGE")
    return bytes([tag]) + len(payload).to_bytes(8, "big") + payload


def _validate_normative_policy(policy: Mapping[str, Any]) -> None:
    try:
        validate_value(dict(policy))
        validate_protocol_object(policy, "AIFC/signature-preimage-policy/v1")
    except (CanonicalizationError, RuntimeSchemaError) as exc:
        raise SignaturePreimageError(f"SIGNATURE_POLICY_INVALID:{exc}") from exc

    _require(policy.get("policy_id") == POLICY_ID, "SIGNATURE_POLICY_ID_MISMATCH")
    _require(policy.get("signature_profile_id") == PROFILE_ID, "SIGNATURE_PROFILE_ID_MISMATCH")
    _require(policy.get("signature_algorithm") == "Ed25519", "SIGNATURE_ALGORITHM_MISMATCH")
    _require(policy.get("domain_separator") == DOMAIN.decode("ascii"), "SIGNATURE_DOMAIN_MISMATCH")
    _require(policy.get("framing") == "TAG_U8_LENGTH_U64BE_V1", "SIGNATURE_FRAMING_MISMATCH")
    _require(policy.get("prehash_mode") == "NONE_DIRECT_ED25519", "SIGNATURE_PREHASH_MODE_MISMATCH")
    _require(policy.get("public_key_encoding") == "LOWERCASE_HEX_32_BYTES", "PUBLIC_KEY_ENCODING_POLICY_MISMATCH")
    _require(policy.get("signature_encoding") == "LOWERCASE_HEX_64_BYTES", "SIGNATURE_ENCODING_POLICY_MISMATCH")
    _require(policy.get("timestamp_semantics") == "SIGNED_IF_PRESENT_INTEGRITY_ONLY_NOT_FRESHNESS", "TIMESTAMP_SEMANTICS_MISMATCH")
    _require(policy.get("frozen_before_first_created") is True, "SIGNATURE_POLICY_NOT_FROZEN")
    _require(policy.get("field_tags") == TAG, "SIGNATURE_FIELD_TAG_TABLE_MISMATCH")


def _validate_receipt_against_policy(receipt: Mapping[str, Any], policy: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        validate_value(dict(receipt))
    except CanonicalizationError as exc:
        raise SignaturePreimageError(f"RECEIPT_CANONICAL_VALUE_REJECTED:{exc}") from exc

    schema = receipt.get("schema")
    profile = RECEIPT_PROFILES.get(schema)
    _require(profile is not None, f"UNSUPPORTED_RECEIPT_SCHEMA:{schema}")
    try:
        validate_protocol_object(receipt, str(schema))
    except RuntimeSchemaError as exc:
        raise SignaturePreimageError(f"RECEIPT_SCHEMA_INVALID:{exc}") from exc

    _require(receipt.get("signature_profile_id") == PROFILE_ID, "RECEIPT_SIGNATURE_PROFILE_REBINDING")
    _require(receipt.get("signature_algorithm") == "Ed25519", "RECEIPT_SIGNATURE_ALGORITHM_REBINDING")
    _require(receipt.get("experiment_id") == policy.get("experiment_id"), "CROSS_EXPERIMENT_SIGNATURE_REPLAY")

    policy_profiles = policy.get("receipt_profiles")
    _require(isinstance(policy_profiles, Mapping), "SIGNATURE_POLICY_RECEIPT_PROFILES_INVALID")
    frozen = policy_profiles.get(profile["policy_name"])
    _require(isinstance(frozen, Mapping), "SIGNATURE_POLICY_RECEIPT_PROFILE_MISSING")
    _require(frozen.get("receipt_schema") == schema, "CROSS_RECEIPT_TYPE_REPLAY")
    _require(frozen.get("scope_kind") == profile["scope_kind"], "SIGNATURE_SCOPE_REBINDING")
    _require(frozen.get("position_source") == profile["position_field"], "SIGNATURE_POSITION_SOURCE_REBINDING")
    _require(frozen.get("content_hash_source") == profile["content_hash_field"], "SIGNATURE_CONTENT_SOURCE_REBINDING")
    _require(frozen.get("registry_hash_source") == profile["registry_hash_field"], "SIGNATURE_REGISTRY_SOURCE_REBINDING")
    return profile


def compile_signature_preimage(receipt: Mapping[str, Any], policy: Mapping[str, Any]) -> bytes:
    """Return the exact direct-Ed25519 message bytes for a supported receipt."""
    _validate_normative_policy(policy)
    profile = _validate_receipt_against_policy(receipt, policy)

    receipt_schema = str(receipt["schema"])
    protocol_version = policy.get("protocol_version")
    _require(isinstance(protocol_version, str) and protocol_version, "SIGNATURE_POLICY_PROTOCOL_VERSION_INVALID")

    if profile["trial_scoped"]:
        trial_payload = b"\x01" + _u64(receipt.get("trial_index"), "trial_index")
    else:
        _require("trial_index" not in receipt, "EXPERIMENT_SCOPED_RECEIPT_MUST_NOT_HAVE_TRIAL_INDEX")
        trial_payload = b"\x00"

    position = receipt.get(profile["position_field"])
    content_hash = receipt.get(profile["content_hash_field"])
    registry_hash = receipt.get(profile["registry_hash_field"])
    timestamp = receipt.get("wall_clock_timestamp")
    timestamp_present = b"\x00" if timestamp is None else b"\x01"
    timestamp_bytes = b"" if timestamp is None else _utf8(timestamp, "wall_clock_timestamp")

    fields = [
        (TAG["receipt_schema"], _utf8(receipt_schema, "receipt_schema")),
        (TAG["protocol_version"], _utf8(protocol_version, "protocol_version")),
        (TAG["signature_profile_id"], _utf8(receipt.get("signature_profile_id"), "signature_profile_id")),
        (TAG["scope_kind"], _utf8(profile["scope_kind"], "scope_kind")),
        (TAG["experiment_id"], _utf8(receipt.get("experiment_id"), "experiment_id")),
        (TAG["trial_index_or_absent"], trial_payload),
        (TAG["logical_position_or_transition_role"], _utf8(position, "logical_position_or_transition_role")),
        (TAG["content_schema"], _utf8(receipt.get("content_schema"), "content_schema")),
        (TAG["content_hash"], _hex32(content_hash, "content_hash")),
        (TAG["registry_hash"], _hex32(registry_hash, "registry_hash")),
        (TAG["registry_sequence"], _u64(receipt.get("registry_sequence"), "registry_sequence")),
        (TAG["witness_id"], _utf8(receipt.get("witness_id"), "witness_id")),
        (TAG["key_id"], _utf8(receipt.get("key_id"), "key_id")),
        (TAG["timestamp_present"], timestamp_present),
        (TAG["timestamp_utf8"], timestamp_bytes),
    ]

    _require([tag for tag, _ in fields] == list(range(1, 16)), "SIGNATURE_FIELD_ORDER_MISMATCH")
    return DOMAIN + b"\x00" + b"".join(frame(tag, payload) for tag, payload in fields)


def signature_preimage_sha256(receipt: Mapping[str, Any], policy: Mapping[str, Any]) -> str:
    """Diagnostic/test-vector digest only. Ed25519 itself must sign the raw preimage bytes."""
    return hashlib.sha256(compile_signature_preimage(receipt, policy)).hexdigest()
