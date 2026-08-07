import sys
import unittest
from pathlib import Path
from unittest.mock import patch

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

import full_admission_v05  # noqa: E402


class FullAdmissionV05CompositionTests(unittest.TestCase):
    def test_signature_preregistration_failure_blocks_downstream(self):
        blocked = {
            "schema": "AIFC/verifier-result/v1",
            "terminal_grade": "INVALIDATED_EVIDENCE",
            "failure_codes": ["SIGNATURE_PREIMAGE_POLICY_REQUIRED_FOR_V05"],
        }
        with patch.object(full_admission_v05, "verify_signature_preimage_preregistration", return_value=blocked) as prereg, \
             patch.object(full_admission_v05, "verify_full_admission_v02") as downstream:
            result = full_admission_v05.verify_full_admission_v05({}, object())
            self.assertIs(result, blocked)
            prereg.assert_called_once()
            downstream.assert_not_called()

    def test_downstream_runs_only_after_signature_preregistration_pass(self):
        downstream_result = {"terminal_grade": "NOT_ADMITTED", "failure_codes": []}
        with patch.object(full_admission_v05, "verify_signature_preimage_preregistration", return_value=None) as prereg, \
             patch.object(full_admission_v05, "verify_full_admission_v02", return_value=downstream_result) as downstream:
            result = full_admission_v05.verify_full_admission_v05({}, object())
            self.assertIs(result, downstream_result)
            prereg.assert_called_once()
            downstream.assert_called_once()


if __name__ == "__main__":
    unittest.main()
