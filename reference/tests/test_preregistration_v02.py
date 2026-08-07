import copy
import sys
import tempfile
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import canonical_json_bytes  # noqa: E402
from canonical_v02 import protocol_hash_v02  # noqa: E402
from frontier import experiment_genesis_hash  # noqa: E402
from preregistration_v02 import verify_plan_preregistration  # noqa: E402
from replay import registry_genesis_hash  # noqa: E402
from resolver_v02 import EvidenceResolverV02  # noqa: E402


class StoreV02:
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
            "store_id": "prereg-test",
            "entries": self.entries,
        })


def registry(exp="exp-1"):
    ws = []
    for i in range(4):
        ws.append({
            "witness_id": f"w{i}",
            "failure_domain": f"fd-{i}",
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
        "registry_id": "r0",
        "experiment_id": exp,
        "registry_sequence": 0,
        "previous_registry_hash": registry_genesis_hash(exp),
        "transition_certificate_hash": None,
        "fault_model": {"n": 4, "f": 1, "q": 3, "independence_unit": "FAILURE_DOMAIN"},
        "witnesses": ws,
    }


def plan(exp, registry_hash):
    return {
        "schema": "AIFC/experiment-plan/v1",
        "experiment_id": exp,
        "protocol_version": "1.0-draft",
        "mode": "FIXED_HORIZON",
        "trial_creation_policy_hash": "1" * 64,
        "declared_trial_count": 1,
        "initial_witness_registry_hash": registry_hash,
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


def plan_quorum(exp, plan_hash, registry_hash):
    receipts = []
    for i in range(3):
        receipts.append({
            "schema": "AIFC/experiment-plan-receipt/v1",
            "experiment_id": exp,
            "logical_position": "EXPERIMENT_PLAN_FROZEN",
            "content_hash": plan_hash,
            "registry_hash": registry_hash,
            "witness_id": f"w{i}",
            "key_id": f"k{i}",
            "signature_algorithm": "Ed25519",
            "signature": "ab" * 64,
        })
    return {
        "schema": "AIFC/experiment-plan-quorum/v1",
        "experiment_id": exp,
        "logical_position": "EXPERIMENT_PLAN_FROZEN",
        "content_hash": plan_hash,
        "registry_hash": registry_hash,
        "n": 4,
        "f": 1,
        "q": 3,
        "receipts": receipts,
    }


def created(exp, plan_hash, plan_q_hash):
    return {
        "schema": "AIFC/trial-ledger-event/v1",
        "experiment_id": exp,
        "event_index": 0,
        "trial_index": 1,
        "run_id": "run-1",
        "transition_ordinal": 0,
        "state_from": None,
        "state_to": "CREATED",
        "terminal_subtype": None,
        "previous_event_hash": experiment_genesis_hash(exp),
        "prerequisite_certificate_hash": plan_q_hash,
        "payload_hash": plan_hash,
        "evidence_bundle_hash": None,
        "reason_code": "CREATE_SLOT",
    }


def build(root: Path):
    s = StoreV02(root)
    exp = "exp-1"
    reg = registry(exp)
    reg_hash = s.protocol(reg)
    p = plan(exp, reg_hash)
    p_hash = s.protocol(p)
    q = plan_quorum(exp, p_hash, reg_hash)
    q_hash = s.protocol(q)
    c = created(exp, p_hash, q_hash)
    c_hash = s.protocol(c)
    package = {
        "schema": "AIFC/replay-package/v0.2",
        "experiment_id": exp,
        "subject_trial_index": 1,
        "experiment_plan_hash": p_hash,
        "experiment_plan_quorum_certificate_hash": q_hash,
        "ledger_event_hashes": [c_hash],
        "evidence_bundle_hash": "0" * 64,
    }
    return s, package, reg, p, q, c


class PlanPreregistrationTests(unittest.TestCase):
    def test_plan_quorum_precedes_created(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, *_ = build(Path(td))
            self.assertIsNone(verify_plan_preregistration(package, s.resolver()))

    def test_created_without_plan_quorum_prerequisite_fails(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, reg, p, q, c = build(Path(td))
            bad = copy.deepcopy(c)
            bad["prerequisite_certificate_hash"] = "f" * 64
            package["ledger_event_hashes"] = [s.protocol(bad)]
            result = verify_plan_preregistration(package, s.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
            self.assertTrue(any("EXPERIMENT_PLAN_NOT_CERTIFIED_BEFORE_CREATED" in x for x in result["failure_codes"]))

    def test_plan_quorum_fault_model_rebinding_fails(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, reg, p, q, c = build(Path(td))
            bad_q = copy.deepcopy(q)
            bad_q["q"] = 2
            bad_q_hash = s.protocol(bad_q)
            package["experiment_plan_quorum_certificate_hash"] = bad_q_hash
            bad_c = copy.deepcopy(c)
            bad_c["prerequisite_certificate_hash"] = bad_q_hash
            package["ledger_event_hashes"] = [s.protocol(bad_c)]
            result = verify_plan_preregistration(package, s.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
            self.assertTrue(any("PLAN_QUORUM_FAULT_MODEL_REBINDING" in x for x in result["failure_codes"]))

    def test_plan_quorum_same_failure_domain_fails(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, reg, p, q, c = build(Path(td))
            bad_reg = copy.deepcopy(reg)
            for i in range(3):
                bad_reg["witnesses"][i]["failure_domain"] = "shared"
            bad_reg_hash = s.protocol(bad_reg)
            bad_plan = copy.deepcopy(p)
            bad_plan["initial_witness_registry_hash"] = bad_reg_hash
            bad_plan_hash = s.protocol(bad_plan)
            bad_q = plan_quorum("exp-1", bad_plan_hash, bad_reg_hash)
            bad_q_hash = s.protocol(bad_q)
            bad_c = created("exp-1", bad_plan_hash, bad_q_hash)
            package["experiment_plan_hash"] = bad_plan_hash
            package["experiment_plan_quorum_certificate_hash"] = bad_q_hash
            package["ledger_event_hashes"] = [s.protocol(bad_c)]
            result = verify_plan_preregistration(package, s.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
            self.assertTrue(any("FAILURE_DOMAINS" in x or "SYBIL" in x for x in result["failure_codes"]))

    def test_plan_receipt_experiment_rebinding_fails(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, reg, p, q, c = build(Path(td))
            bad_q = copy.deepcopy(q)
            bad_q["receipts"][0]["experiment_id"] = "other-exp"
            bad_q_hash = s.protocol(bad_q)
            package["experiment_plan_quorum_certificate_hash"] = bad_q_hash
            bad_c = copy.deepcopy(c)
            bad_c["prerequisite_certificate_hash"] = bad_q_hash
            package["ledger_event_hashes"] = [s.protocol(bad_c)]
            result = verify_plan_preregistration(package, s.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
            self.assertTrue(any("PLAN_RECEIPT_EXPERIMENT_REBINDING" in x for x in result["failure_codes"]))


if __name__ == "__main__":
    unittest.main()
