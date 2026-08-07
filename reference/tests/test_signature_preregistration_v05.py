import copy
import sys
import tempfile
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from preregistration_v02 import verify_plan_preregistration  # noqa: E402
from preregistration_v05 import verify_signature_preimage_preregistration  # noqa: E402
from signature_preimage_v05 import normative_policy  # noqa: E402
from test_preregistration_v02 import StoreV02, created, plan, plan_quorum, registry  # noqa: E402


def build(root: Path, *, bind_signature_policy: bool = True, policy_experiment_id: str = "exp-1"):
    s = StoreV02(root)
    exp = "exp-1"
    reg = registry(exp)
    reg_hash = s.protocol(reg)
    p = plan(exp, reg_hash)
    policy = None
    policy_hash = None
    if bind_signature_policy:
        policy = normative_policy(policy_experiment_id)
        policy_hash = s.protocol(policy)
        p["signature_preimage_policy_hash"] = policy_hash
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
    return s, package, p, policy, policy_hash


class SignaturePreregistrationV05Tests(unittest.TestCase):
    def test_normative_policy_is_certified_inside_plan_before_created(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, *_ = build(Path(td))
            self.assertIsNone(verify_plan_preregistration(package, s.resolver()))
            self.assertIsNone(verify_signature_preimage_preregistration(package, s.resolver()))

    def test_legacy_plan_remains_v02_readable_but_cannot_pass_v05(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, *_ = build(Path(td), bind_signature_policy=False)
            self.assertIsNone(verify_plan_preregistration(package, s.resolver()))
            result = verify_signature_preimage_preregistration(package, s.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
            self.assertTrue(any("SIGNATURE_PREIMAGE_POLICY_REQUIRED_FOR_V05" in x for x in result["failure_codes"]))

    def test_signature_policy_experiment_rebinding_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, *_ = build(Path(td), policy_experiment_id="other-exp")
            self.assertIsNone(verify_plan_preregistration(package, s.resolver()))
            result = verify_signature_preimage_preregistration(package, s.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
            self.assertTrue(any("SIGNATURE_PREIMAGE_POLICY_EXPERIMENT_REBINDING" in x for x in result["failure_codes"]))

    def test_dangling_signature_policy_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            s, package, p, policy, policy_hash = build(Path(td))
            bad_plan = copy.deepcopy(p)
            bad_plan["signature_preimage_policy_hash"] = "f" * 64
            bad_plan_hash = s.protocol(bad_plan)
            reg_hash = p["initial_witness_registry_hash"]
            bad_q = plan_quorum("exp-1", bad_plan_hash, reg_hash)
            bad_q_hash = s.protocol(bad_q)
            bad_created = created("exp-1", bad_plan_hash, bad_q_hash)
            package["experiment_plan_hash"] = bad_plan_hash
            package["experiment_plan_quorum_certificate_hash"] = bad_q_hash
            package["ledger_event_hashes"] = [s.protocol(bad_created)]
            result = verify_signature_preimage_preregistration(package, s.resolver())
            self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
            self.assertTrue(any("SIGNATURE_PREIMAGE_POLICY_EVIDENCE_FAILURE" in x for x in result["failure_codes"]))


if __name__ == "__main__":
    unittest.main()
