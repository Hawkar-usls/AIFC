import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import load_json_strict  # noqa: E402


NEW_V06_GATES = {
    "REGISTRY_LOCAL_KEY_ELIGIBILITY",
    "HISTORICAL_KEY_LIFECYCLE",
    "EXTERNAL_FRESHNESS_REPLAY",
}


class Ed25519ConformanceTests(unittest.TestCase):
    def load(self, rel):
        return load_json_strict(ROOT / rel)

    def test_release_gate_is_strict_extension_53_to_56(self):
        prev = self.load("conformance/AIFC-RELEASE-GATE-v1.0.5-draft.json")
        curr = self.load("conformance/AIFC-RELEASE-GATE-v1.0.6-draft.json")
        p = [x["id"] for x in prev["required_checks"] if x.get("required") is True]
        c = [x["id"] for x in curr["required_checks"] if x.get("required") is True]
        self.assertEqual(len(p), 53)
        self.assertEqual(len(c), 56)
        self.assertEqual(set(c), set(p) | NEW_V06_GATES)
        self.assertEqual(curr["status"], "DRAFT_NOT_SATISFIED")
        self.assertEqual(
            curr["supersedes_for_draft_evaluation"],
            "conformance/AIFC-RELEASE-GATE-v1.0.5-draft.json",
        )
        self.assertIn("ED25519_SIGNATURE_CRYPTO", set(c))

    def test_crypto_backend_identity_is_machine_readable_in_verifier_result(self):
        schema = self.load("schemas/verifier-result.schema.json")
        crypto = schema["properties"]["crypto_backend"]
        props = crypto["properties"]
        self.assertEqual(props["backend_id"]["const"], "OPENSSL_PKEYUTL_ED25519_V1")
        self.assertEqual(props["executable_sha256"]["pattern"], "^[0-9a-f]{64}$")

    def test_ed25519_backend_is_narrow_and_fail_closed(self):
        text = (VERIFIER_DIR / "ed25519_crypto.py").read_text(encoding="utf-8")
        self.assertIn("pkeyutl", text)
        self.assertIn("-verify", text)
        self.assertIn("-rawin", text)
        self.assertIn("ED25519_SPKI_PREFIX", text)
        self.assertIn("ED25519_SIGNATURE_LENGTH_INVALID", text)

    def test_registry_local_crypto_admission_has_expected_attack_paths(self):
        text = (VERIFIER_DIR / "ed25519_admission.py").read_text(encoding="utf-8")
        for token in (
            "REGISTRY_SEQUENCE_REBINDING",
            "WITNESS_ID_NOT_UNIQUE_IN_SIGNING_REGISTRY",
            "KEY_ID_NOT_UNIQUE_FOR_WITNESS",
            "KEY_NOT_ACTIVE_AT_SIGNING_REGISTRY",
            "KEY_NOT_YET_VALID_AT_REGISTRY_SEQUENCE",
            "KEY_EXPIRED_AT_REGISTRY_SEQUENCE",
            "ED25519_SIGNATURE_INVALID",
        ):
            self.assertIn(token, text)

    def test_v06_claim_ceiling_keeps_historical_lifecycle_blocked(self):
        text = (VERIFIER_DIR / "full_admission_v06.py").read_text(encoding="utf-8")
        self.assertIn('gates["ED25519_SIGNATURE_CRYPTO"] = "PASS"', text)
        self.assertIn('gates["HISTORICAL_KEY_LIFECYCLE"] = "BLOCKED"', text)
        self.assertIn('result["terminal_grade"] = "NOT_ADMITTED"', text)
        self.assertIn('"OPENSSL_PKEYUTL_ED25519_V1"', text)

    def test_normative_crypto_boundary_document_exists(self):
        doc = ROOT / "spec" / "ED25519_CRYPTO_REPLAY-v1.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("RFC 8032", text)
        self.assertIn("valid signature != fresh history", text)
        self.assertIn("HISTORICAL_KEY_LIFECYCLE = BLOCKED", text)
        self.assertIn("2c2ad0fd73ebac49a048038941fc4cae0b616cb8ef8a7b174acc63c7c63b1297", text)

    def test_v06_cli_exists_and_preserves_exit_taxonomy(self):
        cli = ROOT / "reference" / "verifier" / "aifc_verify_v06.py"
        self.assertTrue(cli.is_file())
        text = cli.read_text(encoding="utf-8")
        self.assertIn("CLI-EXIT-TAXONOMY-v1.json", text)
        self.assertIn("full_admission_v06", text)
        self.assertIn("HISTORICAL_KEY_LIFECYCLE", text)


if __name__ == "__main__":
    unittest.main()
