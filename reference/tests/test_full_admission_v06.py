import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from ed25519_admission import Ed25519AdmissionError  # noqa: E402
from full_admission_v06 import verify_replay_manifest  # noqa: E402


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


def preimage_summary():
    return SimpleNamespace(receipt_count=12, preimage_sha256s=("aa" * 32,), materials=(object(),) * 12)


def crypto_summary():
    return SimpleNamespace(
        receipt_count=12,
        verified_count=12,
        backend_version="OpenSSL 3.x test backend",
        backend_executable_sha256="bb" * 32,
    )


class FullAdmissionV06Tests(unittest.TestCase):
    def test_crypto_pass_sets_registry_local_gates_and_backend_identity(self):
        with patch("full_admission_v06.replay_signature_preimages", return_value=preimage_summary()), \
             patch("full_admission_v06.replay_ed25519_signatures", return_value=crypto_summary()), \
             patch("full_admission_v06.verify_v03", return_value=downstream("NOT_ADMITTED")):
            result = verify_replay_manifest(MANIFEST, object())
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["gate_results"]["SIGNATURE_PREIMAGE_REPLAY"], "PASS")
        self.assertEqual(result["gate_results"]["REGISTRY_LOCAL_KEY_ELIGIBILITY"], "PASS")
        self.assertEqual(result["gate_results"]["ED25519_SIGNATURE_CRYPTO"], "PASS")
        self.assertEqual(result["gate_results"]["HISTORICAL_KEY_LIFECYCLE"], "BLOCKED")
        self.assertEqual(result["crypto_backend"]["backend_id"], "OPENSSL_PKEYUTL_ED25519_V1")
        self.assertEqual(result["verifier_version"], "0.6.0-ed25519-crypto")

    def test_crypto_failure_invalidates_before_downstream_replay(self):
        with patch("full_admission_v06.replay_signature_preimages", return_value=preimage_summary()), \
             patch(
                 "full_admission_v06.replay_ed25519_signatures",
                 side_effect=Ed25519AdmissionError("ED25519_SIGNATURE_INVALID:w0:k0:AIFC/witness-receipt/v1"),
             ), patch("full_admission_v06.verify_v03") as downstream_mock:
            result = verify_replay_manifest(MANIFEST, object())
        downstream_mock.assert_not_called()
        self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
        self.assertEqual(result["gate_results"]["SIGNATURE_PREIMAGE_REPLAY"], "PASS")
        self.assertEqual(result["gate_results"]["ED25519_SIGNATURE_CRYPTO"], "FAIL")
        self.assertTrue(any("ED25519_SIGNATURE_INVALID" in x for x in result["failure_codes"]))

    def test_historical_key_lifecycle_blocks_forward_null_incompatibility_claim(self):
        with patch("full_admission_v06.replay_signature_preimages", return_value=preimage_summary()), \
             patch("full_admission_v06.replay_ed25519_signatures", return_value=crypto_summary()), \
             patch("full_admission_v06.verify_v03", return_value=downstream("FORWARD_NULL_INCOMPATIBILITY_CANDIDATE")):
            result = verify_replay_manifest(MANIFEST, object())
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["gate_results"]["ED25519_SIGNATURE_CRYPTO"], "PASS")
        self.assertEqual(result["gate_results"]["HISTORICAL_KEY_LIFECYCLE"], "BLOCKED")
        self.assertIn("HISTORICAL_KEY_LIFECYCLE:BLOCKED", result["failure_codes"])

    def test_historical_key_lifecycle_blocks_forward_null_miss_admission_too(self):
        with patch("full_admission_v06.replay_signature_preimages", return_value=preimage_summary()), \
             patch("full_admission_v06.replay_ed25519_signatures", return_value=crypto_summary()), \
             patch("full_admission_v06.verify_v03", return_value=downstream("FORWARD_NULL_CONSISTENT_MISS")):
            result = verify_replay_manifest(MANIFEST, object())
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["gate_results"]["HISTORICAL_KEY_LIFECYCLE"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
