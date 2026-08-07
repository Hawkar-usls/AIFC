import copy
import sys
import tempfile
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import canonical_json_bytes  # noqa: E402
from canonical_v02 import protocol_hash_v02  # noqa: E402
from replay import registry_genesis_hash  # noqa: E402
from resolver_v02 import EvidenceResolverV02  # noqa: E402
from signature_policy_admission import SignaturePolicyAdmissionError, replay_signature_preimages  # noqa: E402


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.entries = []
        (root / "objects").mkdir(parents=True, exist_ok=True)

    def protocol(self, obj):
        h = protocol_hash_v02(obj)
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

    def resolver(self):
        return EvidenceResolverV02(self.root, {
            "schema": "AIFC/evidence-store-index/v1",
            "store_id": "sig-preimage-test",
            "entries": self.entries,
        })


def signature_policy(exp="exp-1", protocol_version="1.0-draft"):
    return {
        "schema": "AIFC/signature-preimage-policy/v1",
        "policy_id": "AIFC-ED25519-SIGNATURE-PREIMAGE-POLICY-V1",
        "experiment_id": exp,
        "protocol_version": protocol_version,
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


def registry(exp="exp-1"):
    witnesses = []
    for i in range(4):
        witnesses.append({
            "witness_id": f"w{i}",
            "failure_domain": f"fd-{i}",
            "status": "ACTIVE",
            "keys": [{
                "key_id": f"k{i}",
                "algorithm": "Ed25519",
                "public_key_encoding": "hex",
                "public_key": f"{i+1:02x}" * 32,
                "valid_from_registry_sequence": 0,
                "valid_until_registry_sequence": None,
                "status": "ACTIVE",
                "predecessor_key_id": None,
                "revocation_reason": None,
            }],
        })
    return {
        "schema": "AIFC/witness-registry/v1",
        "registry_id": "r0",
        "experiment_id": exp,
        "registry_sequence": 0,
        "previous_registry_hash": registry_genesis_hash(exp),
        "transition_certificate_hash": None,
        "fault_model": {"n": 4, "f": 1, "q": 3, "independence_unit": "FAILURE_DOMAIN"},
        "witnesses": witnesses,
    }


def plan(exp, registry_hash, policy_hash):
    return {
        "schema": "AIFC/experiment-plan/v1",
        "experiment_id": exp,
        "protocol_version": "1.0-draft",
        "mode": "FIXED_HORIZON",
        "trial_creation_policy_hash": "10" * 32,
        "declared_trial_count": 1,
        "initial_witness_registry_hash": registry_hash,
        "candidate_generation_policy_hash": "20" * 32,
        "target_selector_policy_hash": "30" * 32,
        "target_derivation_policy_hash": "40" * 32,
        "entropy_policy_hash": "50" * 32,
        "signature_preimage_policy_hash": policy_hash,
        "causal_model_hash": "60" * 32,
        "statistical_plan_hash": "70" * 32,
        "publication_policy_hash": "80" * 32,
        "external_freshness_policy_hash": "90" * 32,
        "conditioning_view_policy_hash": "a0" * 32,
        "allowed_registry_reconfiguration": False,
        "strongest_grade_exactly_one_target_derivation_per_trial": True,
        "frozen_before_first_created": True,
    }


def plan_receipts(exp, plan_hash, registry_hash):
    return [{
        "schema": "AIFC/experiment-plan-receipt/v1",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "experiment_id": exp,
        "logical_position": "EXPERIMENT_PLAN_FROZEN",
        "content_schema": "AIFC/experiment-plan/v1",
        "content_hash": plan_hash,
        "registry_hash": registry_hash,
        "registry_sequence": 0,
        "witness_id": f"w{i}",
        "key_id": f"k{i}",
        "signature_algorithm": "Ed25519",
        "signature": "ab" * 64,
        "wall_clock_timestamp": None,
    } for i in range(3)]


def trial_receipts(exp, trial, position, content_hash, content_schema, registry_hash):
    return [{
        "schema": "AIFC/witness-receipt/v1",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "experiment_id": exp,
        "trial_index": trial,
        "logical_position": position,
        "content_schema": content_schema,
        "content_hash": content_hash,
        "registry_hash": registry_hash,
        "registry_sequence": 0,
        "witness_id": f"w{i}",
        "key_id": f"k{i}",
        "signature_algorithm": "Ed25519",
        "signature": "cd" * 64,
        "wall_clock_timestamp": None,
    } for i in range(3)]


def build(root: Path):
    s = Store(root)
    exp = "exp-1"
    reg_hash = s.protocol(registry(exp))
    policy_hash = s.protocol(signature_policy(exp))
    p = plan(exp, reg_hash, policy_hash)
    p_hash = s.protocol(p)

    plan_q = {
        "schema": "AIFC/experiment-plan-quorum/v1",
        "experiment_id": exp,
        "logical_position": "EXPERIMENT_PLAN_FROZEN",
        "content_hash": p_hash,
        "registry_hash": reg_hash,
        "n": 4, "f": 1, "q": 3,
        "receipts": plan_receipts(exp, p_hash, reg_hash),
    }
    plan_q_hash = s.protocol(plan_q)

    content_hashes = []
    for idx in range(3):
        hard = {
            "schema": "AIFC/hard-witness/v1",
            "experiment_id": exp,
            "run_id": "run-1",
            "trial_index": 1,
            "semantic_class": None,
            "payload128": f"{idx+1:02x}" * 16,
            "nonce128": f"{idx+4:02x}" * 16,
        }
        content_hashes.append(s.protocol(hard))

    positions = ["CREATED", "PRE_RETURN_FROZEN", "PRE_TARGET_VIEW_FROZEN"]
    q_hashes = []
    quorums = []
    for position, content_hash in zip(positions, content_hashes):
        q = {
            "schema": "AIFC/quorum-certificate/v1",
            "experiment_id": exp,
            "trial_index": 1,
            "logical_position": position,
            "content_hash": content_hash,
            "registry_hash": reg_hash,
            "n": 4, "f": 1, "q": 3,
            "receipts": trial_receipts(exp, 1, position, content_hash, "AIFC/hard-witness/v1", reg_hash),
        }
        quorums.append(q)
        q_hashes.append(s.protocol(q))

    manifest = {
        "experiment_plan_hash": p_hash,
        "experiment_plan_quorum_certificate_hash": plan_q_hash,
        "created_quorum_certificate_hash": q_hashes[0],
        "pre_return_quorum_certificate_hash": q_hashes[1],
        "pre_target_view_quorum_certificate_hash": q_hashes[2],
        "registry_transition_certificate_hashes": [],
    }
    return s, manifest, quorums


class SignaturePolicyAdmissionTests(unittest.TestCase):
    def test_honest_preimage_replay_reconstructs_all_twelve_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, _ = build(Path(td))
            summary = replay_signature_preimages(manifest, s.resolver())
            self.assertEqual(summary.receipt_count, 12)
            self.assertEqual(len(set(summary.preimage_sha256s)), 12)

    def test_registry_sequence_rebinding_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, quorums = build(Path(td))
            bad = copy.deepcopy(quorums[0])
            bad["receipts"][0]["registry_sequence"] = 1
            manifest["created_quorum_certificate_hash"] = s.protocol(bad)
            with self.assertRaises(SignaturePolicyAdmissionError) as ctx:
                replay_signature_preimages(manifest, s.resolver())
            self.assertIn("REGISTRY_SEQUENCE_REBINDING", str(ctx.exception))

    def test_cross_trial_signature_replay_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, quorums = build(Path(td))
            bad = copy.deepcopy(quorums[1])
            bad["receipts"][0]["trial_index"] = 2
            manifest["pre_return_quorum_certificate_hash"] = s.protocol(bad)
            with self.assertRaises(SignaturePolicyAdmissionError) as ctx:
                replay_signature_preimages(manifest, s.resolver())
            self.assertIn("CROSS_TRIAL_SIGNATURE_REPLAY", str(ctx.exception))

    def test_content_schema_rebinding_is_rejected_by_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, quorums = build(Path(td))
            bad = copy.deepcopy(quorums[2])
            bad["receipts"][0]["content_schema"] = "AIFC/candidate-set/v1"
            manifest["pre_target_view_quorum_certificate_hash"] = s.protocol(bad)
            with self.assertRaises(Exception) as ctx:
                replay_signature_preimages(manifest, s.resolver())
            self.assertIn("EXPECTED_SCHEMA_MISMATCH", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
