#!/usr/bin/env python3
"""Authoritative AIFC Verifier A v0.7 historical key-lifecycle path."""
from __future__ import annotations

from typing import Any, Mapping

from ed25519_admission import Ed25519AdmissionError, replay_ed25519_signatures
from full_admission_v03 import verify_replay_manifest as verify_v03
from key_lifecycle import KeyLifecycleError, replay_historical_key_lifecycle
from resolver import EvidenceResolutionError
from resolver_v02 import EvidenceResolverV02
from signature_policy_admission import SignaturePolicyAdmissionError, replay_signature_preimages
from signature_preimage import SignaturePreimageError


def _invalid(manifest: Mapping[str, Any], code: str, detail: str = "") -> dict[str, Any]:
    experiment_id = manifest.get("experiment_id")
    trial_index = manifest.get("subject_trial_index")
    bundle_hash = manifest.get("evidence_bundle_hash")
    return {
        "schema": "AIFC/verifier-result/v1",
        "experiment_id": experiment_id if isinstance(experiment_id, str) and experiment_id else "UNKNOWN",
        "trial_index": trial_index if isinstance(trial_index, int) and trial_index >= 1 else 1,
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.7.0-key-lifecycle",
        "evidence_bundle_hash": bundle_hash if isinstance(bundle_hash, str) and len(bundle_hash) == 64 else "0" * 64,
        "gate_results": {
            "SIGNATURE_PREIMAGE_POLICY_VALID": "FAIL",
            "SIGNATURE_PREIMAGE_REPLAY": "FAIL",
            "CANONICAL_ED25519_ENCODING": "FAIL",
            "REGISTRY_LOCAL_KEY_ELIGIBILITY": "FAIL",
            "ED25519_SIGNATURE_CRYPTO": "FAIL",
            "KEY_LIFECYCLE_POLICY_VALID": "FAIL",
            "KEY_LIFECYCLE_LEDGER_REPLAY": "FAIL",
            "RETROACTIVE_KEY_QUORUM_REEVALUATION": "FAIL",
            "HISTORICAL_KEY_LIFECYCLE": "BLOCKED",
            "EXTERNAL_FRESHNESS_REPLAY": "BLOCKED",
        },
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": [f"{code}:{detail}" if detail else code],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def verify_replay_manifest(manifest: Mapping[str, Any], resolver: EvidenceResolverV02) -> dict[str, Any]:
    try:
        preimage_summary = replay_signature_preimages(manifest, resolver)
    except (SignaturePolicyAdmissionError, SignaturePreimageError, EvidenceResolutionError, KeyError, TypeError, ValueError) as exc:
        return _invalid(manifest, "SIGNATURE_PREIMAGE_REPLAY_REJECTED", str(exc))

    try:
        crypto_summary = replay_ed25519_signatures(preimage_summary, resolver)
    except (Ed25519AdmissionError, EvidenceResolutionError, KeyError, TypeError, ValueError) as exc:
        result = _invalid(manifest, "ED25519_SIGNATURE_CRYPTO_REJECTED", str(exc))
        result["gate_results"]["SIGNATURE_PREIMAGE_POLICY_VALID"] = "PASS"
        result["gate_results"]["SIGNATURE_PREIMAGE_REPLAY"] = "PASS"
        result["gate_results"]["CANONICAL_ED25519_ENCODING"] = "PASS"
        return result

    try:
        lifecycle_summary = replay_historical_key_lifecycle(manifest, resolver, preimage_summary)
    except (KeyLifecycleError, EvidenceResolutionError, KeyError, TypeError, ValueError) as exc:
        result = _invalid(manifest, "HISTORICAL_KEY_LIFECYCLE_REJECTED", str(exc))
        gates = result["gate_results"]
        gates["SIGNATURE_PREIMAGE_POLICY_VALID"] = "PASS"
        gates["SIGNATURE_PREIMAGE_REPLAY"] = "PASS"
        gates["CANONICAL_ED25519_ENCODING"] = "PASS"
        gates["REGISTRY_LOCAL_KEY_ELIGIBILITY"] = "PASS"
        gates["ED25519_SIGNATURE_CRYPTO"] = "PASS"
        gates["KEY_LIFECYCLE_POLICY_VALID"] = "PASS"
        return result

    result = verify_v03(manifest, resolver)
    gates = result.setdefault("gate_results", {})
    gates["SIGNATURE_PREIMAGE_POLICY_VALID"] = "PASS"
    gates["SIGNATURE_PREIMAGE_REPLAY"] = "PASS"
    gates["CANONICAL_ED25519_ENCODING"] = "PASS"
    gates["REGISTRY_LOCAL_KEY_ELIGIBILITY"] = "PASS"
    gates["ED25519_SIGNATURE_CRYPTO"] = "PASS"
    gates["KEY_LIFECYCLE_POLICY_VALID"] = "PASS"
    gates["KEY_LIFECYCLE_LEDGER_REPLAY"] = "PASS"
    gates["RETROACTIVE_KEY_QUORUM_REEVALUATION"] = "PASS"
    gates["HISTORICAL_KEY_LIFECYCLE"] = "BLOCKED"
    gates["EXTERNAL_FRESHNESS_REPLAY"] = "BLOCKED"
    result["verifier_version"] = "0.7.0-key-lifecycle"
    result["crypto_backend"] = {
        "backend_id": "OPENSSL_PKEYUTL_ED25519_V1",
        "version_line": crypto_summary.backend_version,
        "executable_sha256": crypto_summary.backend_executable_sha256,
    }
    result["key_lifecycle_summary"] = {
        "lifecycle_event_count": lifecycle_summary.lifecycle_event_count,
        "boundary_count": lifecycle_summary.boundary_count,
        "invalidated_signature_count": lifecycle_summary.invalidated_signature_count,
        "quorum_group_count": len(lifecycle_summary.quorum_results),
        "cutoff_registry_sequence": lifecycle_summary.cutoff_registry_sequence,
        "final_head_hash": lifecycle_summary.final_head_hash,
        "external_completeness_proven": False,
    }

    if lifecycle_summary.external_completeness_proven:
        # v0.7 has no code path that may establish this. Treat any unexpected future
        # change as fail-closed until the external freshness gate is versioned.
        gates["HISTORICAL_KEY_LIFECYCLE"] = "FAIL"
        result["terminal_grade"] = "INVALIDATED_EVIDENCE"
        result.setdefault("failure_codes", []).append("UNVERSIONED_EXTERNAL_KEY_LIFECYCLE_COMPLETENESS")
        return result

    # A locally clean/surviving lifecycle chain cannot establish absence of omitted
    # compromise events. Any forward-null admitted result is therefore capped.
    if result.get("terminal_grade") in {
        "FORWARD_NULL_CONSISTENT_MISS",
        "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE",
    }:
        result["terminal_grade"] = "NOT_ADMITTED"
        result.setdefault("failure_codes", []).append("HISTORICAL_KEY_LIFECYCLE:BLOCKED_EXTERNAL_COMPLETENESS")

    return result
