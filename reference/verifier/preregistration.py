#!/usr/bin/env python3
"""Experiment-plan preregistration gate for AIFC Verifier A v0.2.

The plan is experiment-scoped and must be externally certified before the first
trial slot exists. This module verifies the directed structural chain:

    EXPERIMENT_PLAN
      -> experiment-plan quorum
      -> first CREATED.prerequisite_certificate_hash
      -> trial-scoped CREATED quorum later in the replay engine

Ed25519 signature cryptography remains a separate blocked gate in v0.2.
"""
from __future__ import annotations

from typing import Any, Mapping

from canonical import CanonicalizationError, protocol_hash
from replay import _active_key, _obj, _validate_registry_object, experiment_genesis_hash
from resolver import EvidenceResolutionError, EvidenceResolver


def _invalid(manifest: Mapping[str, Any], code: str, detail: str = "") -> dict[str, Any]:
    experiment_id = manifest.get("experiment_id")
    trial_index = manifest.get("subject_trial_index")
    bundle_hash = manifest.get("evidence_bundle_hash")
    return {
        "schema": "AIFC/verifier-result/v1",
        "experiment_id": experiment_id if isinstance(experiment_id, str) and experiment_id else "UNKNOWN",
        "trial_index": trial_index if isinstance(trial_index, int) and trial_index >= 1 else 1,
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.2.0-replay",
        "evidence_bundle_hash": bundle_hash if isinstance(bundle_hash, str) and len(bundle_hash) == 64 else "0" * 64,
        "gate_results": {"EXPERIMENT_PLAN_PREREGISTRATION": "FAIL"},
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": [f"{code}:{detail}" if detail else code],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def verify_plan_preregistration(manifest: Mapping[str, Any], resolver: EvidenceResolver) -> dict[str, Any] | None:
    """Return None on structural PASS, otherwise a fail-closed verifier-result."""
    try:
        experiment_id = manifest.get("experiment_id")
        if not isinstance(experiment_id, str) or not experiment_id:
            return _invalid(manifest, "EXPERIMENT_ID_INVALID")

        plan_hash = manifest.get("experiment_plan_hash")
        quorum_hash = manifest.get("experiment_plan_quorum_certificate_hash")
        if not isinstance(plan_hash, str) or len(plan_hash) != 64:
            return _invalid(manifest, "EXPERIMENT_PLAN_HASH_INVALID")
        if not isinstance(quorum_hash, str) or len(quorum_hash) != 64:
            return _invalid(manifest, "EXPERIMENT_PLAN_QUORUM_HASH_INVALID")

        plan = _obj(resolver, plan_hash, "AIFC/experiment-plan/v1")
        if plan.get("experiment_id") != experiment_id:
            return _invalid(manifest, "EXPERIMENT_PLAN_EXPERIMENT_REBINDING")
        if plan.get("frozen_before_first_created") is not True:
            return _invalid(manifest, "EXPERIMENT_PLAN_NOT_FROZEN")

        registry_hash = plan.get("initial_witness_registry_hash")
        if not isinstance(registry_hash, str) or len(registry_hash) != 64:
            return _invalid(manifest, "INITIAL_REGISTRY_HASH_INVALID")
        registry = _obj(resolver, registry_hash, "AIFC/witness-registry/v1")
        members = _validate_registry_object(registry, registry_hash, experiment_id)
        if registry.get("registry_sequence") != 0:
            return _invalid(manifest, "EXPERIMENT_PLAN_REQUIRES_INITIAL_REGISTRY_SEQUENCE_ZERO")

        quorum = _obj(resolver, quorum_hash, "AIFC/experiment-plan-quorum/v1")
        if quorum.get("experiment_id") != experiment_id:
            return _invalid(manifest, "PLAN_QUORUM_EXPERIMENT_REBINDING")
        if quorum.get("logical_position") != "EXPERIMENT_PLAN_FROZEN":
            return _invalid(manifest, "PLAN_QUORUM_LOGICAL_POSITION_INVALID")
        if quorum.get("content_hash") != plan_hash:
            return _invalid(manifest, "PLAN_QUORUM_CONTENT_REBINDING")
        if quorum.get("registry_hash") != registry_hash:
            return _invalid(manifest, "PLAN_QUORUM_REGISTRY_REBINDING")

        fault = registry.get("fault_model", {})
        expected_fault = (fault.get("n"), fault.get("f"), fault.get("q"))
        if (quorum.get("n"), quorum.get("f"), quorum.get("q")) != expected_fault:
            return _invalid(manifest, "PLAN_QUORUM_FAULT_MODEL_REBINDING")
        n, f, q = expected_fault
        if not all(isinstance(x, int) for x in expected_fault) or not (n >= 1 and 0 <= f < n and 1 <= q <= n and 2 * q > n + f):
            return _invalid(manifest, "PLAN_QUORUM_FAULT_MODEL_UNSAFE")

        receipts = quorum.get("receipts")
        if not isinstance(receipts, list) or len(receipts) < q:
            return _invalid(manifest, "PLAN_QUORUM_RECEIPTS_INSUFFICIENT")
        seen_ids: set[str] = set()
        seen_domains: set[str] = set()
        for receipt in receipts:
            if not isinstance(receipt, Mapping) or receipt.get("schema") != "AIFC/experiment-plan-receipt/v1":
                return _invalid(manifest, "PLAN_RECEIPT_SCHEMA_MISMATCH")
            if receipt.get("experiment_id") != experiment_id:
                return _invalid(manifest, "PLAN_RECEIPT_EXPERIMENT_REBINDING")
            if receipt.get("logical_position") != "EXPERIMENT_PLAN_FROZEN":
                return _invalid(manifest, "PLAN_RECEIPT_POSITION_REBINDING")
            if receipt.get("content_hash") != plan_hash:
                return _invalid(manifest, "PLAN_RECEIPT_CONTENT_REBINDING")
            if receipt.get("registry_hash") != registry_hash:
                return _invalid(manifest, "PLAN_RECEIPT_REGISTRY_REBINDING")
            wid = receipt.get("witness_id")
            if not isinstance(wid, str) or wid not in members:
                return _invalid(manifest, "PLAN_RECEIPT_WITNESS_NOT_IN_REGISTRY", str(wid))
            if wid in seen_ids:
                return _invalid(manifest, "PLAN_RECEIPT_DUPLICATE_WITNESS", wid)
            witness = members[wid]
            if not _active_key(witness, str(receipt.get("key_id")), 0):
                return _invalid(manifest, "PLAN_RECEIPT_KEY_NOT_ACTIVE", wid)
            seen_ids.add(wid)
            seen_domains.add(str(witness.get("failure_domain")))
        if len(seen_ids) < q:
            return _invalid(manifest, "PLAN_QUORUM_DISTINCT_WITNESS_COUNT_INSUFFICIENT")
        if len(seen_domains) < q:
            return _invalid(manifest, "PLAN_QUORUM_SAME_FAILURE_DOMAIN_SYBIL")

        ledger_hashes = manifest.get("ledger_event_hashes")
        if not isinstance(ledger_hashes, list) or not ledger_hashes:
            return _invalid(manifest, "LEDGER_HASH_LIST_INVALID")
        first = _obj(resolver, str(ledger_hashes[0]), "AIFC/trial-ledger-event/v1")
        if first.get("event_index") != 0 or first.get("state_from") is not None or first.get("state_to") != "CREATED":
            return _invalid(manifest, "FIRST_LEDGER_EVENT_NOT_CREATED")
        if first.get("previous_event_hash") != experiment_genesis_hash(experiment_id):
            return _invalid(manifest, "FIRST_CREATED_GENESIS_PREDECESSOR_MISMATCH")
        if first.get("payload_hash") != plan_hash:
            return _invalid(manifest, "FIRST_CREATED_PLAN_HASH_REBINDING")
        if first.get("prerequisite_certificate_hash") != quorum_hash:
            return _invalid(manifest, "EXPERIMENT_PLAN_NOT_CERTIFIED_BEFORE_CREATED")

        # Hash recomputation is implicit in resolver; this extra equality documents the contract.
        if protocol_hash(quorum) != quorum_hash:
            return _invalid(manifest, "PLAN_QUORUM_HASH_RECOMPUTE_MISMATCH")
        return None
    except (EvidenceResolutionError, CanonicalizationError, KeyError, TypeError, ValueError) as exc:
        return _invalid(manifest, "EXPERIMENT_PLAN_PREREGISTRATION_EVIDENCE_FAILURE", str(exc))
