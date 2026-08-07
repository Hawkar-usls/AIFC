import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from full_admission_v05 import verify_replay_manifest  # noqa: E402
from signature_policy_admission import SignaturePolicyAdmissionError  # noqa: E402


MANIFEST = {
    "experiment_id": "exp-1",
    "subject_trial_index": 1,
    "evidence_bundle_hash": "11" * 32,
}


def downstream(grade="NOT_ADMITTED"):
    return {
        "schema": "AIFC/verifier-result/v1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.3.0-self-audit",
        "evidence_bundle_hash": "11" * 32,
        "gate_results": {"DOWNSTREAM_CORE": "PASS"},
        "exact_match": False,
        "terminal_grade": grade,
        "failure_codes": [],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


class FullAdmissionV05Tests(unittest.TestCase):
    def test_successful_preimage_replay_keeps_crypto_explicitly_blocked(self):
        summary = SimpleNamespace(receipt_count=12, preimage_sha256s=("aa" * 32,))
        with patch("full_admission_v05.replay_signature_preimages", return_value=summary), \
             patch("full_admission_v05.verify_v03", return_value=downstream("NOT_ADMITTED")):
            result = verify_replay_manifest(MANIFEST, object())
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["gate_results"]["SIGNATURE_PREIMAGE_POLICY_VALID"], "PASS")
        self.assertEqual(result["gate_results"]["SIGNATURE_PREIMAGE_REPLAY"], "PASS")
        self.assertEqual(result["gate_results"]["CANONICAL_ED25519_ENCODING"], "PASS")
        self.assertEqual(result["gate_results"]["ED25519_SIGNATURE_CRYPTO"], "BLOCKED")
        self.assertEqual(result["verifier_version"], "0.5.0-signature-preimage")

    def test_blocked_crypto_caps_forward_null_outcome_to_not_admitted(self):
        summary = SimpleNamespace(receipt_count=12, preimage_sha256s=("aa" * 32,))
        with patch("full_admission_v05.replay_signature_preimages", return_value=summary), \
             patch("full_admission_v05.verify_v03", return_value=downstream("FORWARD_NULL_INCOMPATIBILITY_CANDIDATE")):
            result = verify_replay_manifest(MANIFEST, object())
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["gate_results"]["ED25519_SIGNATURE_CRYPTO"], "BLOCKED")
        self.assertIn("ED25519_SIGNATURE_CRYPTO:BLOCKED", result["failure_codes"])

    def test_signature_preimage_failure_invalidates_before_downstream_replay(self):
        with patch(
            "full_admission_v05.replay_signature_preimages",
            side_effect=SignaturePolicyAdmissionError("REGISTRY_SEQUENCE_REBINDING"),
        ), patch("full_admission_v05.verify_v03") as downstream_mock:
            result = verify_replay_manifest(MANIFEST, object())
        downstream_mock.assert_not_called()
        self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
        self.assertEqual(result["gate_results"]["SIGNATURE_PREIMAGE_REPLAY"], "FAIL")
        self.assertEqual(result["gate_results"]["ED25519_SIGNATURE_CRYPTO"], "BLOCKED")
        self.assertTrue(any("REGISTRY_SEQUENCE_REBINDING" in x for x in result["failure_codes"]))


if __name__ == "__main__":
    unittest.main()
