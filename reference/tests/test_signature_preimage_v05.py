import copy
import hashlib
import sys
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from signature_preimage_v05 import (  # noqa: E402
    DOMAIN,
    SignaturePreimageError,
    build_signature_preimage,
    normative_policy,
)


class SignaturePreimageV05Tests(unittest.TestCase):
    def setUp(self):
        self.policy = normative_policy("exp-1")
        self.receipt = {
            "schema": "AIFC/witness-receipt/v1",
            "experiment_id": "exp-1",
            "trial_index": 7,
            "logical_position": "PRE_RETURN_FROZEN",
            "content_hash": "11" * 32,
            "registry_hash": "22" * 32,
            "witness_id": "w0",
            "key_id": "k0",
            "signature_algorithm": "Ed25519",
            "signature": "ab" * 64,
            "wall_clock_timestamp": "2026-08-07T18:00:00Z",
        }
        self.kwargs = {
            "policy": self.policy,
            "protocol_version": "1.0-draft",
            "content_schema": "AIFC/trial-ledger-event/v1",
            "registry_sequence": 3,
        }

    def preimage(self, receipt=None, **overrides):
        kwargs = dict(self.kwargs)
        kwargs.update(overrides)
        return build_signature_preimage(receipt or self.receipt, **kwargs)

    def test_golden_vector_is_byte_stable(self):
        actual = self.preimage()
        self.assertTrue(actual.startswith(DOMAIN))
        self.assertEqual(
            hashlib.sha256(actual).hexdigest(),
            "e4ec24fa3b8d4ce0f423dad82fb6d4c1b2e371119309aee81b22d6e0188df117",
        )

    def test_cross_receipt_type_replay_changes_preimage(self):
        other = {
            "schema": "AIFC/experiment-plan-receipt/v1",
            "experiment_id": "exp-1",
            "logical_position": "EXPERIMENT_PLAN_FROZEN",
            "content_hash": self.receipt["content_hash"],
            "registry_hash": self.receipt["registry_hash"],
            "witness_id": "w0",
            "key_id": "k0",
            "signature_algorithm": "Ed25519",
            "signature": "ab" * 64,
            "wall_clock_timestamp": "2026-08-07T18:00:00Z",
        }
        self.assertNotEqual(self.preimage(), self.preimage(other, content_schema="AIFC/experiment-plan/v1"))

    def test_each_security_binding_changes_exact_preimage(self):
        baseline = self.preimage()
        mutations = [
            ("CROSS_EXPERIMENT_SIGNATURE_REPLAY", {"experiment_id": "exp-2"}, {"policy": normative_policy("exp-2")}),
            ("CROSS_TRIAL_SIGNATURE_REPLAY", {"trial_index": 8}, {}),
            ("LOGICAL_POSITION_REBINDING", {"logical_position": "TARGET_ARMED"}, {}),
            ("REGISTRY_REBINDING", {"registry_hash": "33" * 32}, {}),
            ("WITNESS_ID_SUBSTITUTION", {"witness_id": "w1"}, {}),
            ("KEY_ID_SUBSTITUTION", {"key_id": "k1"}, {}),
            ("TIMESTAMP_TAMPER", {"wall_clock_timestamp": "2026-08-07T18:00:01Z"}, {}),
        ]
        for attack, fields, kwargs in mutations:
            with self.subTest(attack=attack):
                receipt = copy.deepcopy(self.receipt)
                receipt.update(fields)
                self.assertNotEqual(baseline, self.preimage(receipt, **kwargs))

        self.assertNotEqual(baseline, self.preimage(registry_sequence=4), "REGISTRY_SEQUENCE_REBINDING")
        self.assertNotEqual(
            baseline,
            self.preimage(content_schema="AIFC/target-evidence/v1"),
            "CROSS_CONTENT_SCHEMA_REPLAY",
        )
        self.assertNotEqual(
            baseline,
            self.preimage(protocol_version="1.0-other"),
            "CROSS_PROTOCOL_SIGNATURE_REPLAY",
        )

    def test_registry_transition_role_rebinding_changes_preimage(self):
        receipt = {
            "schema": "AIFC/registry-transition-receipt/v1",
            "experiment_id": "exp-1",
            "transition_body_hash": "44" * 32,
            "signing_registry_hash": "55" * 32,
            "role": "OLD_REGISTRY_AUTHORIZATION",
            "witness_id": "w0",
            "key_id": "k0",
            "signature_algorithm": "Ed25519",
            "signature": "ab" * 64,
            "wall_clock_timestamp": None,
        }
        old = self.preimage(receipt, content_schema="AIFC/registry-transition-body/v1")
        receipt["role"] = "NEW_REGISTRY_ACCEPTANCE"
        new = self.preimage(receipt, content_schema="AIFC/registry-transition-body/v1")
        self.assertNotEqual(old, new, "TRANSITION_ROLE_REBINDING")

    def test_explicit_absence_differs_from_present_timestamp_and_trial(self):
        no_time = copy.deepcopy(self.receipt)
        no_time["wall_clock_timestamp"] = None
        self.assertNotEqual(self.preimage(), self.preimage(no_time))

        experiment_receipt = {
            "schema": "AIFC/experiment-plan-receipt/v1",
            "experiment_id": "exp-1",
            "logical_position": "EXPERIMENT_PLAN_FROZEN",
            "content_hash": "11" * 32,
            "registry_hash": "22" * 32,
            "witness_id": "w0",
            "key_id": "k0",
            "signature_algorithm": "Ed25519",
            "signature": "ab" * 64,
        }
        exp_preimage = self.preimage(experiment_receipt, content_schema="AIFC/experiment-plan/v1")
        self.assertNotEqual(exp_preimage, self.preimage())

    def test_claimant_defined_policy_is_rejected(self):
        bad = copy.deepcopy(self.policy)
        bad["ed25519_variant"] = "Ed25519ph"
        with self.assertRaises(SignaturePreimageError) as ctx:
            self.preimage(policy=bad)
        self.assertIn("NON_NORMATIVE_SIGNATURE_PREIMAGE_POLICY", str(ctx.exception))

    def test_unsupported_receipt_type_fails_closed(self):
        bad = copy.deepcopy(self.receipt)
        bad["schema"] = "AIFC/future-receipt/v1"
        with self.assertRaises(SignaturePreimageError) as ctx:
            self.preimage(bad)
        self.assertIn("UNSUPPORTED_RECEIPT_SCHEMA", str(ctx.exception))

    def test_hash_text_must_be_canonical_lowercase(self):
        bad = copy.deepcopy(self.receipt)
        bad["content_hash"] = ("AA" * 32)
        with self.assertRaises(SignaturePreimageError) as ctx:
            self.preimage(bad)
        self.assertIn("EXPECTED_LOWERCASE_HEX_32_BYTES", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
