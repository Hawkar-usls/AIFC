#!/usr/bin/env python3
"""Authoritative AIFC Verifier A replay engine v0.2.

This module composes the deterministic replay helpers from replay.py but owns the
current top-level evidence-admission choreography. In particular, the per-trial
evidence bundle never points forward to the experiment-level publication manifest.
"""
from __future__ import annotations

from typing import Any, Mapping

from canonical import CanonicalizationError
from frontier import exact_hit_cap, validate_canonical_rational, zero_cap_outcome
from resolver import EvidenceResolutionError, EvidenceResolver
from replay import (
    ReplayRejected,
    _context,
    _obj,
    _reject,
    _require,
    _resolve_hashes,
    _state_event,
    _validate_candidate_profile,
    _validate_causal_evidence,
    _validate_plan_and_policies,
    _validate_publication_manifest,
    _validate_selector,
    derive_target,
    replay_candidate_set,
    replay_ledger,
    replay_quorum,
    replay_registry_chain,
    target_bytes_hash,
)


def verify_replay_manifest(manifest: Mapping[str, Any], resolver: EvidenceResolver) -> dict[str, Any]:
    gates: dict[str, str] = {}
    try:
        _require(manifest.get("schema") == "AIFC/replay-package/v0.2", "REPLAY_PACKAGE", "REPLAY_PACKAGE_SCHEMA_MISMATCH")
        experiment_id = manifest.get("experiment_id")
        subject_trial = manifest.get("subject_trial_index")
        _require(isinstance(experiment_id, str) and experiment_id, "REPLAY_PACKAGE", "EXPERIMENT_ID_INVALID")
        _require(isinstance(subject_trial, int) and subject_trial >= 1, "REPLAY_PACKAGE", "SUBJECT_TRIAL_INVALID")

        plan_hash = str(manifest.get("experiment_plan_hash"))
        plan_objects = _validate_plan_and_policies(resolver, plan_hash, experiment_id)
        plan = plan_objects["plan"]
        gates["EXPERIMENT_PLAN_REPLAY"] = "PASS"
        _require(plan.get("mode") == "FIXED_HORIZON", "STATISTICAL_PLAN_REPLAY", "ANYTIME_EXPERIMENT_REPLAY_NOT_IMPLEMENTED")
        declared_trial_count = plan.get("declared_trial_count")
        _require(isinstance(declared_trial_count, int) and declared_trial_count >= 1, "EXPERIMENT_PLAN_REPLAY", "DECLARED_TRIAL_COUNT_INVALID")
        _require(1 <= subject_trial <= declared_trial_count, "REPLAY_PACKAGE", "SUBJECT_TRIAL_OUTSIDE_PLAN")

        ledger_hashes = manifest.get("ledger_event_hashes")
        _require(isinstance(ledger_hashes, list) and ledger_hashes, "LEDGER_REPLAY", "LEDGER_HASH_LIST_INVALID")
        events = [_obj(resolver, str(h), "AIFC/trial-ledger-event/v1") for h in ledger_hashes]
        ledger = replay_ledger(events, experiment_id, declared_trial_count, plan_hash)
        _require(ledger["event_hashes"] == ledger_hashes, "LEDGER_REPLAY", "LEDGER_HASH_ORDER_MISMATCH")
        gates["LEDGER_REPLAY"] = "PASS"
        gates["COMPLETE_TRIAL_PUBLICATION"] = "PASS"

        bundle_hash = str(manifest.get("evidence_bundle_hash"))
        bundle = _obj(resolver, bundle_hash, "AIFC/evidence-bundle/v1")
        _context(bundle, experiment_id, subject_trial)
        run_id = bundle.get("run_id")
        _require(isinstance(run_id, str) and run_id, "CONTEXT_BINDING", "RUN_ID_INVALID")
        _require(bundle.get("experiment_plan_hash") == plan_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_PLAN_HASH_MISMATCH")

        current_registry_hash = str(manifest.get("witness_registry_hash"))
        transition_hashes = manifest.get("registry_transition_certificate_hashes")
        _require(isinstance(transition_hashes, list), "REGISTRY_TRANSITION_REPLAY", "TRANSITION_HASH_LIST_INVALID")
        registry = replay_registry_chain(resolver, plan, transition_hashes, current_registry_hash, experiment_id)
        _require(bundle.get("witness_registry_hash") == current_registry_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_REGISTRY_HASH_MISMATCH")
        expected_transition_hash = transition_hashes[-1] if transition_hashes else None
        _require(bundle.get("witness_registry_transition_hash") == expected_transition_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_TRANSITION_HASH_MISMATCH")
        gates["REGISTRY_TRANSITION_REPLAY"] = "PASS"
        gates["WITNESS_REGISTRY_FAULT_MODEL"] = "PASS"

        _, created_event_hash = _state_event(ledger, subject_trial, "CREATED")
        created_cert_hash = str(manifest.get("created_quorum_certificate_hash"))
        created_cert = _obj(resolver, created_cert_hash, "AIFC/quorum-certificate/v1")
        replay_quorum(created_cert, registry, current_registry_hash, experiment_id=experiment_id, trial_index=subject_trial, logical_position="CREATED", content_hash=created_event_hash, gate="CREATED_QUORUM_REPLAY")
        gates["CREATED_QUORUM_REPLAY"] = "PASS"

        candidate_set_hash = str(manifest.get("candidate_set_hash"))
        hard_hashes = manifest.get("hard_witness_hashes")
        _require(isinstance(hard_hashes, list), "CANDIDATE_SET_REPLAY", "HARD_WITNESS_HASH_LIST_INVALID")
        candidate_set, candidate_bytes = replay_candidate_set(resolver, candidate_set_hash, hard_hashes, experiment_id, subject_trial, run_id)
        gates["CANDIDATE_SET_REPLAY"] = "PASS"

        candidate_profile_hash = str(manifest.get("candidate_generation_profile_hash"))
        candidate_profile = _obj(resolver, candidate_profile_hash, "AIFC/candidate-generation-profile/v1")
        candidate_policy_hash = str(plan.get("candidate_generation_policy_hash"))
        _validate_candidate_profile(resolver, candidate_profile, candidate_profile_hash, plan_objects["candidate_generation"], candidate_policy_hash, candidate_set, created_cert_hash, experiment_id, subject_trial)
        gates["CANDIDATE_PROVENANCE"] = "PASS"

        pre_return_hash = str(manifest.get("pre_return_certificate_hash"))
        pre_return = _obj(resolver, pre_return_hash, "AIFC/pre-return-certificate/v1")
        _context(pre_return, experiment_id, subject_trial, run_id)
        freeze_event, freeze_event_hash = _state_event(ledger, subject_trial, "PRE_RETURN_FROZEN")
        _require(freeze_event.get("payload_hash") == candidate_set_hash, "PRE_RETURN_REPLAY", "FREEZE_EVENT_CANDIDATE_SET_HASH_MISMATCH")
        _require(pre_return.get("experiment_plan_hash") == plan_hash, "PRE_RETURN_REPLAY", "PRE_RETURN_PLAN_REBINDING")
        _require(pre_return.get("freeze_event_hash") == freeze_event_hash, "PRE_RETURN_REPLAY", "FREEZE_EVENT_HASH_MISMATCH")
        _require(pre_return.get("ledger_head_hash") == freeze_event_hash, "PRE_RETURN_REPLAY", "PRE_RETURN_LEDGER_HEAD_MISMATCH")
        _require(pre_return.get("candidate_set_hash") == candidate_set_hash, "PRE_RETURN_REPLAY", "PRE_RETURN_CANDIDATE_SET_REBINDING")
        _require(pre_return.get("candidate_multiplicity") == candidate_set.get("cardinality"), "PRE_RETURN_REPLAY", "PRE_RETURN_MULTIPLICITY_MISMATCH")
        _require(pre_return.get("candidate_generation_profile_hash") == candidate_profile_hash, "PRE_RETURN_REPLAY", "PRE_RETURN_CANDIDATE_PROFILE_REBINDING")
        _require(pre_return.get("target_selector_policy_hash") == plan.get("target_selector_policy_hash"), "PRE_RETURN_REPLAY", "PRE_RETURN_SELECTOR_POLICY_REBINDING")
        _require(pre_return.get("target_derivation_policy_hash") == plan.get("target_derivation_policy_hash"), "PRE_RETURN_REPLAY", "PRE_RETURN_DERIVATION_POLICY_REBINDING")

        pre_q_hash = str(manifest.get("pre_return_quorum_certificate_hash"))
        pre_q = _obj(resolver, pre_q_hash, "AIFC/quorum-certificate/v1")
        replay_quorum(pre_q, registry, current_registry_hash, experiment_id=experiment_id, trial_index=subject_trial, logical_position="PRE_RETURN_FROZEN", content_hash=freeze_event_hash, gate="PRE_RETURN_QUORUM_REPLAY")
        _require(pre_return.get("quorum_certificate_hash") == pre_q_hash, "PRE_RETURN_QUORUM_REPLAY", "PRE_RETURN_QUORUM_HASH_MISMATCH")
        quorum_event, quorum_event_hash = _state_event(ledger, subject_trial, "QUORUM_CERTIFIED")
        _require(quorum_event.get("payload_hash") == pre_q_hash, "PRE_RETURN_QUORUM_REPLAY", "QUORUM_EVENT_PAYLOAD_MISMATCH")
        gates["PRE_RETURN_REPLAY"] = "PASS"
        gates["PRE_RETURN_QUORUM_REPLAY"] = "PASS"

        selector_hash = str(manifest.get("target_selector_profile_hash"))
        selector = _obj(resolver, selector_hash, "AIFC/target-selector-profile/v1")
        derivation_hash = str(manifest.get("target_derivation_profile_hash"))
        derivation = _obj(resolver, derivation_hash, "AIFC/target-derivation-profile/v1")
        _context(derivation, experiment_id, subject_trial, run_id)
        _require(derivation.get("policy_hash") == plan.get("target_derivation_policy_hash"), "TARGET_DERIVATION_REPLAY", "DERIVATION_POLICY_REBINDING")
        _require(derivation.get("target_selector_profile_hash") == selector_hash, "TARGET_DERIVATION_REPLAY", "DERIVATION_SELECTOR_REBINDING")
        derivation_policy = plan_objects["target_derivation"]
        _require(derivation.get("extraction", {}).get("method") in derivation_policy.get("allowed_extraction_methods", []), "TARGET_DERIVATION_REPLAY", "EXTRACTION_METHOD_NOT_ALLOWED")
        _require(derivation.get("transformation", {}).get("algorithm") in derivation_policy.get("allowed_transformation_algorithms", []), "TARGET_DERIVATION_REPLAY", "TRANSFORMATION_NOT_ALLOWED")
        _require(derivation.get("transformation", {}).get("framing") == derivation_policy.get("framing"), "TARGET_DERIVATION_REPLAY", "DERIVATION_FRAMING_POLICY_MISMATCH")
        _require(set(derivation.get("transformation", {}).get("input_order", [])) <= set(derivation_policy.get("allowed_input_tokens", [])), "TARGET_DERIVATION_REPLAY", "DERIVATION_INPUT_TOKEN_NOT_ALLOWED")

        view_hash = str(manifest.get("pre_target_conditioning_view_hash"))
        view = _obj(resolver, view_hash, "AIFC/pre-target-conditioning-view/v1")
        _context(view, experiment_id, subject_trial, run_id)
        _require(view.get("ledger_head_hash") == quorum_event_hash, "PRE_TARGET_VIEW_REPLAY", "CONDITIONING_VIEW_LEDGER_HEAD_MISMATCH")
        expected_view_bindings = {
            "experiment_plan_hash": plan_hash,
            "candidate_set_hash": candidate_set_hash,
            "candidate_generation_profile_hash": candidate_profile_hash,
            "pre_return_certificate_hash": pre_return_hash,
            "pre_return_quorum_certificate_hash": pre_q_hash,
            "witness_registry_hash": current_registry_hash,
            "target_selector_profile_hash": selector_hash,
            "target_derivation_profile_hash": derivation_hash,
            "causal_model_hash": str(plan.get("causal_model_hash")),
        }
        for field, expected in expected_view_bindings.items():
            _require(view.get(field) == expected, "PRE_TARGET_VIEW_REPLAY", "CONDITIONING_VIEW_REBINDING", field)
        _require(not view.get("unresolved_assumptions"), "PRE_TARGET_VIEW_REPLAY", "POST_HOC_CONDITIONING_VIEW_SANITIZATION_OR_UNRESOLVED_VIEW")
        conditioning_policy = plan_objects["conditioning_policy"]
        if conditioning_policy.get("operator_state_evidence_required") is True:
            _require(bool(view.get("operator_state_evidence_hashes")), "PRE_TARGET_VIEW_REPLAY", "OPERATOR_STATE_EVIDENCE_MISSING")
        if conditioning_policy.get("source_state_evidence_required") is True:
            _require(bool(view.get("source_state_evidence_hashes")), "PRE_TARGET_VIEW_REPLAY", "SOURCE_STATE_EVIDENCE_MISSING")
        _resolve_hashes(resolver, view.get("operator_state_evidence_hashes", []), "PRE_TARGET_VIEW_REPLAY")
        _resolve_hashes(resolver, view.get("source_state_evidence_hashes", []), "PRE_TARGET_VIEW_REPLAY")
        _resolve_hashes(resolver, view.get("additional_pre_target_evidence_hashes", []), "PRE_TARGET_VIEW_REPLAY")

        view_q_hash = str(manifest.get("pre_target_view_quorum_certificate_hash"))
        view_q = _obj(resolver, view_q_hash, "AIFC/quorum-certificate/v1")
        replay_quorum(view_q, registry, current_registry_hash, experiment_id=experiment_id, trial_index=subject_trial, logical_position="PRE_TARGET_VIEW_FROZEN", content_hash=view_hash, gate="PRE_TARGET_VIEW_QUORUM_REPLAY")
        armed_event, _ = _state_event(ledger, subject_trial, "TARGET_ARMED")
        _require(armed_event.get("payload_hash") == view_q_hash, "PRE_TARGET_VIEW_QUORUM_REPLAY", "TARGET_ARMED_PAYLOAD_NOT_VIEW_QUORUM")
        gates["PRE_TARGET_VIEW_REPLAY"] = "PASS"
        gates["PRE_TARGET_VIEW_QUORUM_REPLAY"] = "PASS"

        _validate_selector(selector, plan_objects["target_selector"], profile_hash=selector_hash, policy_hash=str(plan.get("target_selector_policy_hash")), plan_hash=plan_hash, pre_return_quorum_hash=pre_q_hash, pre_target_view_quorum_hash=view_q_hash, experiment_id=experiment_id, trial_index=subject_trial, resolver=resolver)
        gates["TARGET_SELECTOR_REPLAY"] = "PASS"

        entropy_hash = str(manifest.get("entropy_profile_hash"))
        entropy = _obj(resolver, entropy_hash, "AIFC/entropy-profile/v1")
        _context(entropy, experiment_id, subject_trial)
        _require(entropy.get("target_selector_profile_hash") == selector_hash, "ENTROPY_PROFILE_REPLAY", "ENTROPY_SELECTOR_REBINDING")
        _require(entropy.get("target_derivation_profile_hash") == derivation_hash, "ENTROPY_PROFILE_REPLAY", "ENTROPY_DERIVATION_REBINDING")
        _require(entropy.get("conditioning_view_hash") == view_hash, "ENTROPY_PROFILE_REPLAY", "POST_HOC_CONDITIONING_VIEW_SANITIZATION")
        _require(entropy.get("source_id") == selector.get("source_id") == derivation.get("source_id"), "ENTROPY_PROFILE_REPLAY", "ENTROPY_SOURCE_REBINDING")
        bound_result, p_i = validate_canonical_rational(entropy.get("point_probability_upper_bound", {}))
        _require(bound_result.ok and p_i is not None, "ENTROPY_PROFILE_REPLAY", bound_result.code, bound_result.detail)
        _require(entropy.get("admission_status") == "ADMITTED", "ENTROPY_PROFILE_REPLAY", "ENTROPY_PROFILE_NOT_ADMITTED")
        _require(not entropy.get("unresolved_assumptions"), "ENTROPY_PROFILE_REPLAY", "ENTROPY_UNRESOLVED_ASSUMPTIONS")
        for row in entropy.get("external_evidence", []):
            resolver.resolve(str(row.get("content_hash")))
        if entropy.get("derivation_document_hash") is not None:
            resolver.resolve(str(entropy.get("derivation_document_hash")))
        gates["ENTROPY_PROFILE_REPLAY"] = "PASS"

        causal_hash = str(manifest.get("causal_model_hash"))
        _require(causal_hash == plan.get("causal_model_hash"), "CAUSAL_MODEL_EVIDENCE", "CAUSAL_MODEL_PLAN_REBINDING")
        causal = _obj(resolver, causal_hash, "AIFC/causal-model/v1")
        _validate_causal_evidence(resolver, causal, experiment_id)
        gates["CAUSAL_EVIDENCE_RESOLUTION"] = "PASS"

        statistical_hash = str(manifest.get("statistical_plan_hash"))
        _require(statistical_hash == plan.get("statistical_plan_hash"), "STATISTICAL_PLAN_REPLAY", "STATISTICAL_PLAN_REBINDING")
        statistical = _obj(resolver, statistical_hash, "AIFC/statistical-plan/v1")
        _context(statistical, experiment_id)
        alpha_res, _ = validate_canonical_rational(statistical.get("alpha", {}))
        _require(alpha_res.ok, "STATISTICAL_PLAN_REPLAY", alpha_res.code, alpha_res.detail)
        _require(statistical.get("mode") == "FIXED_HORIZON", "STATISTICAL_PLAN_REPLAY", "ANYTIME_STATISTICS_NOT_IMPLEMENTED")
        _require(statistical.get("declared_horizon") == declared_trial_count, "STATISTICAL_PLAN_REPLAY", "STATISTICAL_HORIZON_REBINDING")
        _require(statistical.get("fixed_horizon_product_bound_policy") == "ONLY_FOR_DETERMINISTIC_OR_PREREGISTERED_CAP_SEQUENCE", "STATISTICAL_PLAN_REPLAY", "FIXED_HORIZON_BOUND_CONDITIONS_NOT_FROZEN")
        gates["STATISTICAL_PLAN_REPLAY"] = "PASS"

        target_hash = str(manifest.get("target_evidence_hash"))
        target = _obj(resolver, target_hash, "AIFC/target-evidence/v1")
        _context(target, experiment_id, subject_trial)
        _require(target.get("target_selector_profile_hash") == selector_hash, "TARGET_DERIVATION_REPLAY", "TARGET_SELECTOR_PROFILE_REBINDING")
        _require(target.get("target_derivation_profile_hash") == derivation_hash, "TARGET_DERIVATION_REPLAY", "TARGET_DERIVATION_PROFILE_REBINDING")
        _require(target.get("conditioning_view_hash") == view_hash, "TARGET_DERIVATION_REPLAY", "TARGET_CONDITIONING_VIEW_REBINDING")
        _require(target.get("entropy_profile_hash") == entropy_hash, "TARGET_DERIVATION_REPLAY", "TARGET_ENTROPY_REBINDING")
        _require(target.get("target_event_id") == selector.get("selected_event_id"), "TARGET_DERIVATION_REPLAY", "TARGET_EVENT_SELECTOR_MISMATCH")
        raw_resolved = resolver.resolve(str(target.get("raw_source_object_hash")))
        _resolve_hashes(resolver, target.get("source_evidence_hashes", []), "TARGET_SOURCE_EVIDENCE")
        derived = derive_target(derivation, raw_resolved.exact_bytes, target_event_id=str(target.get("target_event_id")), pre_return_hash=pre_return_hash)
        target_hex = target.get("target_bytes_hex")
        _require(isinstance(target_hex, str) and target_hex, "TARGET_DERIVATION_REPLAY", "TARGET_BYTES_REQUIRED")
        try:
            declared_target = bytes.fromhex(target_hex)
        except ValueError as exc:
            _reject("TARGET_DERIVATION_REPLAY", "TARGET_BYTES_HEX_INVALID", str(exc))
        _require(declared_target == derived, "TARGET_DERIVATION_REPLAY", "DERIVED_TARGET_BYTES_MISMATCH")
        _require(target.get("target_canonical_hash") == target_bytes_hash(derived), "TARGET_DERIVATION_REPLAY", "TARGET_CANONICAL_HASH_MISMATCH")
        observed_event, _ = _state_event(ledger, subject_trial, "TARGET_OBSERVED")
        _require(observed_event.get("payload_hash") == target_hash, "TARGET_DERIVATION_REPLAY", "TARGET_OBSERVED_PAYLOAD_MISMATCH")
        gates["TARGET_DERIVATION_REPLAY"] = "PASS"

        exact_match = any(candidate == derived for candidate in candidate_bytes)
        k = int(candidate_set["cardinality"])
        a_i = exact_hit_cap(k, p_i)
        zero = zero_cap_outcome(a_i, exact_match)
        if a_i == 0:
            _require(zero.ok, "STATISTICAL_CAP_STRUCTURE", zero.code, zero.detail)
        gates["EXACT_IDENTITY"] = "PASS"
        gates["STATISTICAL_CAP_STRUCTURE"] = "PASS"

        # Per-trial bundle deliberately does NOT bind the later publication manifest.
        bindings = {
            "experiment_plan_hash": plan_hash,
            "pre_return_certificate_hash": pre_return_hash,
            "candidate_generation_profile_hash": candidate_profile_hash,
            "candidate_set_hash": candidate_set_hash,
            "candidate_multiplicity": k,
            "target_selector_profile_hash": selector_hash,
            "target_derivation_profile_hash": derivation_hash,
            "conditioning_view_hash": view_hash,
            "entropy_profile_hash": entropy_hash,
            "causal_model_hash": causal_hash,
            "statistical_plan_hash": statistical_hash,
            "witness_registry_hash": current_registry_hash,
            "target_evidence_hash": target_hash,
        }
        for field, expected in bindings.items():
            _require(bundle.get(field) == expected, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_REBINDING", field)
        if bundle.get("eprocess_state_hash") is not None:
            resolver.resolve(str(bundle.get("eprocess_state_hash")), expected_schema="AIFC/eprocess-state/v1")
        gates["EVIDENCE_BUNDLE_BINDINGS"] = "PASS"

        _, verified_event_hash = _state_event(ledger, subject_trial, "VERIFIED")
        _require(bundle.get("trial_ledger_head_hash") == verified_event_hash, "TERMINAL_BUNDLE_BINDING", "BUNDLE_HEAD_MUST_BE_VERIFIED_EVENT")
        terminal_event = ledger["terminal"][subject_trial]
        _require(terminal_event.get("evidence_bundle_hash") == bundle_hash, "TERMINAL_BUNDLE_BINDING", "TERMINAL_BUNDLE_HASH_MISMATCH")
        expected_subtype = "COMPLETED_HIT" if exact_match else "COMPLETED_MISS"
        _require(terminal_event.get("terminal_subtype") == expected_subtype, "TERMINAL_BUNDLE_BINDING", "TERMINAL_SUBTYPE_IDENTITY_MISMATCH")
        gates["TERMINAL_BUNDLE_BINDING"] = "PASS"

        publication_hash = str(manifest.get("publication_manifest_hash"))
        publication = _obj(resolver, publication_hash, "AIFC/publication-manifest/v1")
        _validate_publication_manifest(resolver, publication, publication_hash, experiment_id=experiment_id, plan_hash=plan_hash, publication_policy_hash=str(plan.get("publication_policy_hash")), declared_trial_count=declared_trial_count, ledger=ledger, subject_trial=subject_trial, subject_bundle_hash=bundle_hash)
        gates["PUBLICATION_MANIFEST_REPLAY"] = "PASS"

        gates["ED25519_SIGNATURE_CRYPTO"] = "BLOCKED"
        gates["CAUSAL_D_SEPARATION"] = "BLOCKED"
        gates["TARGET_SOURCE_CRYPTOGRAPHIC_PROOF"] = "BLOCKED"
        gates["FULL_EXPERIMENT_STATISTICAL_REPLAY"] = "BLOCKED"
        gates["BYTE_IDENTICAL_CANONICALIZATION"] = "BLOCKED"

        return {
            "schema": "AIFC/verifier-result/v1",
            "experiment_id": experiment_id,
            "trial_index": subject_trial,
            "verifier_id": "AIFC-Verifier-A",
            "verifier_version": "0.2.0-replay",
            "evidence_bundle_hash": bundle_hash,
            "gate_results": gates,
            "exact_match": exact_match,
            "terminal_grade": "STRUCTURAL_MATCH_ONLY" if exact_match else "NOT_ADMITTED",
            "failure_codes": [],
            "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
            "fail_open": False,
        }
    except (ReplayRejected, EvidenceResolutionError, CanonicalizationError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ReplayRejected):
            gates[exc.problem.gate] = "FAIL"
            code, detail = exc.problem.code, exc.problem.detail
        elif isinstance(exc, EvidenceResolutionError):
            gates["EVIDENCE_RESOLUTION"] = "FAIL"
            code, detail = "EVIDENCE_RESOLUTION_FAILED", str(exc)
        elif isinstance(exc, CanonicalizationError):
            gates["CANONICALIZATION_A"] = "FAIL"
            code, detail = "CANONICALIZATION_REJECTED", str(exc)
        else:
            gates["REPLAY_PACKAGE"] = "FAIL"
            code, detail = "MALFORMED_OR_MISSING_EVIDENCE", str(exc)
        experiment_id = manifest.get("experiment_id", "UNKNOWN") if isinstance(manifest, Mapping) else "UNKNOWN"
        trial_index = manifest.get("subject_trial_index", 1) if isinstance(manifest, Mapping) else 1
        bundle_hash = manifest.get("evidence_bundle_hash", "0" * 64) if isinstance(manifest, Mapping) else "0" * 64
        return {
            "schema": "AIFC/verifier-result/v1",
            "experiment_id": experiment_id if isinstance(experiment_id, str) and experiment_id else "UNKNOWN",
            "trial_index": trial_index if isinstance(trial_index, int) and trial_index >= 1 else 1,
            "verifier_id": "AIFC-Verifier-A",
            "verifier_version": "0.2.0-replay",
            "evidence_bundle_hash": bundle_hash if isinstance(bundle_hash, str) and len(bundle_hash) == 64 else "0" * 64,
            "gate_results": gates,
            "exact_match": False,
            "terminal_grade": "INVALIDATED_EVIDENCE",
            "failure_codes": [f"{code}:{detail}" if detail else code],
            "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
            "fail_open": False,
        }
