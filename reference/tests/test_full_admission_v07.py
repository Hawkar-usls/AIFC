import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from key_lifecycle import KeyLifecycleError  # noqa: E402
from full_admission_v07 import verify_replay_manifest  # noqa: E402


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
    return SimpleNamespace(receipt_count=12, materials=(object(),) * 12)


def crypto_summary():
    return SimpleNamespace(
        receipt_count=12,
        verified_count=12,
        backend_version="OpenSSL test backend",
        backend_executable_sha256="aa" * 32,
    )


def lifecycle_summary(*, events=0, boundaries=0, invalidated=0, complete=False):
    return SimpleNamespace(
        lifecycle_event_count=events,
        boundary_count=boundaries,
        invalidated_signature_count=invalidated,
        quorum_results=(SimpleNamespace(), SimpleNamespace()),
        cutoff_registry_sequence=4,
        final_head_hash="bb" * 32,
        external_completeness_proven=complete,
    )


class FullAdmissionV07Tests(unittest.TestCase):
    def test_local_lifecycle_replay_passes_without_claiming_historical_completeness(self):
        with patch("full_admission_v07.replay_signature_preimages", return_value=preimage_summary()), \
             patch("full_admission_v07.replay_ed25519_signatures", return_value=crypto_summary()), \
             patch("full_admission_v07.replay_historical_key_lifecycle", return_value=lifecycle_summary()), \
             patch("full_admission_v07.verify_v03", return_value=downstream("NOT_ADMITTED")):
            result = verify_replay_manifest(MANIFEST, object())
        gates = result["gate_results"]
        self.assertEqual(gates["ED25519_SIGNATURE_CRYPTO"], "PASS")
        self.assertEqual(gates["KEY_LIFECYCLE_POLICY_VALID"], "PASS")
        self.assertEqual(gates["KEY_LIFECYCLE_LEDGER_REPLAY"], "PASS")
        self.assertEqual(gates["RETROACTIVE_KEY_QUORUM_REEVALUATION"], "PASS")
        self.assertEqual(gates["HISTORICAL_KEY_LIFECYCLE"], "BLOCKED")
        self.assertEqual(gates["EXTERNAL_FRESHNESS_REPLAY"], "BLOCKED")
        self.assertFalse(result["key_lifecycle_summary"]["external_completeness_proven"])
        self.assertEqual(result["verifier_version"], "0.7.0-key-lifecycle")

    def test_known_historical_quorum_collapse_invalidates_evidence_but_passes_replay_mechanism(self):
        with patch("full_admission_v07.replay_signature_preimages", return_value=preimage_summary()), \
             patch("full_admission_v07.replay_ed25519_signatures", return_value=crypto_summary()), \
             patch(
                 "full_admission_v07.replay_historical_key_lifecycle",
                 side_effect=KeyLifecycleError("HISTORICAL_QUORUM_COLLAPSE:certificate-A:witnesses=2:domains=2:q=3"),
             ), patch("full_admission_v07.verify_v03") as downstream_mock:
            result = verify_replay_manifest(MANIFEST, object())
        downstream_mock.assert_not_called()
        self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
        self.assertEqual(result["gate_results"]["ED25519_SIGNATURE_CRYPTO"], "PASS")
        self.assertEqual(result["gate_results"]["KEY_LIFECYCLE_POLICY_VALID"], "PASS")
        self.assertEqual(result["gate_results"]["KEY_LIFECYCLE_LEDGER_REPLAY"], "PASS")
        self.assertEqual(result["gate_results"]["RETROACTIVE_KEY_QUORUM_REEVALUATION"], "PASS")
        self.assertEqual(result["gate_results"]["HISTORICAL_KEY_LIFECYCLE"], "FAIL")
        self.assertTrue(any("HISTORICAL_QUORUM_COLLAPSE" in x for x in result["failure_codes"]))

    def test_empty_or_surviving_local_ledger_cannot_admit_forward_null_incompatibility(self):
        with patch("full_admission_v07.replay_signature_preimages", return_value=preimage_summary()), \
             patch("full_admission_v07.replay_ed25519_signatures", return_value=crypto_summary()), \
             patch("full_admission_v07.replay_historical_key_lifecycle", return_value=lifecycle_summary()), \
             patch("full_admission_v07.verify_v03", return_value=downstream("FORWARD_NULL_INCOMPATIBILITY_CANDIDATE")):
            result = verify_replay_manifest(MANIFEST, object())
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["gate_results"]["HISTORICAL_KEY_LIFECYCLE"], "BLOCKED")
        self.assertIn("HISTORICAL_KEY_LIFECYCLE:BLOCKED_EXTERNAL_COMPLETENESS", result["failure_codes"])

    def test_local_lifecycle_also_cannot_admit_forward_null_miss(self):
        with patch("full_admission_v07.replay_signature_preimages", return_value=preimage_summary()), \
             patch("full_admission_v07.replay_ed25519_signatures", return_value=crypto_summary()), \
             patch("full_admission_v07.replay_historical_key_lifecycle", return_value=lifecycle_summary(events=2, boundaries=1, invalidated=1)), \
             patch("full_admission_v07.verify_v03", return_value=downstream("FORWARD_NULL_CONSISTENT_MISS")):
            result = verify_replay_manifest(MANIFEST, object())
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["key_lifecycle_summary"]["invalidated_signature_count"], 1)
        self.assertEqual(result["gate_results"]["EXTERNAL_FRESHNESS_REPLAY"], "BLOCKED")

    def test_unversioned_external_completeness_true_fails_closed(self):
        with patch("full_admission_v07.replay_signature_preimages", return_value=preimage_summary()), \
             patch("full_admission_v07.replay_ed25519_signatures", return_value=crypto_summary()), \
             patch("full_admission_v07.replay_historical_key_lifecycle", return_value=lifecycle_summary(complete=True)), \
             patch("full_admission_v07.verify_v03", return_value=downstream("NOT_ADMITTED")):
            result = verify_replay_manifest(MANIFEST, object())
        self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
        self.assertEqual(result["gate_results"]["HISTORICAL_KEY_LIFECYCLE"], "FAIL")
        self.assertIn("UNVERSIONED_EXTERNAL_KEY_LIFECYCLE_COMPLETENESS", result["failure_codes"])


if __name__ == "__main__":
    unittest.main()
