#!/usr/bin/env python3
"""AIFC v0.5 normative signature-preimage construction and evidence replay.

This module deliberately does NOT verify Ed25519 signatures. It freezes and replays
only the exact message bytes that a future Ed25519 verifier will consume.

Wire grammar:
  ASCII("AIFC:SIGNATURE_PREIMAGE:v1") || 0x00 || FIELD...
  FIELD := TAG_U8 || LENGTH_U32BE || VALUE

Tags and order are frozen below. Hash fields are 32 decoded bytes. Unsigned integer
fields are 8-byte big-endian. Optional trial/timestamp fields carry an explicit
presence octet, preventing absence from being confused with an empty value.

Strongest-grade replay does not trust caller-supplied protocol_version,
content_schema, or registry_sequence. It derives them from the frozen experiment
plan and exact content-addressed registry/content objects through the resolver.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from canonical import CanonicalizationError, validate_value
from resolver import EvidenceResolutionError

DOMAIN = b"AIFC:SIGNATURE_PREIMAGE:v1\x00"
PROFILE_ID = "AIFC-SIGNATURE-PREIMAGE-V1"
SUPPORTED_RECEIPTS = (
    "AIFC/experiment-plan-receipt/v1",
    "AIFC/registry-transition-receipt/v1",
    "AIFC/witness-receipt/v1",
)

TAG_RECEIPT_SCHEMA = 0x01
TAG_PROTOCOL_VERSION = 0x02
TAG_SIGNATURE_PROFILE_ID = 0x03
TAG_SCOPE_KIND = 0x04
TAG_EXPERIMENT_ID = 0x05
TAG_TRIAL_INDEX_OPTIONAL = 0x06
TAG_LOGICAL_POSITION_OR_ROLE = 0x07
TAG_CONTENT_SCHEMA = 0x08
TAG_CONTENT_HASH = 0x09
TAG_REGISTRY_HASH = 0x0A
TAG_REGISTRY_SEQUENCE = 0x0B
TAG_WITNESS_ID = 0x0C
TAG_KEY_ID = 0x0D
TAG_TIMESTAMP_OPTIONAL = 0x0E


class SignaturePreimageError(ValueError):
    pass


@dataclass(frozen=True)
class ReceiptBinding:
    receipt_schema: str
    scope_kind: str
    experiment_id: str
    trial_index: int | None
    logical_position_or_role: str
    content_hash: str
    registry_hash: str
    witness_id: str
    key_id: str
    timestamp: str | None


def normative_policy(experiment_id: str, policy_id: str = "aifc-signature-v1") -> dict[str, Any]:
    return {
        "schema": "AIFC/signature-preimage-policy/v1",
        "policy_id": policy_id,
        "experiment_id": experiment_id,
        "signature_profile_id": PROFILE_ID,
        "signature_algorithm": "Ed25519",
        "ed25519_variant": "PURE_ED25519_RFC8032_NO_PROTOCOL_PREHASH",
        "domain_separator_ascii": "AIFC:SIGNATURE_PREIMAGE:v1",
        "framing": "FIELD_TAG_U8_LENGTH_U32BE_VALUE",
        "field_tag_encoding": "UNSIGNED_8_BIT_FIXED_BY_PROFILE",
        "field_length_encoding": "UNSIGNED_32_BIT_BIG_ENDIAN",
        "integer_encoding": "UNSIGNED_64_BIT_BIG_ENDIAN",
        "hash_encoding": "LOWERCASE_HEX_IN_JSON_DECODED_TO_EXACT_32_BYTES_IN_PREIMAGE",
        "string_encoding": "UTF8",
        "string_normalization": "NFC_REQUIRED_BY_AIFC_CANONICALIZATION_NO_ADDITIONAL_SIGNATURE_NORMALIZATION",
        "supported_receipt_schemas": list(SUPPORTED_RECEIPTS),
        "public_key_external_encoding": "LOWERCASE_HEX_32_BYTES_EXACT",
        "signature_external_encoding": "LOWERCASE_HEX_64_BYTES_EXACT",
        "timestamp_integrity_semantics": "IF_PRESENT_TIMESTAMP_UTF8_IS_SIGNED_FOR_INTEGRITY_BUT_IS_NOT_FRESHNESS_PROOF",
        "frozen_before_first_created": True,
    }


def assert_normative_policy(policy: Mapping[str, Any], experiment_id: str) -> None:
    expected = normative_policy(experiment_id, str(policy.get("policy_id", "")))
    if dict(policy) != expected:
        raise SignaturePreimageError("NON_NORMATIVE_SIGNATURE_PREIMAGE_POLICY")


def _utf8(value: str, label: str) -> bytes:
    if not isinstance(value, str):
        raise SignaturePreimageError(f"{label}:EXPECTED_STRING")
    try:
        validate_value(value, label)
        return value.encode("utf-8", errors="strict")
    except (CanonicalizationError, UnicodeEncodeError) as exc:
        raise SignaturePreimageError(f"{label}:INVALID_UTF8_OR_NFC:{exc}") from exc


def _hash32(value: str, label: str) -> bytes:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise SignaturePreimageError(f"{label}:EXPECTED_LOWERCASE_HEX_32_BYTES")
    return bytes.fromhex(value)


def _u64(value: int, label: str) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 0xFFFFFFFFFFFFFFFF:
        raise SignaturePreimageError(f"{label}:EXPECTED_U64")
    return value.to_bytes(8, "big")


def _optional_u64(value: int | None, label: str) -> bytes:
    if value is None:
        return b"\x00"
    return b"\x01" + _u64(value, label)


def _optional_utf8(value: str | None, label: str) -> bytes:
    if value is None:
        return b"\x00"
    return b"\x01" + _utf8(value, label)


def _field(tag: int, value: bytes) -> bytes:
    if not (0 <= tag <= 255):
        raise SignaturePreimageError("FIELD_TAG_OUT_OF_RANGE")
    if len(value) > 0xFFFFFFFF:
        raise SignaturePreimageError("FIELD_VALUE_TOO_LONG")
    return bytes((tag,)) + len(value).to_bytes(4, "big") + value


def receipt_binding(receipt: Mapping[str, Any]) -> ReceiptBinding:
    schema = receipt.get("schema")
    if schema == "AIFC/witness-receipt/v1":
        return ReceiptBinding(
            schema, "TRIAL", receipt["experiment_id"], receipt["trial_index"], receipt["logical_position"],
            receipt["content_hash"], receipt["registry_hash"], receipt["witness_id"], receipt["key_id"],
            receipt.get("wall_clock_timestamp"),
        )
    if schema == "AIFC/experiment-plan-receipt/v1":
        return ReceiptBinding(
            schema, "EXPERIMENT", receipt["experiment_id"], None, receipt["logical_position"],
            receipt["content_hash"], receipt["registry_hash"], receipt["witness_id"], receipt["key_id"],
            receipt.get("wall_clock_timestamp"),
        )
    if schema == "AIFC/registry-transition-receipt/v1":
        return ReceiptBinding(
            schema, "REGISTRY_TRANSITION", receipt["experiment_id"], None, receipt["role"],
            receipt["transition_body_hash"], receipt["signing_registry_hash"], receipt["witness_id"], receipt["key_id"],
            receipt.get("wall_clock_timestamp"),
        )
    raise SignaturePreimageError(f"UNSUPPORTED_RECEIPT_SCHEMA:{schema}")


def build_signature_preimage(
    receipt: Mapping[str, Any], *, policy: Mapping[str, Any], protocol_version: str,
    content_schema: str, registry_sequence: int,
) -> bytes:
    """Low-level deterministic builder for frozen vectors/independent implementations.

    Strongest-grade verification must call replay_signature_preimage() instead.
    """
    binding = receipt_binding(receipt)
    assert_normative_policy(policy, binding.experiment_id)
    if policy["experiment_id"] != binding.experiment_id:
        raise SignaturePreimageError("SIGNATURE_POLICY_EXPERIMENT_REBINDING")
    if receipt.get("signature_algorithm") != "Ed25519":
        raise SignaturePreimageError("SIGNATURE_ALGORITHM_NOT_ED25519")

    fields = (
        _field(TAG_RECEIPT_SCHEMA, _utf8(binding.receipt_schema, "receipt_schema")),
        _field(TAG_PROTOCOL_VERSION, _utf8(protocol_version, "protocol_version")),
        _field(TAG_SIGNATURE_PROFILE_ID, _utf8(PROFILE_ID, "signature_profile_id")),
        _field(TAG_SCOPE_KIND, _utf8(binding.scope_kind, "scope_kind")),
        _field(TAG_EXPERIMENT_ID, _utf8(binding.experiment_id, "experiment_id")),
        _field(TAG_TRIAL_INDEX_OPTIONAL, _optional_u64(binding.trial_index, "trial_index")),
        _field(TAG_LOGICAL_POSITION_OR_ROLE, _utf8(binding.logical_position_or_role, "logical_position_or_role")),
        _field(TAG_CONTENT_SCHEMA, _utf8(content_schema, "content_schema")),
        _field(TAG_CONTENT_HASH, _hash32(binding.content_hash, "content_hash")),
        _field(TAG_REGISTRY_HASH, _hash32(binding.registry_hash, "registry_hash")),
        _field(TAG_REGISTRY_SEQUENCE, _u64(registry_sequence, "registry_sequence")),
        _field(TAG_WITNESS_ID, _utf8(binding.witness_id, "witness_id")),
        _field(TAG_KEY_ID, _utf8(binding.key_id, "key_id")),
        _field(TAG_TIMESTAMP_OPTIONAL, _optional_utf8(binding.timestamp, "wall_clock_timestamp")),
    )
    return DOMAIN + b"".join(fields)


def _resolved_protocol(resolver, content_hash: str, expected_schema: str | None = None) -> Mapping[str, Any]:
    try:
        resolved = resolver.resolve(content_hash, expected_schema=expected_schema)
    except EvidenceResolutionError as exc:
        raise SignaturePreimageError(f"SIGNATURE_PREIMAGE_EVIDENCE_RESOLUTION:{exc}") from exc
    if resolved.parsed_json is None:
        raise SignaturePreimageError(f"SIGNATURE_PREIMAGE_EXPECTED_PROTOCOL_JSON:{content_hash}")
    return resolved.parsed_json


def replay_signature_preimage(receipt: Mapping[str, Any], *, experiment_plan_hash: str, resolver) -> bytes:
    """Derive all semantic preimage metadata from exact resolved evidence.

    No Ed25519 verification occurs here. The result is only the exact byte string a
    later pure-Ed25519 gate is required to verify.
    """
    binding = receipt_binding(receipt)
    plan = _resolved_protocol(resolver, experiment_plan_hash, "AIFC/experiment-plan/v1")
    if plan.get("experiment_id") != binding.experiment_id:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_PLAN_EXPERIMENT_REBINDING")
    if plan.get("frozen_before_first_created") is not True:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_PLAN_NOT_FROZEN")
    protocol_version = plan.get("protocol_version")
    if not isinstance(protocol_version, str) or not protocol_version:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_PROTOCOL_VERSION_INVALID")

    policy_hash = plan.get("signature_preimage_policy_hash")
    if not isinstance(policy_hash, str) or len(policy_hash) != 64:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_POLICY_HASH_INVALID")
    policy = _resolved_protocol(resolver, policy_hash, "AIFC/signature-preimage-policy/v1")
    if policy.get("experiment_id") != binding.experiment_id:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_POLICY_EXPERIMENT_REBINDING")
    assert_normative_policy(policy, binding.experiment_id)

    registry = _resolved_protocol(resolver, binding.registry_hash, "AIFC/witness-registry/v1")
    if registry.get("experiment_id") != binding.experiment_id:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_REGISTRY_EXPERIMENT_REBINDING")
    registry_sequence = registry.get("registry_sequence")
    if not isinstance(registry_sequence, int) or isinstance(registry_sequence, bool) or registry_sequence < 0:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_REGISTRY_SEQUENCE_INVALID")

    content = _resolved_protocol(resolver, binding.content_hash)
    content_schema = content.get("schema")
    if not isinstance(content_schema, str) or not content_schema:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_CONTENT_SCHEMA_INVALID")
    if content.get("experiment_id") != binding.experiment_id:
        raise SignaturePreimageError("SIGNATURE_PREIMAGE_CONTENT_EXPERIMENT_REBINDING")

    if binding.receipt_schema == "AIFC/experiment-plan-receipt/v1":
        if binding.content_hash != experiment_plan_hash or content_schema != "AIFC/experiment-plan/v1":
            raise SignaturePreimageError("SIGNATURE_PREIMAGE_EXPERIMENT_PLAN_CONTENT_REBINDING")
    elif binding.receipt_schema == "AIFC/registry-transition-receipt/v1":
        if content_schema != "AIFC/registry-transition-body/v1":
            raise SignaturePreimageError("SIGNATURE_PREIMAGE_REGISTRY_TRANSITION_CONTENT_SCHEMA_REBINDING")

    return build_signature_preimage(
        receipt,
        policy=policy,
        protocol_version=protocol_version,
        content_schema=content_schema,
        registry_sequence=registry_sequence,
    )


def preimage_hex(*args, **kwargs) -> str:
    return build_signature_preimage(*args, **kwargs).hex()
