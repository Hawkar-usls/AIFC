#!/usr/bin/env python3
"""AIFC Verifier A v0.7 historical key lifecycle replay.

Known lifecycle events are applied retroactively to already-verified signatures.
The engine can invalidate evidence when a known compromise/revocation destroys a
certificate quorum. It deliberately cannot prove that the local lifecycle ledger
is complete or fresh; absence of events therefore never establishes historical
key safety by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping

from resolver import EvidenceResolutionError
from resolver_v02 import EvidenceResolverV02
from signature_policy_admission import SignaturePreimageMaterial, SignaturePreimageReplaySummary


class KeyLifecycleError(ValueError):
    pass


@dataclass(frozen=True)
class KeyBoundary:
    witness_id: str
    key_id: str
    effective_from_registry_sequence: int
    event_type: str
    boundary_basis: str
    event_hash: str
    event_index: int


@dataclass(frozen=True)
class HistoricalQuorumResult:
    certificate_group_id: str
    required_q: int
    trusted_witness_count: int
    trusted_failure_domain_count: int
    invalidated_signature_count: int


@dataclass(frozen=True)
class KeyLifecycleReplaySummary:
    lifecycle_event_count: int
    final_head_hash: str
    cutoff_registry_sequence: int
    boundary_count: int
    invalidated_signature_count: int
    quorum_results: tuple[HistoricalQuorumResult, ...]
    external_completeness_proven: bool


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise KeyLifecycleError(code)


def _obj(resolver: EvidenceResolverV02, content_hash: str, schema: str) -> Mapping[str, Any]:
    resolved = resolver.resolve(content_hash, expected_schema=schema)
    if resolved.parsed_json is None:
        raise KeyLifecycleError(f"EXPECTED_PROTOCOL_JSON:{content_hash}")
    return resolved.parsed_json


def key_lifecycle_genesis_hash(experiment_id: str) -> str:
    _require(isinstance(experiment_id, str) and experiment_id, "KEY_LIFECYCLE_EXPERIMENT_ID_INVALID")
    try:
        encoded = experiment_id.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise KeyLifecycleError("KEY_LIFECYCLE_EXPERIMENT_ID_UTF8_INVALID") from exc
    return hashlib.sha256(b"AIFC:KEY_LIFECYCLE_GENESIS:v1\x00" + encoded).hexdigest()


def _find_witness_key(registry: Mapping[str, Any], witness_id: str, key_id: str) -> Mapping[str, Any]:
    witnesses = registry.get("witnesses")
    _require(isinstance(witnesses, list), "KEY_LIFECYCLE_REGISTRY_WITNESSES_INVALID")
    wm = [w for w in witnesses if isinstance(w, Mapping) and w.get("witness_id") == witness_id]
    _require(len(wm) == 1, "KEY_LIFECYCLE_WITNESS_NOT_UNIQUE")
    keys = wm[0].get("keys")
    _require(isinstance(keys, list), "KEY_LIFECYCLE_KEY_SET_INVALID")
    km = [k for k in keys if isinstance(k, Mapping) and k.get("key_id") == key_id]
    _require(len(km) == 1, "KEY_LIFECYCLE_KEY_NOT_UNIQUE")
    return km[0]


def _failure_domain(registry: Mapping[str, Any], witness_id: str) -> str:
    witnesses = registry.get("witnesses")
    _require(isinstance(witnesses, list), "KEY_LIFECYCLE_REGISTRY_WITNESSES_INVALID")
    wm = [w for w in witnesses if isinstance(w, Mapping) and w.get("witness_id") == witness_id]
    _require(len(wm) == 1, "KEY_LIFECYCLE_WITNESS_NOT_UNIQUE")
    domain = wm[0].get("failure_domain")
    _require(isinstance(domain, str) and domain, "KEY_LIFECYCLE_FAILURE_DOMAIN_INVALID")
    return domain


def _event_boundary(event: Mapping[str, Any]) -> int:
    event_type = event.get("event_type")
    recorded = event.get("recorded_against_registry_sequence")
    effective = event.get("effective_from_registry_sequence")
    basis = event.get("boundary_basis")
    _require(isinstance(recorded, int) and recorded >= 0, "KEY_LIFECYCLE_RECORDED_SEQUENCE_INVALID")
    _require(isinstance(effective, int) and effective >= 0, "KEY_LIFECYCLE_EFFECTIVE_SEQUENCE_INVALID")

    if event_type == "COMPROMISE_DISCOVERED":
        _require(basis in {"EXACT_KNOWN", "CONSERVATIVE_LOWER_BOUND", "UNKNOWN_FROM_GENESIS"}, "COMPROMISE_BOUNDARY_BASIS_INVALID")
        _require(effective <= recorded, "COMPROMISE_BOUNDARY_AFTER_DISCOVERY_SEQUENCE")
        if basis == "UNKNOWN_FROM_GENESIS":
            _require(effective == 0, "UNKNOWN_COMPROMISE_BOUNDARY_MUST_START_AT_ZERO")
        return effective

    _require(event_type in {"REVOCATION_DECLARED", "RETIREMENT_DECLARED"}, "KEY_LIFECYCLE_EVENT_TYPE_INVALID")
    _require(basis == "PROSPECTIVE_DECLARATION", "PROSPECTIVE_KEY_EVENT_BOUNDARY_BASIS_INVALID")
    _require(effective >= recorded, "PROSPECTIVE_KEY_EVENT_RETROACTIVE_WITHOUT_COMPROMISE")
    return effective


def _replay_ledger(
    manifest: Mapping[str, Any],
    resolver: EvidenceResolverV02,
) -> tuple[Mapping[str, Any], tuple[KeyBoundary, ...]]:
    experiment_id = manifest.get("experiment_id")
    _require(isinstance(experiment_id, str) and experiment_id, "KEY_LIFECYCLE_EXPERIMENT_ID_INVALID")

    plan_hash = manifest.get("experiment_plan_hash")
    _require(isinstance(plan_hash, str), "EXPERIMENT_PLAN_HASH_MISSING")
    plan = _obj(resolver, plan_hash, "AIFC/experiment-plan/v1")
    _require(plan.get("experiment_id") == experiment_id, "KEY_LIFECYCLE_PLAN_EXPERIMENT_REBINDING")

    policy_hash = plan.get("key_lifecycle_policy_hash")
    _require(isinstance(policy_hash, str), "KEY_LIFECYCLE_POLICY_HASH_MISSING")
    policy = _obj(resolver, policy_hash, "AIFC/key-lifecycle-policy/v1")
    _require(policy.get("experiment_id") == experiment_id, "KEY_LIFECYCLE_POLICY_EXPERIMENT_REBINDING")
    _require(policy.get("policy_id") == "AIFC-KEY-LIFECYCLE-POLICY-V1", "KEY_LIFECYCLE_POLICY_ID_MISMATCH")
    _require(policy.get("frozen_before_first_created") is True, "KEY_LIFECYCLE_POLICY_NOT_FROZEN")
    _require(policy.get("external_completeness_required") is True, "KEY_LIFECYCLE_POLICY_MUST_REQUIRE_EXTERNAL_COMPLETENESS")

    ledger_hash = manifest.get("key_lifecycle_ledger_hash")
    _require(isinstance(ledger_hash, str), "KEY_LIFECYCLE_LEDGER_HASH_MISSING")
    ledger = _obj(resolver, ledger_hash, "AIFC/key-lifecycle-ledger/v1")
    _require(ledger.get("experiment_id") == experiment_id, "KEY_LIFECYCLE_LEDGER_EXPERIMENT_REBINDING")
    _require(ledger.get("policy_hash") == policy_hash, "KEY_LIFECYCLE_LEDGER_POLICY_REBINDING")
    _require(ledger.get("completeness_status") == "LOCAL_CHAIN_REPLAYED_EXTERNAL_COMPLETENESS_NOT_PROVEN", "KEY_LIFECYCLE_LEDGER_COMPLETENESS_STATUS_INVALID")

    bundle_hash = manifest.get("evidence_bundle_hash")
    _require(isinstance(bundle_hash, str), "EVIDENCE_BUNDLE_HASH_MISSING")
    bundle = _obj(resolver, bundle_hash, "AIFC/evidence-bundle/v1")
    _require(bundle.get("experiment_id") == experiment_id, "KEY_LIFECYCLE_BUNDLE_EXPERIMENT_REBINDING")
    _require(bundle.get("key_lifecycle_ledger_hash") == ledger_hash, "KEY_LIFECYCLE_BUNDLE_REBINDING")

    cutoff_hash = ledger.get("cutoff_registry_hash")
    cutoff_sequence = ledger.get("cutoff_registry_sequence")
    _require(isinstance(cutoff_hash, str), "KEY_LIFECYCLE_CUTOFF_REGISTRY_HASH_INVALID")
    _require(isinstance(cutoff_sequence, int) and cutoff_sequence >= 0, "KEY_LIFECYCLE_CUTOFF_SEQUENCE_INVALID")
    cutoff_registry = _obj(resolver, cutoff_hash, "AIFC/witness-registry/v1")
    _require(cutoff_registry.get("experiment_id") == experiment_id, "KEY_LIFECYCLE_CUTOFF_REGISTRY_EXPERIMENT_REBINDING")
    _require(cutoff_registry.get("registry_sequence") == cutoff_sequence, "KEY_LIFECYCLE_CUTOFF_SEQUENCE_REBINDING")

    event_hashes = ledger.get("event_hashes")
    event_count = ledger.get("event_count")
    _require(isinstance(event_hashes, list), "KEY_LIFECYCLE_EVENT_HASH_LIST_INVALID")
    _require(isinstance(event_count, int) and event_count == len(event_hashes), "KEY_LIFECYCLE_EVENT_COUNT_REBINDING")

    expected_previous = key_lifecycle_genesis_hash(experiment_id)
    boundaries: list[KeyBoundary] = []
    for expected_index, event_hash in enumerate(event_hashes):
        _require(isinstance(event_hash, str), "KEY_LIFECYCLE_EVENT_HASH_INVALID")
        event = _obj(resolver, event_hash, "AIFC/key-lifecycle-event/v1")
        _require(event.get("experiment_id") == experiment_id, "KEY_LIFECYCLE_EVENT_EXPERIMENT_REBINDING")
        _require(event.get("event_index") == expected_index, "KEY_LIFECYCLE_EVENT_INDEX_DISCONTINUITY")
        _require(event.get("previous_event_hash") == expected_previous, "KEY_LIFECYCLE_CHAIN_BREAK")

        subject_hash = event.get("subject_registry_hash")
        recorded_hash = event.get("recorded_against_registry_hash")
        _require(isinstance(subject_hash, str), "KEY_LIFECYCLE_SUBJECT_REGISTRY_HASH_INVALID")
        _require(isinstance(recorded_hash, str), "KEY_LIFECYCLE_RECORDED_REGISTRY_HASH_INVALID")
        subject = _obj(resolver, subject_hash, "AIFC/witness-registry/v1")
        recorded = _obj(resolver, recorded_hash, "AIFC/witness-registry/v1")
        _require(subject.get("experiment_id") == experiment_id, "KEY_LIFECYCLE_SUBJECT_REGISTRY_EXPERIMENT_REBINDING")
        _require(recorded.get("experiment_id") == experiment_id, "KEY_LIFECYCLE_RECORDED_REGISTRY_EXPERIMENT_REBINDING")
        _require(recorded.get("registry_sequence") == event.get("recorded_against_registry_sequence"), "KEY_LIFECYCLE_RECORDED_SEQUENCE_REBINDING")
        _require(event.get("recorded_against_registry_sequence") <= cutoff_sequence, "KEY_LIFECYCLE_EVENT_AFTER_LEDGER_CUTOFF")

        witness_id = event.get("witness_id")
        key_id = event.get("key_id")
        _require(isinstance(witness_id, str) and witness_id, "KEY_LIFECYCLE_EVENT_WITNESS_INVALID")
        _require(isinstance(key_id, str) and key_id, "KEY_LIFECYCLE_EVENT_KEY_INVALID")
        _find_witness_key(subject, witness_id, key_id)

        evidence_hashes = event.get("evidence_hashes")
        _require(isinstance(evidence_hashes, list) and evidence_hashes, "KEY_LIFECYCLE_EVENT_EVIDENCE_MISSING")
        for evidence_hash in evidence_hashes:
            _require(isinstance(evidence_hash, str), "KEY_LIFECYCLE_EVENT_EVIDENCE_HASH_INVALID")
            resolver.resolve(evidence_hash)

        effective = _event_boundary(event)
        boundaries.append(KeyBoundary(
            witness_id=witness_id,
            key_id=key_id,
            effective_from_registry_sequence=effective,
            event_type=str(event.get("event_type")),
            boundary_basis=str(event.get("boundary_basis")),
            event_hash=event_hash,
            event_index=expected_index,
        ))
        expected_previous = event_hash

    _require(ledger.get("final_head_hash") == expected_previous, "KEY_LIFECYCLE_FINAL_HEAD_REBINDING")
    return ledger, tuple(boundaries)


def _effective_boundary_map(boundaries: tuple[KeyBoundary, ...]) -> dict[tuple[str, str], KeyBoundary]:
    effective: dict[tuple[str, str], KeyBoundary] = {}
    for boundary in boundaries:
        key = (boundary.witness_id, boundary.key_id)
        current = effective.get(key)
        if current is None or boundary.effective_from_registry_sequence < current.effective_from_registry_sequence:
            effective[key] = boundary
    return effective


def replay_historical_key_lifecycle(
    manifest: Mapping[str, Any],
    resolver: EvidenceResolverV02,
    signatures: SignaturePreimageReplaySummary,
) -> KeyLifecycleReplaySummary:
    ledger, boundaries = _replay_ledger(manifest, resolver)
    effective = _effective_boundary_map(boundaries)
    cutoff_sequence = int(ledger["cutoff_registry_sequence"])

    groups: dict[str, list[SignaturePreimageMaterial]] = {}
    invalidated: set[int] = set()
    for index, material in enumerate(signatures.materials):
        _require(material.certificate_group_id != "", "KEY_LIFECYCLE_SIGNATURE_GROUP_MISSING")
        _require(material.required_q >= 1, "KEY_LIFECYCLE_SIGNATURE_Q_INVALID")
        _require(material.registry_sequence <= cutoff_sequence, "KEY_LIFECYCLE_CUTOFF_BEFORE_SIGNATURE_SEQUENCE")
        groups.setdefault(material.certificate_group_id, []).append(material)
        boundary = effective.get((material.witness_id, material.key_id))
        if boundary is not None and material.registry_sequence >= boundary.effective_from_registry_sequence:
            invalidated.add(index)

    quorum_results: list[HistoricalQuorumResult] = []
    for group_id, materials in groups.items():
        q_values = {m.required_q for m in materials}
        registry_hashes = {m.registry_hash for m in materials}
        registry_sequences = {m.registry_sequence for m in materials}
        _require(len(q_values) == 1, f"HISTORICAL_QUORUM_Q_REBINDING:{group_id}")
        _require(len(registry_hashes) == 1, f"HISTORICAL_QUORUM_REGISTRY_REBINDING:{group_id}")
        _require(len(registry_sequences) == 1, f"HISTORICAL_QUORUM_SEQUENCE_REBINDING:{group_id}")
        required_q = next(iter(q_values))
        registry_hash = next(iter(registry_hashes))
        registry = _obj(resolver, registry_hash, "AIFC/witness-registry/v1")

        trusted_witnesses: set[str] = set()
        trusted_domains: set[str] = set()
        invalidated_count = 0
        for material in materials:
            index = signatures.materials.index(material)
            if index in invalidated:
                invalidated_count += 1
                continue
            trusted_witnesses.add(material.witness_id)
            trusted_domains.add(_failure_domain(registry, material.witness_id))

        result = HistoricalQuorumResult(
            certificate_group_id=group_id,
            required_q=required_q,
            trusted_witness_count=len(trusted_witnesses),
            trusted_failure_domain_count=len(trusted_domains),
            invalidated_signature_count=invalidated_count,
        )
        quorum_results.append(result)
        _require(
            result.trusted_witness_count >= required_q and result.trusted_failure_domain_count >= required_q,
            f"HISTORICAL_QUORUM_COLLAPSE:{group_id}:witnesses={result.trusted_witness_count}:domains={result.trusted_failure_domain_count}:q={required_q}",
        )

    return KeyLifecycleReplaySummary(
        lifecycle_event_count=int(ledger["event_count"]),
        final_head_hash=str(ledger["final_head_hash"]),
        cutoff_registry_sequence=cutoff_sequence,
        boundary_count=len(effective),
        invalidated_signature_count=len(invalidated),
        quorum_results=tuple(quorum_results),
        external_completeness_proven=False,
    )
