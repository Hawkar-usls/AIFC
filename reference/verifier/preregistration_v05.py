#!/usr/bin/env python3
"""AIFC v0.5 strongest-grade signature-preimage preregistration layer.

Legacy v0.2 preregistration remains readable at its historical entry point. This
layer composes it and additionally requires the frozen Experiment Plan to bind the
single normative AIFC v1 signature-preimage policy before first CREATED.
"""
from __future__ import annotations

from typing import Any, Mapping

from canonical import CanonicalizationError
from preregistration_v02 import verify_plan_preregistration
from resolver import EvidenceResolutionError
from resolver_v02 import EvidenceResolverV02
from signature_preimage_v05 import SignaturePreimageError, assert_normative_policy


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
            "EXPERIMENT_PLAN_PREREGISTRATION": "PASS",
            "SIGNATURE_PREIMAGE_POLICY_VALID": "FAIL",
            "SIGNATURE_PREIMAGE_PROFILE_REPLAY": "BLOCKED",
        },
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": [f"{code}:{detail}" if detail else code],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def _obj(resolver: EvidenceResolverV02, content_hash: str, schema: str) -> Mapping[str, Any]:
    resolved = resolver.resolve(content_hash, expected_schema=schema)
    if resolved.parsed_json is None:
        raise EvidenceResolutionError(f"EXPECTED_PROTOCOL_JSON:{content_hash}")
    return resolved.parsed_json


def verify_signature_preimage_preregistration(
    manifest: Mapping[str, Any], resolver: EvidenceResolverV02
) -> dict[str, Any] | None:
    base = verify_plan_preregistration(manifest, resolver)
    if base is not None:
        return base

    try:
        experiment_id = manifest.get("experiment_id")
        plan_hash = manifest.get("experiment_plan_hash")
        if not isinstance(experiment_id, str) or not experiment_id:
            return _invalid(manifest, "EXPERIMENT_ID_INVALID")
        if not isinstance(plan_hash, str) or len(plan_hash) != 64:
            return _invalid(manifest, "EXPERIMENT_PLAN_HASH_INVALID")

        plan = _obj(resolver, plan_hash, "AIFC/experiment-plan/v1")
        signature_policy_hash = plan.get("signature_preimage_policy_hash")
        if not isinstance(signature_policy_hash, str) or len(signature_policy_hash) != 64:
            return _invalid(manifest, "SIGNATURE_PREIMAGE_POLICY_REQUIRED_FOR_V05")

        policy = _obj(resolver, signature_policy_hash, "AIFC/signature-preimage-policy/v1")
        if policy.get("experiment_id") != experiment_id:
            return _invalid(manifest, "SIGNATURE_PREIMAGE_POLICY_EXPERIMENT_REBINDING")
        if policy.get("frozen_before_first_created") is not True:
            return _invalid(manifest, "SIGNATURE_PREIMAGE_POLICY_NOT_FROZEN")
        try:
            assert_normative_policy(policy, experiment_id)
        except SignaturePreimageError as exc:
            return _invalid(manifest, "SIGNATURE_PREIMAGE_POLICY_NON_NORMATIVE", str(exc))
        return None
    except (EvidenceResolutionError, CanonicalizationError, SignaturePreimageError, KeyError, TypeError, ValueError) as exc:
        return _invalid(manifest, "SIGNATURE_PREIMAGE_POLICY_EVIDENCE_FAILURE", str(exc))
