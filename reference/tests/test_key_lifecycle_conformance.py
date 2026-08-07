import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import load_json_strict  # noqa: E402


NEW_V07_GATES = {
    "KEY_LIFECYCLE_POLICY_VALID",
    "KEY_LIFECYCLE_LEDGER_REPLAY",
    "RETROACTIVE_KEY_QUORUM_REEVALUATION",
}


class KeyLifecycleConformanceTests(unittest.TestCase):
    def load(self, rel):
        return load_json_strict(ROOT / rel)

    def test_release_gate_is_strict_extension_56_to_59(self):
        prev = self.load("conformance/AIFC-RELEASE-GATE-v1.0.6-draft.json")
        curr = self.load("conformance/AIFC-RELEASE-GATE-v1.0.7-draft.json")
        p = [x["id"] for x in prev["required_checks"] if x.get("required") is True]
        c = [x["id"] for x in curr["required_checks"] if x.get("required") is True]
        self.assertEqual(len(p), 56)
        self.assertEqual(len(c), 59)
        self.assertEqual(set(c), set(p) | NEW_V07_GATES)
        self.assertEqual(curr["status"], "DRAFT_NOT_SATISFIED")
        self.assertEqual(
            curr["supersedes_for_draft_evaluation"],
            "conformance/AIFC-RELEASE-GATE-v1.0.6-draft.json",
        )
        self.assertIn("HISTORICAL_KEY_LIFECYCLE", set(c))
        self.assertIn("EXTERNAL_FRESHNESS_REPLAY", set(c))

    def test_lifecycle_policy_is_fail_closed_and_requires_external_completeness(self):
        schema = self.load("schemas/key-lifecycle-policy.schema.json")
        props = schema["properties"]
        self.assertEqual(props["policy_id"]["const"], "AIFC-KEY-LIFECYCLE-POLICY-V1")
        self.assertEqual(props["boundary_unit"]["const"], "REGISTRY_SEQUENCE")
        self.assertEqual(
            props["unknown_compromise_boundary_semantics"]["const"],
            "INVALIDATE_FROM_REGISTRY_SEQUENCE_ZERO",
        )
        self.assertIs(props["external_completeness_required"]["const"], True)
        self.assertIs(props["wall_clock_not_sufficient"]["const"], True)

    def test_lifecycle_event_schema_separates_compromise_from_prospective_declaration(self):
        schema = self.load("schemas/key-lifecycle-event.schema.json")
        event_types = set(schema["properties"]["event_type"]["enum"])
        self.assertEqual(
            event_types,
            {"COMPROMISE_DISCOVERED", "REVOCATION_DECLARED", "RETIREMENT_DECLARED"},
        )
        bases = set(schema["properties"]["boundary_basis"]["enum"])
        self.assertIn("UNKNOWN_FROM_GENESIS", bases)
        self.assertIn("PROSPECTIVE_DECLARATION", bases)

    def test_lifecycle_ledger_explicitly_refuses_to_claim_external_completeness(self):
        schema = self.load("schemas/key-lifecycle-ledger.schema.json")
        self.assertEqual(
            schema["properties"]["completeness_status"]["const"],
            "LOCAL_CHAIN_REPLAYED_EXTERNAL_COMPLETENESS_NOT_PROVEN",
        )

    def test_plan_package_and_bundle_have_lifecycle_bindings(self):
        plan = self.load("schemas/experiment-plan.schema.json")
        package = self.load("schemas/replay-package.schema.json")
        bundle = self.load("schemas/evidence-bundle.schema.json")
        self.assertIn("key_lifecycle_policy_hash", plan["properties"])
        self.assertIn("key_lifecycle_ledger_hash", package["properties"])
        self.assertIn("key_lifecycle_ledger_hash", bundle["properties"])
        self.assertIn("compatibility", plan["description"].lower())

    def test_lifecycle_objects_have_protocol_content_identity_domains(self):
        text = (VERIFIER_DIR / "canonical.py").read_text(encoding="utf-8")
        for token in (
            '"AIFC/key-lifecycle-policy/v1": "AIFC:KEY_LIFECYCLE_POLICY:v1"',
            '"AIFC/key-lifecycle-event/v1": "AIFC:KEY_LIFECYCLE_EVENT:v1"',
            '"AIFC/key-lifecycle-ledger/v1": "AIFC:KEY_LIFECYCLE_LEDGER:v1"',
        ):
            self.assertIn(token, text)

    def test_historical_engine_contains_required_fail_closed_paths(self):
        core = (VERIFIER_DIR / "key_lifecycle.py").read_text(encoding="utf-8")
        admission = (VERIFIER_DIR / "key_lifecycle_admission.py").read_text(encoding="utf-8")
        for token in (
            "UNKNOWN_COMPROMISE_BOUNDARY_MUST_START_AT_ZERO",
            "PROSPECTIVE_KEY_EVENT_RETROACTIVE_WITHOUT_COMPROMISE",
            "KEY_LIFECYCLE_CHAIN_BREAK",
            "KEY_LIFECYCLE_FINAL_HEAD_REBINDING",
            "HISTORICAL_QUORUM_COLLAPSE",
        ):
            self.assertIn(token, core)
        for token in (
            "HISTORICAL_QUORUM_Q_VS_REGISTRY_MISMATCH",
            "HISTORICAL_REGISTRY_SEQUENCE_REBINDING",
        ):
            self.assertIn(token, admission)

    def test_verifier_result_summary_cannot_claim_external_completeness(self):
        schema = self.load("schemas/verifier-result.schema.json")
        summary = schema["properties"]["key_lifecycle_summary"]
        self.assertIs(summary["properties"]["external_completeness_proven"]["const"], False)

    def test_v07_claim_ceiling_keeps_freshness_and_historical_completion_blocked(self):
        text = (VERIFIER_DIR / "full_admission_v07.py").read_text(encoding="utf-8")
        self.assertIn('gates["HISTORICAL_KEY_LIFECYCLE"] = "BLOCKED"', text)
        self.assertIn('gates["EXTERNAL_FRESHNESS_REPLAY"] = "BLOCKED"', text)
        self.assertIn('"HISTORICAL_KEY_LIFECYCLE:BLOCKED_EXTERNAL_COMPLETENESS"', text)
        self.assertIn('gates["RETROACTIVE_KEY_QUORUM_REEVALUATION"] = "PASS"', text)

    def test_normative_lifecycle_document_exists(self):
        doc = ROOT / "spec" / "HISTORICAL_KEY_LIFECYCLE-v1.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("HISTORICAL_QUORUM_COLLAPSE", text)
        self.assertIn("empty / surviving local lifecycle ledger", text)
        self.assertIn("EXTERNAL_FRESHNESS_REPLAY = BLOCKED", text)
        self.assertIn("AIFC:KEY_LIFECYCLE_GENESIS:v1", text)

    def test_v07_cli_exists_and_uses_frozen_exit_taxonomy(self):
        cli = ROOT / "reference" / "verifier" / "aifc_verify_v07.py"
        self.assertTrue(cli.is_file())
        text = cli.read_text(encoding="utf-8")
        self.assertIn("CLI-EXIT-TAXONOMY-v1.json", text)
        self.assertIn("full_admission_v07", text)
        self.assertIn("EXTERNAL_FRESHNESS_REPLAY", text)


if __name__ == "__main__":
    unittest.main()
