import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from assurance_monotonicity import (  # noqa: E402
    compare_release_gate_sets,
    compare_schema_identity,
    compare_verifier_results,
    required_gate_ids,
)
from canonical import load_json_strict  # noqa: E402
from protocol_semantics_v03 import ProtocolSemanticsError, replay_terminal_semantics  # noqa: E402
from test_protocol_semantics_v03 import Store as SemanticsStore, event as semantics_event, H  # noqa: E402


NEW_CONVERGENCE_GATES = {
    "VERIFIER_ADMISSION_MONOTONICITY",
    "RELEASE_GATE_MONOTONICITY",
    "SCHEMA_IDENTIFIER_IMMUTABILITY",
    "NORMATIVE_PROFILE_LINEAGE_VALID",
    "SIGNATURE_PREIMAGE_RESOLVER_DERIVED_REPLAY",
}


def result(grade, gates=None):
    return {
        "terminal_grade": grade,
        "gate_results": gates or {},
    }


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()


class AssuranceConvergenceTests(unittest.TestCase):
    def test_successor_outcome_cannot_be_stronger(self):
        comparison = compare_verifier_results(
            result("INVALIDATED_EVIDENCE", {"TERMINAL_SUBTYPE_SEMANTICS": "FAIL"}),
            result("NOT_ADMITTED", {"TERMINAL_SUBTYPE_SEMANTICS": "FAIL"}),
            {"TERMINAL_SUBTYPE_SEMANTICS"},
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertTrue(any("SUCCESSOR_OUTCOME_STRONGER_THAN_PREDECESSOR" in x for x in comparison.failure_codes))

    def test_inherited_fail_gate_cannot_disappear_even_if_terminal_rank_does_not_increase(self):
        comparison = compare_verifier_results(
            result("INVALIDATED_EVIDENCE", {"TRIAL_CREATION_POLICY_REPLAY": "FAIL"}),
            result("INVALIDATED_EVIDENCE", {"TRIAL_CREATION_POLICY_REPLAY": "PASS"}),
            {"TRIAL_CREATION_POLICY_REPLAY"},
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertTrue(any("INHERITED_HARDENING_LAYER_OMISSION" in x for x in comparison.failure_codes))

    def test_blocked_gate_may_be_implemented_by_successor(self):
        comparison = compare_verifier_results(
            result("NOT_ADMITTED", {"ED25519_SIGNATURE_CRYPTO": "BLOCKED"}),
            result("NOT_ADMITTED", {"ED25519_SIGNATURE_CRYPTO": "PASS"}),
            {"ED25519_SIGNATURE_CRYPTO"},
        )
        self.assertEqual(comparison.status, "PASS")

    def test_release_gate_is_exact_56_to_61_extension_by_id_set(self):
        previous = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.6-draft.json")
        current = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.7-draft.json")
        pred_ids = required_gate_ids(previous)
        current_ids = required_gate_ids(current)
        self.assertEqual(len(pred_ids), 56)
        self.assertEqual(len(current_ids), 61)
        self.assertEqual(current_ids - pred_ids, NEW_CONVERGENCE_GATES)
        self.assertEqual(pred_ids - current_ids, set())
        self.assertEqual(compare_release_gate_sets(previous, current).status, "PASS")
        self.assertEqual(current["status"], "DRAFT_NOT_SATISFIED")

    def test_release_gate_regression_is_detected_semantically_not_by_count(self):
        previous = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.6-draft.json")
        regressed = copy.deepcopy(previous)
        regressed["required_checks"] = [
            row for row in regressed["required_checks"] if row["id"] != "ED25519_SIGNATURE_CRYPTO"
        ]
        # Add an unrelated new gate so total count does not reveal the removal.
        regressed["required_checks"].append({"id": "UNRELATED_NEW_GATE", "required": True})
        comparison = compare_release_gate_sets(previous, regressed)
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn("RELEASE_GATE_REGRESSION:ED25519_SIGNATURE_CRYPTO", comparison.failure_codes)

    def test_gate_removal_requires_explicit_successor_mapping(self):
        previous = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.6-draft.json")
        successor = copy.deepcopy(previous)
        successor["required_checks"] = [
            row for row in successor["required_checks"] if row["id"] != "ED25519_SIGNATURE_CRYPTO"
        ]
        successor["required_checks"].append({"id": "ED25519_CRYPTO_STRICTER_V2", "required": True})
        transition = {
            "schema": "AIFC/gate-lineage-transition/v1",
            "removed_gate_id": "ED25519_SIGNATURE_CRYPTO",
            "successor_gate_ids": ["ED25519_CRYPTO_STRICTER_V2"],
            "previous_gate_definition_hash": "11" * 32,
            "successor_definition_hashes": ["22" * 32],
            "equivalence_or_strengthening_evidence_hash": "33" * 32,
            "migration_reason": "test-only strengthening transition",
            "approved_protocol_version": "test-v2",
        }
        self.assertEqual(compare_release_gate_sets(previous, successor, [transition]).status, "PASS")

    def test_issued_schema_registry_matches_exact_current_source_blobs(self):
        registry = load_json_strict(ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v1.json")
        self.assertEqual(registry["validation_semantics_id"], "AIFC_JSON_SCHEMA_D2020_12_STRICT_SOURCE_RUNTIME_V03")
        seen = set()
        for record in registry["records"]:
            with self.subTest(schema_id=record["schema_id"]):
                self.assertNotIn(record["schema_id"], seen)
                seen.add(record["schema_id"])
                self.assertEqual(record["source_content_algorithm"], "GIT_BLOB_SHA1")
                path = ROOT / record["source_path"]
                self.assertTrue(path.is_file())
                actual = git_blob_sha1(path)
                comparison = compare_schema_identity(
                    record,
                    current_schema_id=record["schema_id"],
                    current_dialect="https://json-schema.org/draft/2020-12/schema",
                    current_source_content_id=actual,
                    current_admission_semantics_version=registry["validation_semantics_id"],
                )
                self.assertEqual(comparison.status, "PASS", msg=comparison.failure_codes)

    def test_same_schema_id_source_mutation_is_rejected(self):
        registry = load_json_strict(ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v1.json")
        record = registry["records"][0]
        comparison = compare_schema_identity(
            record,
            current_schema_id=record["schema_id"],
            current_dialect=record["dialect"],
            current_source_content_id="0" * 40,
            current_admission_semantics_version=record["admission_semantics_version"],
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn("SAME_SCHEMA_ID_LANGUAGE_MUTATION:SOURCE_CHANGED", comparison.failure_codes)

    def test_same_schema_id_validator_semantics_mutation_is_rejected(self):
        registry = load_json_strict(ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v1.json")
        record = registry["records"][0]
        comparison = compare_schema_identity(
            record,
            current_schema_id=record["schema_id"],
            current_dialect=record["dialect"],
            current_source_content_id=record["source_content_id"],
            current_admission_semantics_version="DIFFERENT_VALIDATOR_SEMANTICS",
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn("SAME_SCHEMA_ID_LANGUAGE_MUTATION:VALIDATOR_SEMANTICS_CHANGED", comparison.failure_codes)

    def test_current_v06_authoritative_path_still_composes_v03(self):
        text = (VERIFIER_DIR / "full_admission_v06.py").read_text(encoding="utf-8")
        self.assertIn("from full_admission_v03 import verify_replay_manifest as verify_v03", text)
        self.assertIn("result = verify_v03(manifest, resolver)", text)
        self.assertNotIn("from full_admission_v02 import", text)

    def test_real_v03_impossible_terminal_fixture_remains_a_frozen_rejection_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            store = SemanticsStore(Path(td))
            bad = store.protocol(
                semantics_event(0, 1, "CREATED", "TERMINAL", "COMPLETED_HIT", H("d"), None)
            )
            with self.assertRaises(ProtocolSemanticsError) as ctx:
                replay_terminal_semantics({"ledger_event_hashes": [bad]}, store.resolver())
            self.assertIn("IMPOSSIBLE_TERMINAL_SUBTYPE", str(ctx.exception))

    def test_normative_profile_v1_identity_is_preserved_as_historical_tested_scope(self):
        lineage = load_json_strict(ROOT / "conformance" / "AIFC-NORMATIVE-PROFILE-LINEAGE-v1.json")
        records = lineage["records"]
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["profile_id"], "AIFC-ED25519-DIRECT-TYPED-V1")
        self.assertEqual(record["framing_id"], "TAG_U8_LENGTH_U64BE_V1")
        self.assertEqual(record["status"], "HISTORICALLY_ISSUED_TESTED_SCOPE")
        self.assertIsNone(record["successor_profile_id"])


if __name__ == "__main__":
    unittest.main()
