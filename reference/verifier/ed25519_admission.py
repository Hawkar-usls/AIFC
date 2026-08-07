#!/usr/bin/env python3
"""AIFC Verifier A v0.6 Ed25519 cryptographic admission.

This layer consumes already-bound SignaturePreimageMaterial values and verifies
the receipt signatures against keys resolved from the exact signing registry
snapshot. It establishes registry-local cryptographic validity only.

It deliberately does NOT establish historical compromise safety, retroactive key
invalidation, external freshness, or any scientific conclusion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ed25519_crypto import Ed25519CryptoError, backend_identity, verify_ed25519
from resolver_v02 import EvidenceResolverV02
from signature_policy_admission import SignaturePreimageMaterial, SignaturePreimageReplaySummary


class Ed25519AdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class Ed25519ReplaySummary:
    receipt_count: int
    verified_count: int
    backend_version: str
    backend_executable_sha256: str


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Ed25519AdmissionError(code)


def _registry(resolver: EvidenceResolverV02, registry_hash: str) -> Mapping[str, Any]:
    resolved = resolver.resolve(registry_hash, expected_schema="AIFC/witness-registry/v1")
    if resolved.parsed_json is None:
        raise Ed25519AdmissionError(f"EXPECTED_REGISTRY_JSON:{registry_hash}")
    return resolved.parsed_json


def _public_key_for_material(material: SignaturePreimageMaterial, resolver: EvidenceResolverV02) -> bytes:
    registry = _registry(resolver, material.registry_hash)
    _require(registry.get("registry_sequence") == material.registry_sequence, "REGISTRY_SEQUENCE_REBINDING")

    witnesses = registry.get("witnesses")
    _require(isinstance(witnesses, list), "WITNESS_REGISTRY_MEMBERS_INVALID")
    matches = [w for w in witnesses if isinstance(w, Mapping) and w.get("witness_id") == material.witness_id]
    _require(len(matches) == 1, "WITNESS_ID_NOT_UNIQUE_IN_SIGNING_REGISTRY")
    witness = matches[0]
    _require(witness.get("status") == "ACTIVE", "WITNESS_NOT_ACTIVE_AT_SIGNING_REGISTRY")

    keys = witness.get("keys")
    _require(isinstance(keys, list), "WITNESS_KEY_SET_INVALID")
    key_matches = [k for k in keys if isinstance(k, Mapping) and k.get("key_id") == material.key_id]
    _require(len(key_matches) == 1, "KEY_ID_NOT_UNIQUE_FOR_WITNESS")
    key = key_matches[0]

    _require(key.get("algorithm") == "Ed25519", "KEY_ALGORITHM_NOT_ED25519")
    _require(key.get("public_key_encoding") == "hex", "PUBLIC_KEY_ENCODING_AMBIGUITY")
    _require(key.get("status") == "ACTIVE", "KEY_NOT_ACTIVE_AT_SIGNING_REGISTRY")

    valid_from = key.get("valid_from_registry_sequence")
    valid_until = key.get("valid_until_registry_sequence")
    _require(isinstance(valid_from, int) and valid_from <= material.registry_sequence, "KEY_NOT_YET_VALID_AT_REGISTRY_SEQUENCE")
    if valid_until is not None:
        _require(isinstance(valid_until, int) and material.registry_sequence <= valid_until, "KEY_EXPIRED_AT_REGISTRY_SEQUENCE")

    public_key_hex = key.get("public_key")
    _require(isinstance(public_key_hex, str) and len(public_key_hex) == 64, "ED25519_PUBLIC_KEY_ENCODING_INVALID")
    try:
        public_key = bytes.fromhex(public_key_hex)
    except ValueError as exc:
        raise Ed25519AdmissionError("ED25519_PUBLIC_KEY_HEX_INVALID") from exc
    _require(len(public_key) == 32 and public_key_hex == public_key.hex(), "ED25519_PUBLIC_KEY_NOT_CANONICAL_LOWERCASE_HEX")
    return public_key


def replay_ed25519_signatures(
    preimage_summary: SignaturePreimageReplaySummary,
    resolver: EvidenceResolverV02,
) -> Ed25519ReplaySummary:
    """Cryptographically verify every strongest-profile receipt in the summary."""
    _require(preimage_summary.receipt_count > 0, "ED25519_NO_RECEIPTS")
    _require(len(preimage_summary.materials) == preimage_summary.receipt_count, "ED25519_MATERIAL_COUNT_MISMATCH")

    try:
        backend = backend_identity()
    except Ed25519CryptoError as exc:
        raise Ed25519AdmissionError(f"ED25519_BACKEND_UNAVAILABLE:{exc}") from exc

    verified = 0
    for material in preimage_summary.materials:
        receipt = material.receipt
        _require(receipt.get("signature_algorithm") == "Ed25519", "RECEIPT_SIGNATURE_ALGORITHM_REBINDING")
        _require(receipt.get("signature_profile_id") == "AIFC-ED25519-DIRECT-TYPED-V1", "RECEIPT_SIGNATURE_PROFILE_REBINDING")
        signature_hex = receipt.get("signature")
        _require(isinstance(signature_hex, str) and len(signature_hex) == 128, "ED25519_SIGNATURE_ENCODING_INVALID")
        try:
            signature = bytes.fromhex(signature_hex)
        except ValueError as exc:
            raise Ed25519AdmissionError("ED25519_SIGNATURE_HEX_INVALID") from exc
        _require(len(signature) == 64 and signature_hex == signature.hex(), "ED25519_SIGNATURE_NOT_CANONICAL_LOWERCASE_HEX")

        public_key = _public_key_for_material(material, resolver)
        try:
            valid = verify_ed25519(public_key, material.preimage, signature)
        except Ed25519CryptoError as exc:
            raise Ed25519AdmissionError(f"ED25519_BACKEND_FAILURE:{material.witness_id}:{material.key_id}:{exc}") from exc
        _require(valid, f"ED25519_SIGNATURE_INVALID:{material.witness_id}:{material.key_id}:{material.receipt_schema}")
        verified += 1

    _require(verified == preimage_summary.receipt_count, "ED25519_VERIFIED_COUNT_MISMATCH")
    return Ed25519ReplaySummary(
        receipt_count=preimage_summary.receipt_count,
        verified_count=verified,
        backend_version=backend.version_line,
        backend_executable_sha256=backend.executable_sha256,
    )
