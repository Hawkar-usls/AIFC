#!/usr/bin/env python3
"""AIFC Verifier A signature-preimage admission layer.

This module establishes that the exact Ed25519 message is frozen and can be
reconstructed for every receipt currently carried by the replay package. It also
returns bound signature materials for crypto and later historical quorum replay.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping

from canonical_v02 import protocol_hash_v02
from resolver import EvidenceResolutionError
from resolver_v02 import EvidenceResolverV02
from signature_preimage import SignaturePreimageError, compile_signature_preimage


class SignaturePolicyAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class SignaturePreimageMaterial:
    receipt_schema: str
    receipt: Mapping[str, Any]
    preimage: bytes
    registry_hash: str
    registry_sequence: int
    witness_id: str
    key_id: str
    certificate_group_id: str = ""
    required_q: int = 1


@dataclass(frozen=True)
class SignaturePreimageReplaySummary:
    receipt_count: int
    preimage_sha256s: tuple[str, ...]
    materials: tuple[SignaturePreimageMaterial, ...]


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise SignaturePolicyAdmissionError(code)


def _obj(resolver: EvidenceResolverV02, content_hash: str, schema: str) -> Mapping[str, Any]:
    resolved = resolver.resolve(content_hash, expected_schema=schema)
    if resolved.parsed_json is None:
        raise SignaturePolicyAdmissionError(f"EXPECTED_PROTOCOL_JSON:{content_hash}")
    return resolved.parsed_json


def _registry_sequence(resolver: EvidenceResolverV02, registry_hash: str) -> int:
    registry = _obj(resolver, registry_hash, "AIFC/witness-registry/v1")
    sequence = registry.get("registry_sequence")
    _require(isinstance(sequence, int) and sequence >= 0, "SIGNING_REGISTRY_SEQUENCE_INVALID")
    return sequence


def _content_exists_as_declared(resolver: EvidenceResolverV02, content_hash: str, content_schema: str) -> None:
    _obj(resolver, content_hash, content_schema)


def _material(
    receipt: Mapping[str, Any],
    preimage: bytes,
    registry_hash_field: str,
    certificate_group_id: str,
    required_q: int,
) -> SignaturePreimageMaterial:
    registry_hash = receipt.get(registry_hash_field)
    registry_sequence = receipt.get("registry_sequence")
    witness_id = receipt.get("witness_id")
    key_id = receipt.get("key_id")
    _require(isinstance(registry_hash, str), "SIGNATURE_MATERIAL_REGISTRY_HASH_INVALID")
    _require(isinstance(registry_sequence, int) and registry_sequence >= 0, "SIGNATURE_MATERIAL_REGISTRY_SEQUENCE_INVALID")
    _require(isinstance(witness_id, str) and witness_id, "SIGNATURE_MATERIAL_WITNESS_ID_INVALID")
    _require(isinstance(key_id, str) and key_id, "SIGNATURE_MATERIAL_KEY_ID_INVALID")
    _require(isinstance(certificate_group_id, str) and certificate_group_id, "SIGNATURE_MATERIAL_GROUP_ID_INVALID")
    _require(isinstance(required_q, int) and required_q >= 1, "SIGNATURE_MATERIAL_REQUIRED_Q_INVALID")
    return SignaturePreimageMaterial(
        receipt_schema=str(receipt.get("schema")),
        receipt=receipt,
        preimage=preimage,
        registry_hash=registry_hash,
        registry_sequence=registry_sequence,
        witness_id=witness_id,
        key_id=key_id,
        certificate_group_id=certificate_group_id,
        required_q=required_q,
    )


def _trial_quorum_receipts(
    resolver: EvidenceResolverV02,
    quorum_hash: str,
    policy: Mapping[str, Any],
) -> list[SignaturePreimageMaterial]:
    quorum = _obj(resolver, quorum_hash, "AIFC/quorum-certificate/v1")
    expected_registry_sequence = _registry_sequence(resolver, str(quorum.get("registry_hash")))
    required_q = quorum.get("q")
    _require(isinstance(required_q, int) and required_q >= 1, "TRIAL_QUORUM_Q_INVALID")
    receipts = quorum.get("receipts")
    _require(isinstance(receipts, list) and receipts, "TRIAL_QUORUM_RECEIPTS_MISSING")
    out: list[SignaturePreimageMaterial] = []
    for receipt in receipts:
        _require(isinstance(receipt, Mapping), "TRIAL_RECEIPT_NOT_OBJECT")
        _require(receipt.get("experiment_id") == quorum.get("experiment_id"), "CROSS_EXPERIMENT_SIGNATURE_REPLAY")
        _require(receipt.get("trial_index") == quorum.get("trial_index"), "CROSS_TRIAL_SIGNATURE_REPLAY")
        _require(receipt.get("logical_position") == quorum.get("logical_position"), "LOGICAL_POSITION_REBINDING")
        _require(receipt.get("content_hash") == quorum.get("content_hash"), "SIGNED_CONTENT_HASH_REBINDING")
        _require(receipt.get("registry_hash") == quorum.get("registry_hash"), "REGISTRY_REBINDING")
        _require(receipt.get("registry_sequence") == expected_registry_sequence, "REGISTRY_SEQUENCE_REBINDING")
        content_schema = receipt.get("content_schema")
        _require(isinstance(content_schema, str), "SIGNED_CONTENT_SCHEMA_MISSING")
        _content_exists_as_declared(resolver, str(receipt.get("content_hash")), content_schema)
        preimage = compile_signature_preimage(receipt, policy)
        out.append(_material(receipt, preimage, "registry_hash", quorum_hash, required_q))
    return out


def _plan_quorum_receipts(
    resolver: EvidenceResolverV02,
    quorum_hash: str,
    plan_hash: str,
    policy: Mapping[str, Any],
) -> list[SignaturePreimageMaterial]:
    quorum = _obj(resolver, quorum_hash, "AIFC/experiment-plan-quorum/v1")
    _require(quorum.get("content_hash") == plan_hash, "PLAN_QUORUM_CONTENT_REBINDING")
    expected_registry_sequence = _registry_sequence(resolver, str(quorum.get("registry_hash")))
    _require(expected_registry_sequence == 0, "PLAN_QUORUM_REGISTRY_SEQUENCE_NOT_ZERO")
    required_q = quorum.get("q")
    _require(isinstance(required_q, int) and required_q >= 1, "PLAN_QUORUM_Q_INVALID")
    receipts = quorum.get("receipts")
    _require(isinstance(receipts, list) and receipts, "PLAN_QUORUM_RECEIPTS_MISSING")
    out: list[SignaturePreimageMaterial] = []
    for receipt in receipts:
        _require(isinstance(receipt, Mapping), "PLAN_RECEIPT_NOT_OBJECT")
        _require(receipt.get("experiment_id") == quorum.get("experiment_id"), "CROSS_EXPERIMENT_SIGNATURE_REPLAY")
        _require(receipt.get("logical_position") == quorum.get("logical_position"), "LOGICAL_POSITION_REBINDING")
        _require(receipt.get("content_hash") == quorum.get("content_hash"), "SIGNED_CONTENT_HASH_REBINDING")
        _require(receipt.get("registry_hash") == quorum.get("registry_hash"), "REGISTRY_REBINDING")
        _require(receipt.get("registry_sequence") == expected_registry_sequence, "REGISTRY_SEQUENCE_REBINDING")
        _require(receipt.get("content_schema") == "AIFC/experiment-plan/v1", "PLAN_RECEIPT_CONTENT_SCHEMA_REBINDING")
        _content_exists_as_declared(resolver, plan_hash, "AIFC/experiment-plan/v1")
        preimage = compile_signature_preimage(receipt, policy)
        out.append(_material(receipt, preimage, "registry_hash", quorum_hash, required_q))
    return out


def _transition_receipts(
    resolver: EvidenceResolverV02,
    certificate_hash: str,
    policy: Mapping[str, Any],
) -> list[SignaturePreimageMaterial]:
    certificate = _obj(resolver, certificate_hash, "AIFC/registry-transition-certificate/v1")
    body = certificate.get("transition_body")
    _require(isinstance(body, Mapping), "REGISTRY_TRANSITION_BODY_MISSING")
    body_hash = certificate.get("transition_body_hash")
    _require(isinstance(body_hash, str), "REGISTRY_TRANSITION_BODY_HASH_MISSING")
    _require(protocol_hash_v02(body) == body_hash, "REGISTRY_TRANSITION_BODY_HASH_MISMATCH")

    out: list[SignaturePreimageMaterial] = []
    for quorum_field, expected_role in (
        ("old_registry_authorization", "OLD_REGISTRY_AUTHORIZATION"),
        ("new_registry_acceptance", "NEW_REGISTRY_ACCEPTANCE"),
    ):
        quorum = certificate.get(quorum_field)
        _require(isinstance(quorum, Mapping), f"REGISTRY_TRANSITION_QUORUM_MISSING:{quorum_field}")
        _require(quorum.get("experiment_id") == body.get("experiment_id"), "REGISTRY_EXPERIMENT_REBINDING")
        _require(quorum.get("role") == expected_role, "TRANSITION_ROLE_REBINDING")
        _require(quorum.get("transition_body_hash") == body_hash, "SIGNED_CONTENT_HASH_REBINDING")
        registry_hash = quorum.get("signing_registry_hash")
        _require(isinstance(registry_hash, str), "SIGNING_REGISTRY_HASH_MISSING")
        expected_registry_sequence = _registry_sequence(resolver, registry_hash)
        required_q = quorum.get("q")
        _require(isinstance(required_q, int) and required_q >= 1, "REGISTRY_TRANSITION_QUORUM_Q_INVALID")
        receipts = quorum.get("receipts")
        _require(isinstance(receipts, list) and receipts, "REGISTRY_TRANSITION_RECEIPTS_MISSING")
        group_id = f"{certificate_hash}:{expected_role}"
        for receipt in receipts:
            _require(isinstance(receipt, Mapping), "REGISTRY_TRANSITION_RECEIPT_NOT_OBJECT")
            _require(receipt.get("experiment_id") == quorum.get("experiment_id"), "CROSS_EXPERIMENT_SIGNATURE_REPLAY")
            _require(receipt.get("role") == expected_role, "TRANSITION_ROLE_REBINDING")
            _require(receipt.get("transition_body_hash") == body_hash, "SIGNED_CONTENT_HASH_REBINDING")
            _require(receipt.get("signing_registry_hash") == registry_hash, "REGISTRY_REBINDING")
            _require(receipt.get("registry_sequence") == expected_registry_sequence, "REGISTRY_SEQUENCE_REBINDING")
            _require(receipt.get("content_schema") == "AIFC/registry-transition-body/v1", "TRANSITION_CONTENT_SCHEMA_REBINDING")
            preimage = compile_signature_preimage(receipt, policy)
            out.append(_material(receipt, preimage, "signing_registry_hash", group_id, required_q))
    return out


def replay_signature_preimages(
    manifest: Mapping[str, Any],
    resolver: EvidenceResolverV02,
) -> SignaturePreimageReplaySummary:
    """Resolve the frozen policy and reconstruct every current receipt preimage."""
    plan_hash = manifest.get("experiment_plan_hash")
    _require(isinstance(plan_hash, str), "EXPERIMENT_PLAN_HASH_MISSING")
    plan = _obj(resolver, plan_hash, "AIFC/experiment-plan/v1")
    policy_hash = plan.get("signature_preimage_policy_hash")
    _require(isinstance(policy_hash, str), "SIGNATURE_PREIMAGE_POLICY_HASH_MISSING")
    policy = _obj(resolver, policy_hash, "AIFC/signature-preimage-policy/v1")
    _require(policy.get("experiment_id") == plan.get("experiment_id"), "SIGNATURE_POLICY_EXPERIMENT_REBINDING")
    _require(policy.get("protocol_version") == plan.get("protocol_version"), "SIGNATURE_POLICY_PROTOCOL_VERSION_REBINDING")
    _require(policy.get("frozen_before_first_created") is True, "SIGNATURE_POLICY_NOT_FROZEN")

    materials: list[SignaturePreimageMaterial] = []

    plan_q = manifest.get("experiment_plan_quorum_certificate_hash")
    _require(isinstance(plan_q, str), "EXPERIMENT_PLAN_QUORUM_HASH_MISSING")
    materials.extend(_plan_quorum_receipts(resolver, plan_q, plan_hash, policy))

    for field in (
        "created_quorum_certificate_hash",
        "pre_return_quorum_certificate_hash",
        "pre_target_view_quorum_certificate_hash",
    ):
        qh = manifest.get(field)
        _require(isinstance(qh, str), f"TRIAL_QUORUM_HASH_MISSING:{field}")
        materials.extend(_trial_quorum_receipts(resolver, qh, policy))

    transition_hashes = manifest.get("registry_transition_certificate_hashes")
    _require(isinstance(transition_hashes, list), "REGISTRY_TRANSITION_HASH_LIST_INVALID")
    for certificate_hash in transition_hashes:
        _require(isinstance(certificate_hash, str), "REGISTRY_TRANSITION_HASH_INVALID")
        materials.extend(_transition_receipts(resolver, certificate_hash, policy))

    digests = tuple(hashlib.sha256(material.preimage).hexdigest() for material in materials)
    _require(len(digests) == len(set(digests)), "DUPLICATE_SIGNATURE_PREIMAGE_POSITION")
    return SignaturePreimageReplaySummary(
        receipt_count=len(materials),
        preimage_sha256s=digests,
        materials=tuple(materials),
    )
