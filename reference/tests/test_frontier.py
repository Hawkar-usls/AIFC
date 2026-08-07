import sys
import unittest
from fractions import Fraction
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from bindings import validate_target_derivation_bindings_v02  # noqa: E402
from frontier import (  # noqa: E402
    exact_hit_cap,
    experiment_genesis_hash,
    validate_candidate_generation_profile,
    validate_canonical_rational,
    validate_registry_transition,
    validate_registry_transition_set,
    validate_release_manifest_structure,
    zero_cap_outcome,
)

H0 = "0" * 64
H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64
H4 = "4" * 64


def candidate_profile(**overrides):
    base = {
        "schema": "AIFC/candidate-generation-profile/v1",
        "profile_id": "cgp-1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "policy_hash": H0,
        "created_slot_certificate_hash": H1,
        "generation_mode": "SINGLE_SHOT_AFTER_CERTIFIED_CREATED",
        "generator_identity": {
            "implementation_id": "generator-A",
            "implementation_version": "0.2",
            "code_or_image_hash": H2,
        },
        "pre_created_state_commitment": {
            "method": "external-state-hash",
            "content_hash": H3,
            "externally_certified": True,
        },
        "candidate_set_cardinality_upper_bound": 1,
        "selection_freedom": {
            "operator_choice_after_created": False,
            "operator_choice_after_generation": False,
            "hidden_pool_exclusion_basis": "Single-shot generator bound to certified slot.",
        },
        "external_evidence": [{"evidence_type": "EXECUTION_RECEIPT", "content_hash": H4}],
        "assumptions": [],
        "unresolved_assumptions": [],
        "admission_status": "ADMITTED",
    }
    base.update(overrides)
    return base


def target_profile(frozen=True):
    return {
        "schema": "AIFC/target-derivation-profile/v1",
        "profile_id": "tdp-1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "run_id": "run-1",
        "policy_hash": H0,
        "source_id": "beacon",
        "source_protocol_version": "v1",
        "raw_source_object_schema": "beacon/raw/v1",
        "target_selector_profile_hash": H1,
        "extraction": {"method": "JSON_POINTER_HEX_BYTES", "json_pointer": "/randomness"},
        "transformation": {
            "algorithm": "SHA-256",
            "framing": "AIFC_TYPED_LENGTH_PREFIXED_V1",
            "input_order": ["EXTRACTED_BYTES", "TARGET_EVENT_ID_UTF8"],
        },
        "domain_separator": "AIFC:TARGET:v1",
        "output_length_bits": 256,
        "frozen_before_target": frozen,
    }


def transition_receipt(role, registry_hash, body_hash, witness_id, experiment_id="exp-1"):
    return {
        "schema": "AIFC/registry-transition-receipt/v1",
        "experiment_id": experiment_id,
        "transition_body_hash": body_hash,
        "signing_registry_hash": registry_hash,
        "role": role,
        "witness_id": witness_id,
        "key_id": f"key-{witness_id}",
        "signature_algorithm": "Ed25519",
        "signature": "aa" * 64,
    }


def transition_quorum(role, registry_hash, body_hash, prefix, experiment_id="exp-1"):
    return {
        "schema": "AIFC/registry-transition-quorum/v1",
        "experiment_id": experiment_id,
        "role": role,
        "transition_body_hash": body_hash,
        "signing_registry_hash": registry_hash,
        "n": 4,
        "f": 1,
        "q": 3,
        "receipts": [
            transition_receipt(role, registry_hash, body_hash, f"{prefix}{i}", experiment_id)
            for i in range(3)
        ],
    }


def transition(next_hash=H2, body_hash=H3):
    body = {
        "schema": "AIFC/registry-transition-body/v1",
        "experiment_id": "exp-1",
        "previous_registry_sequence": 0,
        "previous_registry_hash": H1,
        "next_registry_sequence": 1,
        "next_registry_hash": next_hash,
    }
    return {
        "schema": "AIFC/registry-transition-certificate/v1",
        "transition_body": body,
        "transition_body_hash": body_hash,
        "old_registry_authorization": transition_quorum("OLD_REGISTRY_AUTHORIZATION", H1, body_hash, "old"),
        "new_registry_acceptance": transition_quorum("NEW_REGISTRY_ACCEPTANCE", next_hash, body_hash, "new"),
    }


class FrontierVerifierTests(unittest.TestCase):
    def test_genesis_hash_is_deterministic_and_domain_separated(self):
        got = experiment_genesis_hash("exp-1")
        self.assertEqual(len(got), 64)
        self.assertEqual(got, experiment_genesis_hash("exp-1"))
        self.assertNotEqual(got, experiment_genesis_hash("exp-2"))

    def test_canonical_rational_accepts_one_half(self):
        result, value = validate_canonical_rational(
            {"numerator_dec": "1", "denominator_dec": "2", "canonical_reduced": True}
        )
        self.assertTrue(result.ok)
        self.assertEqual(value, Fraction(1, 2))

    def test_noncanonical_rational_rejects_leading_zero(self):
        result, _ = validate_canonical_rational(
            {"numerator_dec": "01", "denominator_dec": "02", "canonical_reduced": True}
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "NONCANONICAL_RATIONAL_NUMERATOR")

    def test_noncanonical_rational_rejects_unreduced(self):
        result, _ = validate_canonical_rational(
            {"numerator_dec": "2", "denominator_dec": "4", "canonical_reduced": True}
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "NONCANONICAL_RATIONAL_NOT_REDUCED")

    def test_zero_cap_never_divides_by_zero(self):
        self.assertTrue(zero_cap_outcome(Fraction(0, 1), False).ok)
        hit = zero_cap_outcome(Fraction(0, 1), True)
        self.assertFalse(hit.ok)
        self.assertEqual(hit.code, "ZERO_CAP_HIT_FORWARD_NULL_PREMISE_CONTRADICTION")

    def test_exact_hit_cap_charges_multiplicity(self):
        self.assertEqual(exact_hit_cap(4, Fraction(1, 16)), Fraction(1, 4))

    def test_candidate_provenance_honest_profile_passes(self):
        self.assertTrue(validate_candidate_generation_profile(candidate_profile()).ok)

    def test_shadow_candidate_pool_fails_closed(self):
        p = candidate_profile()
        p["unresolved_assumptions"] = ["Pre-CREATED hidden pool cannot be excluded"]
        p["admission_status"] = "BLOCKED_SHADOW_POOL_NOT_EXCLUDED"
        result = validate_candidate_generation_profile(p)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "SHADOW_CANDIDATE_POOL_NOT_EXCLUDED")

    def test_post_created_operator_choice_fails(self):
        p = candidate_profile()
        p["selection_freedom"]["operator_choice_after_created"] = True
        result = validate_candidate_generation_profile(p)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "POST_CREATED_OPERATOR_CHOICE_NOT_CHARGED")

    def test_post_generation_candidate_choice_fails(self):
        p = candidate_profile()
        p["selection_freedom"]["operator_choice_after_generation"] = True
        result = validate_candidate_generation_profile(p)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "UNDECLARED_OR_DISALLOWED_POST_GENERATION_CANDIDATE_CHOICE")

    def test_target_derivation_v02_honest_bindings_pass(self):
        ph = H4
        profile = target_profile(True)
        pre = {"target_derivation_policy_hash": H0}
        ep = {"target_derivation_profile_hash": ph, "target_selector_profile_hash": H1, "conditioning_view_hash": H2}
        te = {"target_derivation_profile_hash": ph, "target_selector_profile_hash": H1, "conditioning_view_hash": H2}
        self.assertTrue(validate_target_derivation_bindings_v02(ph, profile, pre, ep, te).ok)

    def test_post_hoc_target_derivation_fails(self):
        result = validate_target_derivation_bindings_v02(
            H4,
            target_profile(False),
            {"target_derivation_policy_hash": H0},
            {"target_derivation_profile_hash": H4, "target_selector_profile_hash": H1, "conditioning_view_hash": H2},
            {"target_derivation_profile_hash": H4, "target_selector_profile_hash": H1, "conditioning_view_hash": H2},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "POST_HOC_TARGET_DERIVATION")

    def test_ambiguous_derivation_encoding_fails(self):
        p = target_profile(True)
        p["transformation"]["framing"] = "FREE_TEXT_CONCAT"
        result = validate_target_derivation_bindings_v02(
            H4,
            p,
            {"target_derivation_policy_hash": H0},
            {"target_derivation_profile_hash": H4, "target_selector_profile_hash": H1, "conditioning_view_hash": H2},
            {"target_derivation_profile_hash": H4, "target_selector_profile_hash": H1, "conditioning_view_hash": H2},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "AMBIGUOUS_DERIVATION_ENCODING")

    def test_joint_registry_transition_structurally_passes(self):
        result = validate_registry_transition(transition())
        self.assertTrue(result.ok)

    def test_registry_experiment_rebinding_fails(self):
        cert = transition()
        cert["new_registry_acceptance"]["experiment_id"] = "other-exp"
        result = validate_registry_transition(cert)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "REGISTRY_EXPERIMENT_REBINDING")

    def test_old_quorum_without_new_acceptance_fails(self):
        cert = transition()
        cert.pop("new_registry_acceptance")
        result = validate_registry_transition(cert)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "NEW_QUORUM_ACCEPTANCE_MISSING")

    def test_unsafe_registry_transition_quorum_fails(self):
        cert = transition()
        cert["old_registry_authorization"]["q"] = 2
        cert["old_registry_authorization"]["receipts"] = cert["old_registry_authorization"]["receipts"][:2]
        result = validate_registry_transition(cert)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "REGISTRY_TRANSITION_UNSAFE_QUORUM")

    def test_registry_reconfiguration_fork_fails_closed(self):
        result = validate_registry_transition_set([
            transition(next_hash=H2, body_hash=H3),
            transition(next_hash=H4, body_hash=H0),
        ])
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "REGISTRY_RECONFIGURATION_FORK")

    def test_frontier_cannot_admit_fake_frozen_pass(self):
        gate_ids = ["G1", "G2"]
        manifest = {
            "schema": "AIFC/release-manifest/v1",
            "gate_results": [
                {"gate_id": "G1", "result": "PASS", "evidence_hash": H1},
                {"gate_id": "G2", "result": "PASS", "evidence_hash": H2},
            ],
            "overall_status": "FROZEN_PASS",
        }
        result = validate_release_manifest_structure(manifest, gate_ids)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "FULL_RELEASE_EVIDENCE_RESOLUTION_NOT_IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
