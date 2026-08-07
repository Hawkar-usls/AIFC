import inspect
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
from signature_preimage_v05 import (  # noqa: E402
    SignaturePreimageError,
    build_signature_preimage,
    normative_policy,
    replay_signature_preimage,
)


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
            "store_id": "signature-preimage-replay-test",
            "entries": self.entries,
        })


def witness_registry(exp="exp-1"):
    return {
        "schema": "AIFC/witness-registry/v1",
        "registry_id": "r0",
        "experiment_id": exp,
        "registry_sequence": 0,
        "previous_registry_hash": registry_genesis_hash(exp),
        "transition_certificate_hash": None,
        "fault_model": {"n": 1, "f": 0, "q": 1, "independence_unit": "FAILURE_DOMAIN"},
        "witnesses": [{
            "witness_id": "w0",
            "failure_domain": "fd-0",
            "status": "ACTIVE",
            "keys": [{
                "key_id": "k0",
                "algorithm": "Ed25519",
                "public_key_encoding": "hex",
                "public_key": "01" * 32,
                "valid_from_registry_sequence": 0,
                "valid_until_registry_sequence": None,
                "status": "ACTIVE",
                "predecessor_key_id": None,
                "revocation_reason": None,
            }],
        }],
    }


def experiment_plan(exp, registry_hash, policy_hash):
    return {
        "schema": "AIFC/experiment-plan/v1",
        "experiment_id": exp,
        "protocol_version": "1.0-draft",
        "mode": "FIXED_HORIZON",
        "trial_creation_policy_hash": "1" * 64,
        "declared_trial_count": 1,
        "initial_witness_registry_hash": registry_hash,
        "signature_preimage_policy_hash": policy_hash,
        "candidate_generation_policy_hash": "2" * 64,
        "target_selector_policy_hash": "3" * 64,
        "target_derivation_policy_hash": "4" * 64,
        "entropy_policy_hash": "5" * 64,
        "causal_model_hash": "6" * 64,
        "statistical_plan_hash": "7" * 64,
        "publication_policy_hash": "8" * 64,
        "external_freshness_policy_hash": "9" * 64,
        "conditioning_view_policy_hash": "a" * 64,
        "allowed_registry_reconfiguration": False,
        "strongest_grade_exactly_one_target_derivation_per_trial": True,
        "frozen_before_first_created": True,
    }


class SignaturePreimageReplayV05Tests(unittest.TestCase):
    def build(self, root: Path):
        s = Store(root)
        exp = "exp-1"
        registry = witness_registry(exp)
        registry_hash = s.protocol(registry)
        policy = normative_policy(exp)
        policy_hash = s.protocol(policy)
        plan = experiment_plan(exp, registry_hash, policy_hash)
        plan_hash = s.protocol(plan)
        content = {
            "schema": "AIFC/hard-witness/v1",
            "experiment_id": exp,
            "run_id": "run-1",
            "trial_index": 1,
            "semantic_class": None,
            "payload128": "11" * 16,
            "nonce128": "22" * 16,
        }
        content_hash = s.protocol(content)
        receipt = {
            "schema": "AIFC/witness-receipt/v1",
            "experiment_id": exp,
            "trial_index": 1,
            "logical_position": "PRE_RETURN_FROZEN",
            "content_hash": content_hash,
            "registry_hash": registry_hash,
            "witness_id": "w0",
            "key_id": "k0",
            "signature_algorithm": "Ed25519",
            "signature": "ab" * 64,
        }
        return s, registry, registry_hash, policy, plan, plan_hash, content, receipt

    def test_strongest_replay_api_does_not_accept_claimant_semantic_metadata(self):
        params = inspect.signature(replay_signature_preimage).parameters
        self.assertNotIn("protocol_version", params)
        self.assertNotIn("content_schema", params)
        self.assertNotIn("registry_sequence", params)
        self.assertEqual(set(params), {"receipt", "experiment_plan_hash", "resolver"})

    def test_replay_derives_content_schema_registry_sequence_and_protocol_version(self):
        with tempfile.TemporaryDirectory() as td:
            s, registry, registry_hash, policy, plan, plan_hash, content, receipt = self.build(Path(td))
            replayed = replay_signature_preimage(
                receipt,
                experiment_plan_hash=plan_hash,
                resolver=s.resolver(),
            )
            expected = build_signature_preimage(
                receipt,
                policy=policy,
                protocol_version=plan["protocol_version"],
                content_schema=content["schema"],
                registry_sequence=registry["registry_sequence"],
            )
            self.assertEqual(replayed, expected)

    def test_experiment_plan_receipt_cannot_rebind_content_to_other_protocol_object(self):
        with tempfile.TemporaryDirectory() as td:
            s, registry, registry_hash, policy, plan, plan_hash, content, receipt = self.build(Path(td))
            other_hash = receipt["content_hash"]
            plan_receipt = {
                "schema": "AIFC/experiment-plan-receipt/v1",
                "experiment_id": "exp-1",
                "logical_position": "EXPERIMENT_PLAN_FROZEN",
                "content_hash": other_hash,
                "registry_hash": registry_hash,
                "witness_id": "w0",
                "key_id": "k0",
                "signature_algorithm": "Ed25519",
                "signature": "ab" * 64,
            }
            with self.assertRaises(SignaturePreimageError) as ctx:
                replay_signature_preimage(
                    plan_receipt,
                    experiment_plan_hash=plan_hash,
                    resolver=s.resolver(),
                )
            self.assertIn("EXPERIMENT_PLAN_CONTENT_REBINDING", str(ctx.exception))

    def test_content_experiment_rebinding_fails_before_preimage(self):
        with tempfile.TemporaryDirectory() as td:
            s, registry, registry_hash, policy, plan, plan_hash, content, receipt = self.build(Path(td))
            other = dict(content)
            other["experiment_id"] = "other-exp"
            other_hash = s.protocol(other)
            receipt = dict(receipt)
            receipt["content_hash"] = other_hash
            with self.assertRaises(SignaturePreimageError) as ctx:
                replay_signature_preimage(
                    receipt,
                    experiment_plan_hash=plan_hash,
                    resolver=s.resolver(),
                )
            self.assertIn("CONTENT_EXPERIMENT_REBINDING", str(ctx.exception))

    def test_registry_experiment_rebinding_fails_before_preimage(self):
        with tempfile.TemporaryDirectory() as td:
            s, registry, registry_hash, policy, plan, plan_hash, content, receipt = self.build(Path(td))
            other_registry = witness_registry("other-exp")
            other_registry_hash = s.protocol(other_registry)
            receipt = dict(receipt)
            receipt["registry_hash"] = other_registry_hash
            with self.assertRaises(SignaturePreimageError) as ctx:
                replay_signature_preimage(
                    receipt,
                    experiment_plan_hash=plan_hash,
                    resolver=s.resolver(),
                )
            self.assertIn("REGISTRY_EXPERIMENT_REBINDING", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
