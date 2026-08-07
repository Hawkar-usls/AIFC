import copy
import sys
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from signature_preimage import (  # noqa: E402
    SignaturePreimageError,
    compile_signature_preimage,
    signature_preimage_sha256,
)


def policy():
    return {
        "schema": "AIFC/signature-preimage-policy/v1",
        "policy_id": "AIFC-ED25519-SIGNATURE-PREIMAGE-POLICY-V1",
        "experiment_id": "exp-1",
        "protocol_version": "1.0-draft",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "signature_algorithm": "Ed25519",
        "domain_separator": "AIFC:SIGNATURE_PREIMAGE:v1",
        "framing": "TAG_U8_LENGTH_U64BE_V1",
        "prehash_mode": "NONE_DIRECT_ED25519",
        "public_key_encoding": "LOWERCASE_HEX_32_BYTES",
        "signature_encoding": "LOWERCASE_HEX_64_BYTES",
        "timestamp_semantics": "SIGNED_IF_PRESENT_INTEGRITY_ONLY_NOT_FRESHNESS",
        "field_tags": {
            "receipt_schema": 1,
            "protocol_version": 2,
            "signature_profile_id": 3,
            "scope_kind": 4,
            "experiment_id": 5,
            "trial_index_or_absent": 6,
            "logical_position_or_transition_role": 7,
            "content_schema": 8,
            "content_hash": 9,
            "registry_hash": 10,
            "registry_sequence": 11,
            "witness_id": 12,
            "key_id": 13,
            "timestamp_present": 14,
            "timestamp_utf8": 15,
        },
        "receipt_profiles": {
            "trial_witness": {
                "receipt_schema": "AIFC/witness-receipt/v1",
                "scope_kind": "TRIAL",
                "position_source": "logical_position",
                "content_hash_source": "content_hash",
                "registry_hash_source": "registry_hash",
            },
            "experiment_plan": {
                "receipt_schema": "AIFC/experiment-plan-receipt/v1",
                "scope_kind": "EXPERIMENT",
                "position_source": "logical_position",
                "content_hash_source": "content_hash",
                "registry_hash_source": "registry_hash",
            },
            "registry_transition": {
                "receipt_schema": "AIFC/registry-transition-receipt/v1",
                "scope_kind": "EXPERIMENT",
                "position_source": "role",
                "content_hash_source": "transition_body_hash",
                "registry_hash_source": "signing_registry_hash",
            },
        },
        "frozen_before_first_created": True,
    }


def trial_receipt():
    return {
        "schema": "AIFC/witness-receipt/v1",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "experiment_id": "exp-1",
        "trial_index": 7,
        "logical_position": "PRE_RETURN_FROZEN",
        "content_schema": "AIFC/trial-ledger-event/v1",
        "content_hash": "11" * 32,
        "registry_hash": "22" * 32,
        "registry_sequence": 3,
        "witness_id": "w0",
        "key_id": "k0",
        "signature_algorithm": "Ed25519",
        "signature": "ab" * 64,
        "wall_clock_timestamp": "2026-08-07T12:34:56Z",
    }


def plan_receipt():
    return {
        "schema": "AIFC/experiment-plan-receipt/v1",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "experiment_id": "exp-1",
        "logical_position": "EXPERIMENT_PLAN_FROZEN",
        "content_schema": "AIFC/experiment-plan/v1",
        "content_hash": "33" * 32,
        "registry_hash": "44" * 32,
        "registry_sequence": 0,
        "witness_id": "w0",
        "key_id": "k0",
        "signature_algorithm": "Ed25519",
        "signature": "cd" * 64,
        "wall_clock_timestamp": None,
    }


def transition_receipt():
    return {
        "schema": "AIFC/registry-transition-receipt/v1",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "experiment_id": "exp-1",
        "transition_body_hash": "55" * 32,
        "content_schema": "AIFC/registry-transition-body/v1",
        "signing_registry_hash": "66" * 32,
        "registry_sequence": 4,
        "role": "OLD_REGISTRY_AUTHORIZATION",
        "witness_id": "w0",
        "key_id": "k0",
        "signature_algorithm": "Ed25519",
        "signature": "ef" * 64,
        "wall_clock_timestamp": None,
    }


class SignaturePreimageTests(unittest.TestCase):
    def test_known_trial_vector(self):
        self.assertEqual(
            signature_preimage_sha256(trial_receipt(), policy()),
            "2c2ad0fd73ebac49a048038941fc4cae0b616cb8ef8a7b174acc63c7c63b1297",
        )

    def test_signature_bytes_are_not_self_signed(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["signature"] = "00" * 64
        self.assertEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_cross_protocol_signature_replay_changes_preimage(self):
        a = compile_signature_preimage(trial_receipt(), policy())
        other = policy()
        other["protocol_version"] = "1.0-draft-other"
        b = compile_signature_preimage(trial_receipt(), other)
        self.assertNotEqual(a, b)

    def test_cross_receipt_type_replay_changes_preimage(self):
        trial = compile_signature_preimage(trial_receipt(), policy())
        plan = compile_signature_preimage(plan_receipt(), policy())
        transition = compile_signature_preimage(transition_receipt(), policy())
        self.assertEqual(len({trial, plan, transition}), 3)

    def test_cross_experiment_signature_replay_is_rejected(self):
        bad = trial_receipt()
        bad["experiment_id"] = "exp-2"
        with self.assertRaises(SignaturePreimageError) as ctx:
            compile_signature_preimage(bad, policy())
        self.assertIn("CROSS_EXPERIMENT_SIGNATURE_REPLAY", str(ctx.exception))

    def test_cross_trial_signature_replay_changes_preimage(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["trial_index"] = 8
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_logical_position_rebinding_changes_preimage(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["logical_position"] = "TARGET_ARMED"
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_content_schema_rebinding_changes_preimage(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["content_schema"] = "AIFC/pre-target-conditioning-view/v1"
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_registry_rebinding_changes_preimage(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["registry_hash"] = "77" * 32
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_registry_sequence_rebinding_changes_preimage(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["registry_sequence"] = 4
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_witness_id_substitution_changes_preimage(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["witness_id"] = "w1"
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_key_id_substitution_changes_preimage(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["key_id"] = "k1"
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_transition_role_rebinding_changes_preimage(self):
        a = transition_receipt()
        b = copy.deepcopy(a)
        b["role"] = "NEW_REGISTRY_ACCEPTANCE"
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_timestamp_tamper_changes_preimage(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["wall_clock_timestamp"] = "2026-08-07T12:34:57Z"
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_timestamp_absence_is_explicit(self):
        a = trial_receipt()
        b = copy.deepcopy(a)
        b["wall_clock_timestamp"] = None
        self.assertNotEqual(compile_signature_preimage(a, policy()), compile_signature_preimage(b, policy()))

    def test_signature_encoding_malleability_is_rejected_by_schema(self):
        bad = trial_receipt()
        bad["signature"] = ("AB" * 64)
        with self.assertRaises(SignaturePreimageError) as ctx:
            compile_signature_preimage(bad, policy())
        self.assertIn("RECEIPT_SCHEMA_INVALID", str(ctx.exception))

    def test_profile_id_substitution_is_rejected(self):
        bad = trial_receipt()
        bad["signature_profile_id"] = "OTHER"
        with self.assertRaises(SignaturePreimageError) as ctx:
            compile_signature_preimage(bad, policy())
        self.assertIn("RECEIPT_SCHEMA_INVALID", str(ctx.exception))

    def test_policy_field_tag_rebinding_is_rejected(self):
        bad_policy = policy()
        bad_policy["field_tags"]["key_id"] = 14
        with self.assertRaises(SignaturePreimageError) as ctx:
            compile_signature_preimage(trial_receipt(), bad_policy)
        self.assertIn("SIGNATURE_POLICY_INVALID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
