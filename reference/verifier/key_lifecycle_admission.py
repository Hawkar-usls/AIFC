#!/usr/bin/env python3
"""Authoritative v0.7 historical-key admission wrapper.

Before applying lifecycle events, independently rebind each certificate group's
required quorum and registry sequence to the resolved signing registry. This
prevents post-crypto weakening of q or registry-position metadata.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from key_lifecycle import KeyLifecycleError, KeyLifecycleReplaySummary, replay_historical_key_lifecycle
from resolver_v02 import EvidenceResolverV02
from signature_policy_admission import SignaturePreimageMaterial, SignaturePreimageReplaySummary


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise KeyLifecycleError(code)


def _registry(resolver: EvidenceResolverV02, registry_hash: str) -> Mapping[str, Any]:
    resolved = resolver.resolve(registry_hash, expected_schema="AIFC/witness-registry/v1")
    if resolved.parsed_json is None:
        raise KeyLifecycleError(f"EXPECTED_REGISTRY_JSON:{registry_hash}")
    return resolved.parsed_json


def _rebind_certificate_groups(
    signatures: SignaturePreimageReplaySummary,
    resolver: EvidenceResolverV02,
) -> None:
    groups: dict[str, list[SignaturePreimageMaterial]] = defaultdict(list)
    for material in signatures.materials:
        _require(bool(material.certificate_group_id), "KEY_LIFECYCLE_SIGNATURE_GROUP_MISSING")
        groups[material.certificate_group_id].append(material)

    for group_id, materials in groups.items():
        registry_hashes = {m.registry_hash for m in materials}
        registry_sequences = {m.registry_sequence for m in materials}
        q_values = {m.required_q for m in materials}
        _require(len(registry_hashes) == 1, f"HISTORICAL_QUORUM_REGISTRY_REBINDING:{group_id}")
        _require(len(registry_sequences) == 1, f"HISTORICAL_QUORUM_SEQUENCE_REBINDING:{group_id}")
        _require(len(q_values) == 1, f"HISTORICAL_QUORUM_Q_REBINDING:{group_id}")

        registry_hash = next(iter(registry_hashes))
        sequence = next(iter(registry_sequences))
        q = next(iter(q_values))
        registry = _registry(resolver, registry_hash)
        _require(registry.get("registry_sequence") == sequence, f"HISTORICAL_REGISTRY_SEQUENCE_REBINDING:{group_id}")
        fault = registry.get("fault_model")
        _require(isinstance(fault, Mapping), f"HISTORICAL_FAULT_MODEL_MISSING:{group_id}")
        _require(fault.get("q") == q, f"HISTORICAL_QUORUM_Q_VS_REGISTRY_MISMATCH:{group_id}")


def replay_historical_key_lifecycle_admitted(
    manifest: Mapping[str, Any],
    resolver: EvidenceResolverV02,
    signatures: SignaturePreimageReplaySummary,
) -> KeyLifecycleReplaySummary:
    _rebind_certificate_groups(signatures, resolver)
    return replay_historical_key_lifecycle(manifest, resolver, signatures)
