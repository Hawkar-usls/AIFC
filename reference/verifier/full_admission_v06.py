#!/usr/bin/env python3
"""Authoritative AIFC Verifier A v0.6 Ed25519 cryptographic admission path."""
from __future__ import annotations

from typing import Any, Mapping

from ed25519_admission import Ed25519AdmissionError, replay_ed25519_signatures
from full_admission_v03 import verify_replay_manifest as verify_v03
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
        "verifier_version": "0.6.0-ed25519-crypto",
        "evidence_bundle_hash": bundle_hash if isinstance(bundle_hash, str) and len(bundle_hash) == 64 else "0" * 64,
        "gate_results": {
            "SIGNATURE_PREIMAGE_POLICY_VALID": "FAIL",
            "SIGNATURE_PREIMAGE_REPLAY": "FAIL",
            "CANONICAL_ED25519_ENCODING": "FAIL",
            "REGISTRY_LOCAL_KEY_ELIGIBILITY": "FAIL",
            "ED25519_SIGNATURE_CRYPTO": "FAIL",
            "HISTORICAL_KEY_LIFECYCLE": "BLOCKED",
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

    result = verify_v03(manifest, resolver)
    gates = result.setdefault("gate_results", {})
    gates["SIGNATURE_PREIMAGE_POLICY_VALID"] = "PASS"
    gates["SIGNATURE_PREIMAGE_REPLAY"] = "PASS"
    gates["CANONICAL_ED25519_ENCODING"] = "PASS"
    gates["REGISTRY_LOCAL_KEY_ELIGIBILITY"] = "PASS"
    gates["ED25519_SIGNATURE_CRYPTO"] = "PASS"
    gates["HISTORICAL_KEY_LIFECYCLE"] = "BLOCKED"
    result["verifier_version"] = "0.6.0-ed25519-crypto"
    result["crypto_backend"] = {
        "backend_id": "OPENSSL_PKEYUTL_ED25519_V1",
        "version_line": crypto_summary.backend_version,
        "executable_sha256": crypto_summary.backend_executable_sha256,
    }

    if crypto_summary.verified_count != crypto_summary.receipt_count:
        gates["ED25519_SIGNATURE_CRYPTO"] = "FAIL"
        result["terminal_grade"] = "INVALIDATED_EVIDENCE"
        result.setdefault("failure_codes", []).append("ED25519_VERIFIED_COUNT_MISMATCH")
        return result

    # Registry-local crypto validity is not historical compromise safety and is not
    # freshness. Until those later gates are implemented, no forward-null outcome
    # is scientifically admitted by v0.6.
    if result.get("terminal_grade") in {
        "FORWARD_NULL_CONSISTENT_MISS",
        "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE",
    }:
        result["terminal_grade"] = "NOT_ADMITTED"
        result.setdefault("failure_codes", []).append("HISTORICAL_KEY_LIFECYCLE:BLOCKED")

    return result
