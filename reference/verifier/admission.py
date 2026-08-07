#!/usr/bin/env python3
"""Top-level AIFC Verifier A admission composition v0.2.

This layer enforces experiment-level contracts that must hold before delegating to
the resolver-driven replay engine. It exists so policy admission cannot silently
lag behind the lower-level replay implementation.
"""
from __future__ import annotations

from typing import Any, Mapping

from canonical import CanonicalizationError
from replay import _context, _obj
from replay_engine import verify_replay_manifest as _verify_core
from resolver import EvidenceResolutionError, EvidenceResolver


def _invalid(manifest: Mapping[str, Any], gate: str, code: str, detail: str = "") -> dict[str, Any]:
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
        "gate_results": {gate: "FAIL"},
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": [f"{code}:{detail}" if detail else code],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def verify_replay_manifest(manifest: Mapping[str, Any], resolver: EvidenceResolver) -> dict[str, Any]:
    try:
        if manifest.get("schema") != "AIFC/replay-package/v0.2":
            return _invalid(manifest, "REPLAY_PACKAGE", "REPLAY_PACKAGE_SCHEMA_MISMATCH")
        experiment_id = manifest.get("experiment_id")
        trial_index = manifest.get("subject_trial_index")
        if not isinstance(experiment_id, str) or not experiment_id:
            return _invalid(manifest, "REPLAY_PACKAGE", "EXPERIMENT_ID_INVALID")
        if not isinstance(trial_index, int) or trial_index < 1:
            return _invalid(manifest, "REPLAY_PACKAGE", "SUBJECT_TRIAL_INVALID")

        plan_hash = manifest.get("experiment_plan_hash")
        if not isinstance(plan_hash, str):
            return _invalid(manifest, "EXPERIMENT_PLAN_REPLAY", "EXPERIMENT_PLAN_HASH_MISSING")
        plan = _obj(resolver, plan_hash, "AIFC/experiment-plan/v1")
        _context(plan, experiment_id)

        entropy_policy_hash = plan.get("entropy_policy_hash")
        if not isinstance(entropy_policy_hash, str):
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_POLICY_HASH_MISSING_FROM_PLAN")
        policy = _obj(resolver, entropy_policy_hash, "AIFC/entropy-policy/v1")
        _context(policy, experiment_id)
        if policy.get("frozen_before_first_created") is not True:
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_POLICY_NOT_FROZEN")
        if policy.get("post_target_method_selection_forbidden") is not True:
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "POST_TARGET_ENTROPY_METHOD_SELECTION_NOT_FORBIDDEN")
        if policy.get("unresolved_assumptions_policy") != "BLOCK_STRONGEST_GRADE":
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_UNRESOLVED_POLICY_NOT_FAIL_CLOSED")

        entropy_hash = manifest.get("entropy_profile_hash")
        if not isinstance(entropy_hash, str):
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_PROFILE_HASH_MISSING")
        profile = _obj(resolver, entropy_hash, "AIFC/entropy-profile/v1")
        _context(profile, experiment_id, trial_index)

        if profile.get("source_id") != policy.get("source_id"):
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_SOURCE_POLICY_REBINDING")
        if profile.get("source_protocol_version") != policy.get("source_protocol_version"):
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_SOURCE_VERSION_POLICY_REBINDING")
        if profile.get("derivation_method") not in policy.get("allowed_derivation_methods", []):
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_DERIVATION_METHOD_NOT_PREREGISTERED")
        if profile.get("unresolved_assumptions"):
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_PROFILE_HAS_UNRESOLVED_ASSUMPTIONS")

        rows = profile.get("external_evidence")
        if not isinstance(rows, list):
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_EXTERNAL_EVIDENCE_INVALID")
        present_types = {row.get("evidence_type") for row in rows if isinstance(row, Mapping)}
        required_types = set(policy.get("required_external_evidence_types", []))
        missing_types = sorted(required_types - present_types)
        if missing_types:
            return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_REQUIRED_EVIDENCE_CLASS_MISSING", ",".join(missing_types))
        for row in rows:
            if isinstance(row, Mapping):
                resolver.resolve(str(row.get("content_hash")))

        spec_hash = policy.get("derivation_spec_hash")
        if spec_hash is not None:
            resolver.resolve(str(spec_hash))

        result = _verify_core(manifest, resolver)
        if result.get("terminal_grade") != "INVALIDATED_EVIDENCE":
            result.setdefault("gate_results", {})["ENTROPY_POLICY_REPLAY"] = "PASS"
        return result
    except (EvidenceResolutionError, CanonicalizationError, KeyError, TypeError, ValueError) as exc:
        return _invalid(manifest, "ENTROPY_POLICY_REPLAY", "ENTROPY_POLICY_EVIDENCE_RESOLUTION_FAILED", str(exc))
