import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import load_json_strict  # noqa: E402


NEW_V05_GATES = {
    "SIGNATURE_PREIMAGE_POLICY_VALID",
    "SIGNATURE_PREIMAGE_REPLAY",
    "CANONICAL_ED25519_ENCODING",
    "ED25519_SIGNATURE_CRYPTO",
}


class SignaturePreimageConformanceTests(unittest.TestCase):
    def load(self, rel):
        return load_json_strict(ROOT / rel)

    def test_release_gate_is_strict_extension_49_to_53(self):
        prev = self.load("conformance/AIFC-RELEASE-GATE-v1.0.4-draft.json")
        curr = self.load("conformance/AIFC-RELEASE-GATE-v1.0.5-draft.json")
        p = [x["id"] for x in prev["required_checks"] if x.get("required") is True]
        c = [x["id"] for x in curr["required_checks"] if x.get("required") is True]
        self.assertEqual(len(p), 49)
        self.assertEqual(len(c), 53)
        self.assertEqual(set(c), set(p) | NEW_V05_GATES)
        self.assertEqual(curr["status"], "DRAFT_NOT_SATISFIED")
        self.assertEqual(
            curr["supersedes_for_draft_evaluation"],
            "conformance/AIFC-RELEASE-GATE-v1.0.4-draft.json",
        )

    def test_signature_policy_is_normative_not_claimant_extensible(self):
        schema = self.load("schemas/signature-preimage-policy.schema.json")
        props = schema["properties"]
        self.assertEqual(props["policy_id"]["const"], "AIFC-ED25519-SIGNATURE-PREIMAGE-POLICY-V1")
        self.assertEqual(props["signature_profile_id"]["const"], "AIFC-ED25519-DIRECT-TYPED-V1")
        self.assertEqual(props["signature_algorithm"]["const"], "Ed25519")
        self.assertEqual(props["domain_separator"]["const"], "AIFC:SIGNATURE_PREIMAGE:v1")
        self.assertEqual(props["framing"]["const"], "TAG_U8_LENGTH_U64BE_V1")
        self.assertEqual(props["prehash_mode"]["const"], "NONE_DIRECT_ED25519")

    def test_experiment_plan_has_signature_policy_binding_property(self):
        plan = self.load("schemas/experiment-plan.schema.json")
        self.assertIn("signature_preimage_policy_hash", plan["properties"])
        self.assertEqual(plan["properties"]["signature_preimage_policy_hash"]["pattern"], "^[0-9a-f]{64}$")
        self.assertIn("historical", plan["description"].lower())
        self.assertIn("v0.5", plan["description"])

    def test_strongest_receipt_profile_requires_exact_signature_context(self):
        for rel in (
            "schemas/witness-receipt.schema.json",
            "schemas/experiment-plan-receipt.schema.json",
            "schemas/registry-transition-receipt.schema.json",
        ):
            schema = self.load(rel)
            self.assertEqual(
                schema["properties"]["signature_profile_id"]["const"],
                "AIFC-ED25519-DIRECT-TYPED-V1",
            )
            strongest = schema["allOf"][0]["then"]
            self.assertIn("content_schema", strongest["required"])
            self.assertIn("registry_sequence", strongest["required"])
            self.assertIn("wall_clock_timestamp", strongest["required"])
            self.assertEqual(strongest["properties"]["signature"]["pattern"], "^[0-9a-f]{128}$")

    def test_registry_public_key_encoding_is_single_canonical_form(self):
        registry = self.load("schemas/witness-registry.schema.json")
        key_props = registry["properties"]["witnesses"]["items"]["properties"]["keys"]["items"]["properties"]
        self.assertEqual(key_props["algorithm"]["const"], "Ed25519")
        self.assertEqual(key_props["public_key_encoding"]["const"], "hex")
        self.assertEqual(key_props["public_key"]["pattern"], "^[0-9a-f]{64}$")

    def test_signature_policy_has_protocol_content_identity_domain(self):
        text = (VERIFIER_DIR / "canonical.py").read_text(encoding="utf-8")
        self.assertIn('"AIFC/signature-preimage-policy/v1": "AIFC:SIGNATURE_PREIMAGE_POLICY:v1"', text)

    def test_preimage_compiler_and_admission_paths_are_present(self):
        compiler = (VERIFIER_DIR / "signature_preimage.py").read_text(encoding="utf-8")
        admission = (VERIFIER_DIR / "signature_policy_admission.py").read_text(encoding="utf-8")
        full = (VERIFIER_DIR / "full_admission_v05.py").read_text(encoding="utf-8")
        for token in (
            "CROSS_EXPERIMENT_SIGNATURE_REPLAY",
            "CROSS_RECEIPT_TYPE_REPLAY",
            "SIGNATURE_FIELD_TAG_TABLE_MISMATCH",
            "AIFC:SIGNATURE_PREIMAGE:v1",
        ):
            self.assertIn(token, compiler)
        for token in (
            "CROSS_TRIAL_SIGNATURE_REPLAY",
            "LOGICAL_POSITION_REBINDING",
            "REGISTRY_SEQUENCE_REBINDING",
            "TRANSITION_ROLE_REBINDING",
        ):
            self.assertIn(token, admission)
        self.assertIn('gates["ED25519_SIGNATURE_CRYPTO"] = "BLOCKED"', full)

    def test_normative_profile_document_exists(self):
        doc = ROOT / "spec" / "SIGNATURE_PREIMAGE_PROFILE-v1.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("signed timestamp != freshness proof", text)
        self.assertIn("CROSS_RECEIPT_TYPE_REPLAY", text)
        self.assertIn("REVOKED_KEY_REPLAY", text)


if __name__ == "__main__":
    unittest.main()
