import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import load_json_strict  # noqa: E402


class SignaturePreimageGateV05Tests(unittest.TestCase):
    def test_v105_is_exact_two_class_extension_of_v104(self):
        previous = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.4-draft.json")
        current = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.5-draft.json")
        previous_ids = [row["id"] for row in previous["required_checks"] if row.get("required") is True]
        current_ids = [row["id"] for row in current["required_checks"] if row.get("required") is True]
        self.assertEqual(len(previous_ids), 49)
        self.assertEqual(len(current_ids), 51)
        self.assertEqual(len(previous_ids), len(set(previous_ids)))
        self.assertEqual(len(current_ids), len(set(current_ids)))
        self.assertEqual(set(previous_ids) - set(current_ids), set())
        self.assertEqual(
            set(current_ids) - set(previous_ids),
            {"SIGNATURE_PREIMAGE_POLICY_VALID", "SIGNATURE_PREIMAGE_PROFILE_REPLAY"},
        )
        self.assertEqual(current["status"], "DRAFT_NOT_SATISFIED")
        self.assertEqual(
            current["supersedes_for_draft_evaluation"],
            "conformance/AIFC-RELEASE-GATE-v1.0.4-draft.json",
        )

    def test_preimage_spec_preserves_crypto_and_freshness_ceiling(self):
        spec = (ROOT / "spec" / "SIGNATURE-PREIMAGE-PROFILE-v1.md").read_text(encoding="utf-8")
        self.assertIn("AIFC:SIGNATURE_PREIMAGE:v1", spec)
        self.assertIn("signed timestamp != freshness proof", spec)
        self.assertIn("ED25519_SIGNATURE_CRYPTO", spec)
        self.assertIn("HISTORICAL_KEY_LIFECYCLE_CRYPTO_REPLAY", spec)
        self.assertIn("does not mean the signature is valid", spec.lower())


if __name__ == "__main__":
    unittest.main()
