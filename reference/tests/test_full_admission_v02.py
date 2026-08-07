import sys
import unittest
from pathlib import Path
from unittest.mock import patch

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from full_admission_v02 import verify_replay_manifest  # noqa: E402


class DummyResolver:
    pass


def failure_result():
    return {
        "schema": "AIFC/verifier-result/v1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.2.0-replay",
        "evidence_bundle_hash": "0" * 64,
        "gate_results": {"EXPERIMENT_PLAN_PREREGISTRATION": "FAIL"},
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": ["EXPERIMENT_PLAN_NOT_CERTIFIED_BEFORE_CREATED"],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def downstream_result():
    return {
        "schema": "AIFC/verifier-result/v1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.2.0-replay",
        "evidence_bundle_hash": "1" * 64,
        "gate_results": {"ENTROPY_POLICY_REPLAY": "PASS", "DOWNSTREAM_REPLAY": "PASS"},
        "exact_match": False,
        "terminal_grade": "NOT_ADMITTED",
        "failure_codes": [],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


class FullAdmissionCompositionTests(unittest.TestCase):
    def test_preregistration_failure_blocks_downstream_replay(self):
        manifest = {"schema": "AIFC/replay-package/v0.2"}
        with patch("full_admission_v02.verify_plan_preregistration", return_value=failure_result()), \
             patch("full_admission_v02.verify_after_preregistration") as downstream:
            result = verify_replay_manifest(manifest, DummyResolver())
        downstream.assert_not_called()
        self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")

    def test_downstream_runs_only_after_preregistration_pass(self):
        manifest = {"schema": "AIFC/replay-package/v0.2"}
        with patch("full_admission_v02.verify_plan_preregistration", return_value=None), \
             patch("full_admission_v02.verify_after_preregistration", return_value=downstream_result()) as downstream:
            result = verify_replay_manifest(manifest, DummyResolver())
        downstream.assert_called_once()
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["gate_results"].get("EXPERIMENT_PLAN_PREREGISTRATION"), "PASS")


if __name__ == "__main__":
    unittest.main()
