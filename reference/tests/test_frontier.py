import sys
import unittest
from fractions import Fraction
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from frontier import (  # noqa: E402
    exact_hit_cap,
    experiment_genesis_hash,
    validate_candidate_generation_profile,
    validate_canonical_rational,
    validate_registry_transition,
    validate_registry_transition_set,
    validate_target_derivation_bindings,
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
        "created_slot_certificate_hash": H1,
        "generation_mode": "SINGLE_SHOT_AFTER_CERTIFIED_CREATED",
        "generator_identity": {
            "implementation_id": "generator-A",
            "implementation_version": "0.1",
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
            "hidden_pool_exclusion_basis": "Single-shot generator bound to certified slot and external execution evidence.",
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
        "source_id": "beacon",
        "source_protocol_version": "v1",
        "raw_source_object_schema": "beacon/raw/v1",
        "event_selector_hash": H1,
        "extraction_rule": "extract field randomness",
        "transformation_rule": {"algorithm": "SHA-256", "input_order": ["raw.randomness", "event_id"]},
        "domain_separator": "AIFC:TARGET:v1",
        "output_length_bits": 256,
        "frozen_before_target": frozen,
    }


def transition_receipt(role, registry_hash, body_hash, witness_id):
    return {
        "schema": "AIFC/registry-transition-receipt/v1",
        "experiment_id": "exp-1",
        "transition_body_hash": body_hash,
        "signing_registry_hash": registry_hash,
        "role": role,
        "witness_id": witness_id,
        "key_id": f"key-{witness_id}",
        "signature_algorithm": "Ed25519",
        "signature": "aa" * 64,
    }


def transition_quorum(role, registry_hash, body_hash, prefix):
    # n=4,f=1,q=3 is safe: 2q=6 > 5=n+f.
    return {
        "schema": "AIFC/registry-transition-quorum/v1",
        "experiment_id": "exp-1",
        "role": role,
        "transition_body_hash": body_hash,
        "signing_registry_hash": registry_hash,
        "n": 4,
        "f": 1,
        "q": 3,
        "receipts": [
            transition_receipt(role, registry_hash, body_hash, f"{prefix}{i}")
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
        "old_registry_authorization": transition_quorum(
            "OLD_REGISTRY_AUTHORIZATION", H1, body_hash, "old"
        ),
        "new_registry_acceptance": transition_quorum(
            "NEW_REGISTRY_ACCEPTANCE", next_hash, body_hash, "new"
        ),
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
        miss = zero_cap_outcome(Fraction(0, 1), False)
        hit = zero_cap_outcome(Fraction(0, 1), True)
        self.assertTrue(miss.ok)
        self.assertFalse(hit.ok)
        self.assertEqual(hit.code, "ZERO_CAP_HIT_FORWARD_NULL_PREMISE_CONTRADICTION")

    def test_exact_hit_cap_charges_multiplicity(self):
        self.assertEqual(exact_hit_cap(4, Fraction(1, 16)), Fraction(1, 4))

    def test_candidate_provenance_honest_profile_passes(self):
        result = validate_candidate_generation_profile(candidate_profile())
        self.assertTrue(result.ok)

    def test_shadow_candidate_pool_fails_closed(self):
        p = candidate_profile()
        p["unresolved_assumptions"] = ["Pre-CREATED hidden candidate pool cannot be excluded"]
        p["admission_status"] = "BLOCKED_SHADOW_POOL_NOT_EXCLUDED"
        result = validate_candidate_generation_profile(p)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "SHADOW_CANDIDATE_POOL_NOT_EXCLUDED")

    def test_post_generation_candidate_choice_fails(self):
        p = candidate_profile()
        p["selection_freedom"]["operator_choice_after_generation"] = True
        result = validate_candidate_generation_profile(p)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "UNDECLARED_OR_DISALLOWED_POST_GENERATION_CANDIDATE_CHOICE")

    def test_target_derivation_honest_bindings_pass(self):
        ph = H4
        profile = target_profile(True)
        pre = {"target_derivation_profile_hash": ph}
        ep = {"target_derivation_profile_hash": ph}
        te = {
            "target_derivation_profile_hash": ph,
            "raw_source_object_hash": H3,
            "target_selector_hash": H1,
        }
        result = validate_target_derivation_bindings(ph, profile, pre, ep, te)
        self.assertTrue(result.ok)

    def test_post_hoc_target_derivation_fails(self):
        ph = H4
        profile = target_profile(False)
        pre = {"target_derivation_profile_hash": ph}
        ep = {"target_derivation_profile_hash": ph}
        te = {
            "target_derivation_profile_hash": ph,
            "raw_source_object_hash": H3,
            "target_selector_hash": H1,
        }
        result = validate_target_derivation_bindings(ph, profile, pre, ep, te)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "POST_HOC_TARGET_DERIVATION")

    def test_target_derivation_rebinding_fails(self):
        ph = H4
        result = validate_target_derivation_bindings(
            ph,
            target_profile(True),
            {"target_derivation_profile_hash": ph},
            {"target_derivation_profile_hash": H0},
            {"target_derivation_profile_hash": ph, "raw_source_object_hash": H3, "target_selector_hash": H1},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "TARGET_DERIVATION_PROFILE_REBINDING")

    def test_joint_registry_transition_structurally_passes(self):
        result = validate_registry_transition(transition())
        self.assertTrue(result.ok)
        self.assertEqual(result.code, "REGISTRY_TRANSITION_STRUCTURAL_PASS")

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
        a = transition(next_hash=H2, body_hash=H3)
        b = transition(next_hash=H4, body_hash=H0)
        result = validate_registry_transition_set([a, b])
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "REGISTRY_RECONFIGURATION_FORK")


if __name__ == "__main__":
    unittest.main()
