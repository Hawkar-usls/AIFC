import copy
import sys
import tempfile
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import canonical_json_bytes, protocol_hash, raw_evidence_hash  # noqa: E402
from frontier import experiment_genesis_hash  # noqa: E402
from replay import derive_target, registry_genesis_hash, target_bytes_hash  # noqa: E402
from replay_engine import verify_replay_manifest  # noqa: E402
from resolver import EvidenceResolver  # noqa: E402


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.entries = []
        (root / "objects").mkdir(parents=True, exist_ok=True)

    def protocol(self, obj):
        h = protocol_hash(obj)
        rel = f"objects/{h}.json"
        (self.root / rel).write_bytes(canonical_json_bytes(obj))
        self.entries.append({
            "content_hash": h,
            "relative_path": rel,
            "content_kind": "AIFC_PROTOCOL_JSON",
            "declared_schema": obj["schema"],
            "media_type": "application/json",
        })
        return h

    def raw(self, data: bytes):
        h = raw_evidence_hash(data)
        rel = f"objects/{h}.bin"
        (self.root / rel).write_bytes(data)
        self.entries.append({
            "content_hash": h,
            "relative_path": rel,
            "content_kind": "RAW_BYTES",
            "media_type": "application/octet-stream",
        })
        return h

    def resolver(self):
        return EvidenceResolver(self.root, {
            "schema": "AIFC/evidence-store-index/v1",
            "store_id": "test-store",
            "entries": self.entries,
        })


def witness_registry(exp):
    witnesses = []
    for i in range(4):
        witnesses.append({
            "witness_id": f"w{i}",
            "failure_domain": f"domain-{i}",
            "status": "ACTIVE",
            "keys": [{
                "key_id": f"k{i}",
                "algorithm": "Ed25519",
                "public_key_encoding": "hex",
                "public_key": (f"{i+1:02x}" * 32),
                "valid_from_registry_sequence": 0,
                "valid_until_registry_sequence": None,
                "status": "ACTIVE",
                "predecessor_key_id": None,
                "revocation_reason": None,
            }],
        })
    return {
        "schema": "AIFC/witness-registry/v1",
        "registry_id": "registry-0",
        "experiment_id": exp,
        "registry_sequence": 0,
        "previous_registry_hash": registry_genesis_hash(exp),
        "transition_certificate_hash": None,
        "fault_model": {"n": 4, "f": 1, "q": 3, "independence_unit": "FAILURE_DOMAIN"},
        "witnesses": witnesses,
    }


def quorum(exp, trial, logical_position, content_hash, registry_hash):
    receipts = []
    for i in range(3):
        receipts.append({
            "schema": "AIFC/witness-receipt/v1",
            "experiment_id": exp,
            "trial_index": trial,
            "logical_position": logical_position,
            "content_hash": content_hash,
            "registry_hash": registry_hash,
            "witness_id": f"w{i}",
            "key_id": f"k{i}",
            "signature_algorithm": "Ed25519",
            "signature": "ab" * 64,
        })
    return {
        "schema": "AIFC/quorum-certificate/v1",
        "experiment_id": exp,
        "trial_index": trial,
        "logical_position": logical_position,
        "content_hash": content_hash,
        "registry_hash": registry_hash,
        "n": 4,
        "f": 1,
        "q": 3,
        "receipts": receipts,
    }


def ledger_event(exp, event_index, trial, ordinal, state_from, state_to, previous_hash, payload_hash, reason, terminal_subtype=None, evidence_bundle_hash=None):
    return {
        "schema": "AIFC/trial-ledger-event/v1",
        "experiment_id": exp,
        "event_index": event_index,
        "trial_index": trial,
        "run_id": "run-1",
        "transition_ordinal": ordinal,
        "state_from": state_from,
        "state_to": state_to,
        "terminal_subtype": terminal_subtype,
        "previous_event_hash": previous_hash,
        "prerequisite_certificate_hash": "f" * 64 if state_to == "CREATED" else None,
        "payload_hash": payload_hash,
        "evidence_bundle_hash": evidence_bundle_hash,
        "reason_code": reason,
    }


def build_fixture(root: Path):
    s = Store(root)
    exp = "exp-1"
    trial = 1
    run = "run-1"

    generic_evidence = s.raw(b"independent audit evidence")
    operator_evidence = s.raw(b"operator pre-target state")
    source_state_evidence = s.raw(b"source pre-target state")
    entropy_evidence = s.raw(b"beacon entropy/security evidence")
    selector_transcript = s.raw(b"fixed-event selector recomputation transcript")
    rollback_domain = s.raw(b"candidate host and local logs")

    registry = witness_registry(exp)
    registry_hash = s.protocol(registry)

    trial_creation = {
        "schema": "AIFC/trial-creation-policy/v1", "policy_id": "tcp-1", "experiment_id": exp,
        "method": "PREALLOCATED_SLOTS", "slot_index_rule": "CONTIGUOUS_ONE_BASED", "declared_trial_count": 1,
        "schedule_or_trigger_spec_hash": None, "candidate_generation_before_created_forbidden": True,
        "silent_slot_deletion_forbidden": True, "frozen_before_first_created": True,
    }
    trial_creation_hash = s.protocol(trial_creation)
    candidate_policy = {
        "schema": "AIFC/candidate-generation-policy/v1", "policy_id": "cgp-policy-1", "experiment_id": exp,
        "allowed_generation_modes": ["SINGLE_SHOT_AFTER_CERTIFIED_CREATED"],
        "maximum_candidate_set_cardinality": 1,
        "operator_choice_after_created_policy": "FORBIDDEN_FOR_STRONGEST_GRADE_V1",
        "operator_choice_after_generation_policy": "FORBIDDEN_FOR_STRONGEST_GRADE_V1",
        "hidden_pool_policy": "EXCLUDE_WITH_EXTERNAL_EVIDENCE_OR_FAIL_STRONGEST_GRADE",
        "required_external_evidence_types": ["EXECUTION_RECEIPT"], "frozen_before_first_created": True,
    }
    candidate_policy_hash = s.protocol(candidate_policy)
    selector_policy = {
        "schema": "AIFC/target-selector-policy/v1", "policy_id": "tsp-1", "experiment_id": exp,
        "source_id": "beacon-A", "source_protocol_version": "v1",
        "selection_algorithm": "FIXED_EVENT_ID_FROM_PLAN", "anchor_role": "EXPERIMENT_PLAN",
        "parameters": {"fixed_event_id": "round-1000", "safety_margin_events": None, "round_offset": None,
                       "source_schedule_spec_hash": None, "schedule_epoch_external_evidence_hash": None},
        "exactly_one_event_per_trial": True, "frozen_before_first_created": True,
    }
    selector_policy_hash = s.protocol(selector_policy)
    derivation_policy = {
        "schema": "AIFC/target-derivation-policy/v1", "policy_id": "tdp-policy-1", "experiment_id": exp,
        "allowed_extraction_methods": ["JSON_POINTER_HEX_BYTES"],
        "allowed_transformation_algorithms": ["SHA-256"],
        "allowed_input_tokens": ["EXTRACTED_BYTES", "TARGET_EVENT_ID_UTF8", "RUN_ID_UTF8", "PRE_RETURN_CERTIFICATE_HASH_BYTES"],
        "framing": "AIFC_TYPED_LENGTH_PREFIXED_V1", "exactly_one_derivation_per_trial": True,
        "frozen_before_first_created": True,
    }
    derivation_policy_hash = s.protocol(derivation_policy)
    entropy_policy = {
        "schema": "AIFC/entropy-policy/v1", "policy_id": "entropy-policy-1", "experiment_id": exp,
        "source_id": "beacon-A", "source_protocol_version": "v1",
        "allowed_derivation_methods": ["PUBLIC_BEACON_SPECIFICATION"],
        "conditioning_view_role": "AIFC_PRE_TARGET_CONDITIONING_VIEW_AT_TARGET_ARMED",
        "required_external_evidence_types": ["SOURCE_SECURITY_EVIDENCE"],
        "derivation_spec_hash": entropy_evidence,
        "unresolved_assumptions_policy": "BLOCK_STRONGEST_GRADE",
        "post_target_method_selection_forbidden": True,
        "frozen_before_first_created": True,
    }
    entropy_policy_hash = s.protocol(entropy_policy)
    causal = {
        "schema": "AIFC/causal-model/v1", "model_id": "cm-1", "experiment_id": exp,
        "nodes": [
            {"id": "R", "role": "PRE_RETURN_HARD", "observed": True, "available_pre_target": True, "evidence_hashes": [generic_evidence]},
            {"id": "T", "role": "TARGET_HARD", "observed": True, "available_pre_target": False, "evidence_hashes": [generic_evidence]},
        ],
        "edges": [],
        "no_edge_claims": [
            {"source": "T", "target": "R", "basis": "EVIDENCE_BACKED", "evidence_hashes": [generic_evidence], "unresolved_assumption": None},
            {"source": "R", "target": "T", "basis": "EVIDENCE_BACKED", "evidence_hashes": [generic_evidence], "unresolved_assumption": None},
        ],
        "conditioned_on": [],
        "required_d_separations": [{"left": "R", "right": "T", "given": []}],
        "forbidden_conditioning": [], "assumptions": [], "unresolved_assumptions": [],
        "model_completeness_status": "EXTERNALLY_AUDITED_NOT_PROVEN_COMPLETE",
    }
    causal_hash = s.protocol(causal)
    statistical = {
        "schema": "AIFC/statistical-plan/v1", "plan_id": "stat-1", "experiment_id": exp,
        "mode": "FIXED_HORIZON", "alpha": {"numerator_dec": "1", "denominator_dec": "20", "canonical_reduced": True},
        "candidate_multiplicity_rule": "USE_VERIFIED_CANDIDATE_SET_CARDINALITY",
        "target_derivation_rule": "EXACTLY_ONE_ADMITTED_TARGET_DERIVATION_PER_TRIAL",
        "fixed_horizon_product_bound_policy": "ONLY_FOR_DETERMINISTIC_OR_PREREGISTERED_CAP_SEQUENCE",
        "declared_horizon": 1,
        "anytime_eprocess_policy": {"enabled": False, "lambda_policy_type": "DISABLED", "fixed_lambda": None,
                                    "predictable_algorithm_spec_hash": None, "history_input_policy_hash": None},
        "frozen_before_first_created": True,
    }
    statistical_hash = s.protocol(statistical)
    publication_policy = {
        "schema": "AIFC/publication-policy/v1", "policy_id": "pub-1", "experiment_id": exp,
        "publish_every_certified_created_slot": True, "publish_terminal_state_for_every_slot": True,
        "publish_aborts_and_invalidations": True, "publish_ledger_continuity_proof": True,
        "external_publication_root_required": True, "maximum_publication_delay_policy_hash": None,
        "frozen_before_first_created": True,
    }
    publication_policy_hash = s.protocol(publication_policy)
    freshness_policy = {
        "schema": "AIFC/external-freshness-policy/v1", "policy_id": "fresh-1", "experiment_id": exp,
        "rollback_domain_definition_hash": rollback_domain,
        "required_external_roots": ["EXPERIMENT_PLAN", "CREATED", "PRE_RETURN_FROZEN", "TARGET_ARMED", "TERMINAL"],
        "freshness_semantics": "APPEND_ONLY_HEAD_OUTSIDE_ROLLBACK_DOMAIN", "wall_clock_not_sufficient": True,
        "minimum_independent_failure_domains": 3, "frozen_before_first_created": True,
    }
    freshness_hash = s.protocol(freshness_policy)
    conditioning_policy = {
        "schema": "AIFC/conditioning-view-policy/v1", "policy_id": "cvp-1", "experiment_id": exp,
        "capture_state": "TARGET_ARMED",
        "required_binding_classes": ["EXPERIMENT_PLAN", "LEDGER_HEAD", "CANDIDATE_SET", "CANDIDATE_GENERATION_PROFILE",
                                     "PRE_RETURN_CERTIFICATE", "PRE_RETURN_QUORUM", "WITNESS_REGISTRY", "TARGET_SELECTOR_PROFILE",
                                     "TARGET_DERIVATION_PROFILE", "CAUSAL_MODEL", "OPERATOR_STATE", "SOURCE_STATE"],
        "operator_state_evidence_required": True, "source_state_evidence_required": True,
        "externally_certified": True, "post_target_reconstruction_forbidden": True,
        "unresolved_assumptions_policy": "BLOCK_STRONGEST_GRADE", "frozen_before_first_created": True,
    }
    conditioning_hash = s.protocol(conditioning_policy)

    plan = {
        "schema": "AIFC/experiment-plan/v1", "experiment_id": exp, "protocol_version": "1.0-draft",
        "mode": "FIXED_HORIZON", "trial_creation_policy_hash": trial_creation_hash, "declared_trial_count": 1,
        "initial_witness_registry_hash": registry_hash, "candidate_generation_policy_hash": candidate_policy_hash,
        "target_selector_policy_hash": selector_policy_hash, "target_derivation_policy_hash": derivation_policy_hash,
        "entropy_policy_hash": entropy_policy_hash,
        "causal_model_hash": causal_hash, "statistical_plan_hash": statistical_hash,
        "publication_policy_hash": publication_policy_hash, "external_freshness_policy_hash": freshness_hash,
        "conditioning_view_policy_hash": conditioning_hash, "allowed_registry_reconfiguration": False,
        "strongest_grade_exactly_one_target_derivation_per_trial": True, "frozen_before_first_created": True,
    }
    plan_hash = s.protocol(plan)

    event_hashes = []
    created = ledger_event(exp, 0, trial, 0, None, "CREATED", experiment_genesis_hash(exp), plan_hash, "CREATE_SLOT")
    created_hash = s.protocol(created); event_hashes.append(created_hash)
    created_q = quorum(exp, trial, "CREATED", created_hash, registry_hash)
    created_q_hash = s.protocol(created_q)

    candidate_evidence = s.raw(b"single-shot candidate execution receipt")
    candidate_profile = {
        "schema": "AIFC/candidate-generation-profile/v1", "profile_id": "candidate-profile-1", "experiment_id": exp,
        "trial_index": trial, "policy_hash": candidate_policy_hash, "created_slot_certificate_hash": created_q_hash,
        "generation_mode": "SINGLE_SHOT_AFTER_CERTIFIED_CREATED",
        "generator_identity": {"implementation_id": "generator-A", "implementation_version": "1", "code_or_image_hash": generic_evidence},
        "pre_created_state_commitment": {"method": "external-state-hash", "content_hash": generic_evidence, "externally_certified": True},
        "candidate_set_cardinality_upper_bound": 1,
        "selection_freedom": {"operator_choice_after_created": False, "operator_choice_after_generation": False,
                              "hidden_pool_exclusion_basis": "single-shot externally witnessed execution"},
        "external_evidence": [{"evidence_type": "EXECUTION_RECEIPT", "content_hash": candidate_evidence, "locator": None}],
        "assumptions": [], "unresolved_assumptions": [], "admission_status": "ADMITTED",
    }
    candidate_profile_hash = s.protocol(candidate_profile)
    hard = {
        "schema": "AIFC/hard-witness/v1", "experiment_id": exp, "run_id": run, "trial_index": trial,
        "semantic_class": None, "payload128": "11" * 16, "nonce128": "22" * 16,
    }
    hard_hash = s.protocol(hard)
    candidate_set = {
        "schema": "AIFC/candidate-set/v1", "experiment_id": exp, "trial_index": trial, "run_id": run,
        "hard_witness_hashes": [hard_hash], "cardinality": 1,
    }
    candidate_set_hash = s.protocol(candidate_set)

    freeze = ledger_event(exp, 1, trial, 1, "CREATED", "PRE_RETURN_FROZEN", created_hash, candidate_set_hash, "FREEZE")
    freeze_hash = s.protocol(freeze); event_hashes.append(freeze_hash)
    pre_q = quorum(exp, trial, "PRE_RETURN_FROZEN", freeze_hash, registry_hash)
    pre_q_hash = s.protocol(pre_q)
    pre = {
        "schema": "AIFC/pre-return-certificate/v1", "experiment_id": exp, "trial_index": trial, "run_id": run,
        "experiment_plan_hash": plan_hash, "candidate_set_hash": candidate_set_hash, "candidate_multiplicity": 1,
        "candidate_generation_profile_hash": candidate_profile_hash, "freeze_event_hash": freeze_hash,
        "ledger_head_hash": freeze_hash, "quorum_certificate_hash": pre_q_hash,
        "target_selector_policy_hash": selector_policy_hash, "target_derivation_policy_hash": derivation_policy_hash,
    }
    pre_hash = s.protocol(pre)
    qevent = ledger_event(exp, 2, trial, 2, "PRE_RETURN_FROZEN", "QUORUM_CERTIFIED", freeze_hash, pre_q_hash, "QUORUM")
    qevent_hash = s.protocol(qevent); event_hashes.append(qevent_hash)

    selector = {
        "schema": "AIFC/target-selector-profile/v1", "profile_id": "selector-1", "experiment_id": exp, "trial_index": trial,
        "policy_hash": selector_policy_hash, "source_id": "beacon-A", "source_protocol_version": "v1",
        "selection_algorithm": "FIXED_EVENT_ID_FROM_PLAN", "anchor_role": "EXPERIMENT_PLAN", "anchor_hash": plan_hash,
        "parameters": {"fixed_event_id": "round-1000", "schedule_period_numerator_ns": None,
                       "schedule_period_denominator": None, "schedule_epoch_external_evidence_hash": None,
                       "safety_margin_events": None, "round_offset": None, "source_schedule_spec_hash": None},
        "selected_event_id": "round-1000", "selection_transcript_hash": selector_transcript,
        "frozen_before_target_observed": True, "alternative_selected_events": [],
    }
    selector_hash = s.protocol(selector)
    derivation = {
        "schema": "AIFC/target-derivation-profile/v1", "profile_id": "derive-1", "experiment_id": exp,
        "trial_index": trial, "run_id": run, "policy_hash": derivation_policy_hash,
        "source_id": "beacon-A", "source_protocol_version": "v1", "raw_source_object_schema": "beacon/raw/v1",
        "target_selector_profile_hash": selector_hash,
        "extraction": {"method": "JSON_POINTER_HEX_BYTES", "json_pointer": "/randomness"},
        "transformation": {"algorithm": "SHA-256", "framing": "AIFC_TYPED_LENGTH_PREFIXED_V1",
                           "input_order": ["EXTRACTED_BYTES", "TARGET_EVENT_ID_UTF8", "RUN_ID_UTF8", "PRE_RETURN_CERTIFICATE_HASH_BYTES"]},
        "domain_separator": "AIFC:TARGET:v1", "output_length_bits": 256, "frozen_before_target": True,
    }
    derivation_hash = s.protocol(derivation)

    view = {
        "schema": "AIFC/pre-target-conditioning-view/v1", "view_id": "view-1", "experiment_id": exp,
        "trial_index": trial, "run_id": run, "logical_state": "TARGET_ARMED", "ledger_head_hash": qevent_hash,
        "experiment_plan_hash": plan_hash, "candidate_set_hash": candidate_set_hash,
        "candidate_generation_profile_hash": candidate_profile_hash, "pre_return_certificate_hash": pre_hash,
        "pre_return_quorum_certificate_hash": pre_q_hash, "witness_registry_hash": registry_hash,
        "target_selector_profile_hash": selector_hash, "target_derivation_profile_hash": derivation_hash,
        "causal_model_hash": causal_hash, "operator_state_evidence_hashes": [operator_evidence],
        "source_state_evidence_hashes": [source_state_evidence], "additional_pre_target_evidence_hashes": [],
        "unresolved_assumptions": [], "frozen_before_target_observed": True,
    }
    view_hash = s.protocol(view)
    view_q = quorum(exp, trial, "PRE_TARGET_VIEW_FROZEN", view_hash, registry_hash)
    view_q_hash = s.protocol(view_q)
    armed = ledger_event(exp, 3, trial, 3, "QUORUM_CERTIFIED", "TARGET_ARMED", qevent_hash, view_q_hash, "ARM_TARGET")
    armed_hash = s.protocol(armed); event_hashes.append(armed_hash)

    entropy = {
        "schema": "AIFC/entropy-profile/v1", "profile_id": "entropy-1", "experiment_id": exp, "trial_index": trial,
        "source_id": "beacon-A", "source_protocol_version": "v1", "target_selector_profile_hash": selector_hash,
        "target_derivation_profile_hash": derivation_hash, "conditioning_view_hash": view_hash,
        "point_probability_upper_bound": {"numerator_dec": "1", "denominator_dec": "256", "canonical_reduced": True},
        "min_entropy_bits_lower_bound": "8", "derivation_method": "PUBLIC_BEACON_SPECIFICATION",
        "derivation_document_hash": entropy_evidence, "assumptions": [], "unresolved_assumptions": [],
        "external_evidence": [{"evidence_type": "SOURCE_SECURITY_EVIDENCE", "content_hash": entropy_evidence, "locator": None}],
        "admission_status": "ADMITTED",
    }
    entropy_hash = s.protocol(entropy)

    source_bytes = canonical_json_bytes({"randomness": "33" * 32})
    raw_source_hash = s.raw(source_bytes)
    source_proof = s.raw(b"source event proof placeholder")
    derived = derive_target(derivation, source_bytes, target_event_id="round-1000", pre_return_hash=pre_hash)
    target = {
        "schema": "AIFC/target-evidence/v1", "experiment_id": exp, "trial_index": trial, "source_id": "beacon-A",
        "target_selector_profile_hash": selector_hash, "target_derivation_profile_hash": derivation_hash,
        "conditioning_view_hash": view_hash, "target_event_id": "round-1000", "raw_source_object_hash": raw_source_hash,
        "target_canonical_hash": target_bytes_hash(derived), "target_bytes_hex": derived.hex(),
        "entropy_profile_hash": entropy_hash, "source_evidence_hashes": [source_proof], "wall_clock_timestamp": None,
    }
    target_hash = s.protocol(target)
    observed = ledger_event(exp, 4, trial, 4, "TARGET_ARMED", "TARGET_OBSERVED", armed_hash, target_hash, "TARGET_OBSERVED")
    observed_hash = s.protocol(observed); event_hashes.append(observed_hash)
    verified = ledger_event(exp, 5, trial, 5, "TARGET_OBSERVED", "VERIFIED", observed_hash, target_hash, "VERIFY_STRUCTURAL")
    verified_hash = s.protocol(verified); event_hashes.append(verified_hash)

    bundle = {
        "schema": "AIFC/evidence-bundle/v1", "experiment_id": exp, "trial_index": trial, "run_id": run,
        "experiment_plan_hash": plan_hash, "trial_ledger_head_hash": verified_hash,
        "pre_return_certificate_hash": pre_hash, "candidate_generation_profile_hash": candidate_profile_hash,
        "candidate_set_hash": candidate_set_hash, "candidate_multiplicity": 1,
        "target_selector_profile_hash": selector_hash, "target_derivation_profile_hash": derivation_hash,
        "conditioning_view_hash": view_hash, "entropy_profile_hash": entropy_hash, "causal_model_hash": causal_hash,
        "statistical_plan_hash": statistical_hash, "witness_registry_hash": registry_hash,
        "witness_registry_transition_hash": None, "target_evidence_hash": target_hash, "eprocess_state_hash": None,
        "additional_evidence_hashes": [],
    }
    bundle_hash = s.protocol(bundle)
    terminal = ledger_event(exp, 6, trial, 6, "VERIFIED", "TERMINAL", verified_hash, bundle_hash, "COMPLETE_MISS",
                            terminal_subtype="COMPLETED_MISS", evidence_bundle_hash=bundle_hash)
    terminal_hash = s.protocol(terminal); event_hashes.append(terminal_hash)

    publication_root = s.raw(b"externally rooted publication head")
    publication_receipt = s.raw(b"publication witness receipt")
    publication = {
        "schema": "AIFC/publication-manifest/v1", "manifest_id": "pub-manifest-1", "experiment_id": exp,
        "experiment_plan_hash": plan_hash, "publication_policy_hash": publication_policy_hash,
        "declared_trial_count": 1, "final_ledger_head_hash": terminal_hash,
        "trial_records": [{"trial_index": 1, "terminal_event_hash": terminal_hash,
                           "terminal_subtype": "COMPLETED_MISS", "evidence_bundle_hash": bundle_hash}],
        "external_publication_root_hash": publication_root,
        "external_publication_receipt_hashes": [publication_receipt],
    }
    publication_hash = s.protocol(publication)

    package = {
        "schema": "AIFC/replay-package/v0.2", "experiment_id": exp, "subject_trial_index": 1,
        "experiment_plan_hash": plan_hash, "ledger_event_hashes": event_hashes,
        "evidence_bundle_hash": bundle_hash, "hard_witness_hashes": [hard_hash],
        "candidate_set_hash": candidate_set_hash, "candidate_generation_profile_hash": candidate_profile_hash,
        "pre_return_certificate_hash": pre_hash, "created_quorum_certificate_hash": created_q_hash,
        "pre_return_quorum_certificate_hash": pre_q_hash, "target_selector_profile_hash": selector_hash,
        "target_derivation_profile_hash": derivation_hash, "pre_target_conditioning_view_hash": view_hash,
        "pre_target_view_quorum_certificate_hash": view_q_hash, "entropy_profile_hash": entropy_hash,
        "causal_model_hash": causal_hash, "statistical_plan_hash": statistical_hash, "eprocess_state_hash": None,
        "witness_registry_hash": registry_hash, "registry_transition_certificate_hashes": [],
        "target_evidence_hash": target_hash, "publication_manifest_hash": publication_hash,
    }
    return s, package, {
        "candidate_profile": candidate_profile,
        "view": view,
        "registry": registry,
    }


class ReplayTests(unittest.TestCase):
    def test_honest_content_addressed_replay_reaches_structural_miss(self):
        with tempfile.TemporaryDirectory() as td:
            store, package, _ = build_fixture(Path(td))
            result = verify_replay_manifest(package, store.resolver())
            self.assertEqual(result["terminal_grade"], "NOT_ADMITTED", msg=f"HONEST_REPLAY_RESULT={result!r}")
            self.assertFalse(result["fail_open"])
            self.assertEqual(result["gate_results"].get("LEDGER_REPLAY"), "PASS")
            self.assertEqual(result["gate_results"].get("TARGET_DERIVATION_REPLAY"), "PASS")
            self.assertEqual(result["gate_results"].get("CAUSAL_D_SEPARATION"), "BLOCKED")

    def test_dangling_evidence_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            store, package, _ = build_fixture(Path(td))
            package["entropy_profile_hash"] = "f" * 64
            result = verify_replay_manifest(package, store.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
            self.assertEqual(result["gate_results"].get("EVIDENCE_RESOLUTION"), "FAIL")

    def test_post_created_operator_choice_fails_replay(self):
        with tempfile.TemporaryDirectory() as td:
            store, package, refs = build_fixture(Path(td))
            mutated = copy.deepcopy(refs["candidate_profile"])
            mutated["selection_freedom"]["operator_choice_after_created"] = True
            mutated_hash = store.protocol(mutated)
            package["candidate_generation_profile_hash"] = mutated_hash
            result = verify_replay_manifest(package, store.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")

    def test_post_hoc_conditioning_view_sanitization_fails(self):
        with tempfile.TemporaryDirectory() as td:
            store, package, refs = build_fixture(Path(td))
            sanitized = copy.deepcopy(refs["view"])
            sanitized["operator_state_evidence_hashes"] = []
            sanitized_hash = store.protocol(sanitized)
            package["pre_target_conditioning_view_hash"] = sanitized_hash
            result = verify_replay_manifest(package, store.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")

    def test_fault_model_rebinding_fails(self):
        with tempfile.TemporaryDirectory() as td:
            store, package, refs = build_fixture(Path(td))
            bad = copy.deepcopy(refs["registry"])
            bad["fault_model"]["q"] = 2
            bad_hash = store.protocol(bad)
            package["witness_registry_hash"] = bad_hash
            result = verify_replay_manifest(package, store.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")

    def test_same_failure_domain_sybil_fails(self):
        with tempfile.TemporaryDirectory() as td:
            store, package, refs = build_fixture(Path(td))
            bad = copy.deepcopy(refs["registry"])
            for i in range(3):
                bad["witnesses"][i]["failure_domain"] = "same-domain"
            bad_hash = store.protocol(bad)
            package["witness_registry_hash"] = bad_hash
            result = verify_replay_manifest(package, store.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
