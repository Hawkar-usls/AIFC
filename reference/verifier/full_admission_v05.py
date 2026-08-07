#!/usr/bin/env python3
"""Authoritative AIFC Verifier A v0.5 signature-preimage admission path."""
from __future__ import annotations

from typing import Any, Mapping

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
        "verifier_version": "0.5.0-signature-preimage",
        "evidence_bundle_hash": bundle_hash if isinstance(bundle_hash, str) and len(bundle_hash) == 64 else "0" * 64,
        "gate_results": {
            "SIGNATURE_PREIMAGE_POLICY_VALID": "FAIL",
            "SIGNATURE_PREIMAGE_REPLAY": "FAIL",
            "CANONICAL_ED25519_ENCODING": "FAIL",
            "ED25519_SIGNATURE_CRYPTO": "BLOCKED",
        },
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": [f"{code}:{detail}" if detail else code],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def verify_replay_manifest(manifest: Mapping[str, Any], resolver: EvidenceResolverV02) -> dict[str, Any]:
    try:
        summary = replay_signature_preimages(manifest, resolver)
    except (SignaturePolicyAdmissionError, SignaturePreimageError, EvidenceResolutionError, KeyError, TypeError, ValueError) as exc:
        return _invalid(manifest, "SIGNATURE_PREIMAGE_REPLAY_REJECTED", str(exc))

    result = verify_v03(manifest, resolver)
    gates = result.setdefault("gate_results", {})
    if result.get("terminal_grade") != "INVALIDATED_EVIDENCE":
        gates["SIGNATURE_PREIMAGE_POLICY_VALID"] = "PASS"
        gates["SIGNATURE_PREIMAGE_REPLAY"] = "PASS"
        gates["CANONICAL_ED25519_ENCODING"] = "PASS"
    else:
        gates.setdefault("SIGNATURE_PREIMAGE_POLICY_VALID", "PASS")
        gates.setdefault("SIGNATURE_PREIMAGE_REPLAY", "PASS")
        gates.setdefault("CANONICAL_ED25519_ENCODING", "PASS")

    # The message is frozen and replayable, but no signature is trusted yet.
    gates["ED25519_SIGNATURE_CRYPTO"] = "BLOCKED"
    result["verifier_version"] = "0.5.0-signature-preimage"

    # Keep receipt-count evidence in a deterministic failure-code-style diagnostic only
    # when no receipts were found; a valid replay package is expected to carry receipts.
    if summary.receipt_count == 0:
        result.setdefault("failure_codes", []).append("SIGNATURE_PREIMAGE_REPLAY:NO_RECEIPTS")
        gates["SIGNATURE_PREIMAGE_REPLAY"] = "FAIL"
        result["terminal_grade"] = "INVALIDATED_EVIDENCE"

    # Crypto is mandatory for any admitted forward-null conclusion.
    if result.get("terminal_grade") in {"FORWARD_NULL_CONSISTENT_MISS", "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE"}:
        result["terminal_grade"] = "NOT_ADMITTED"
        result.setdefault("failure_codes", []).append("ED25519_SIGNATURE_CRYPTO:BLOCKED")

    return result
