import copy
import hashlib
import inspect
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from assurance_monotonicity import (  # noqa: E402
    ADMISSION_ALLOWED_SUCCESSORS,
    compare_release_gate_sets,
    compare_schema_identity,
    compare_verifier_results,
    derive_inherited_gate_obligations,
    required_gate_ids,
)
from canonical import load_json_strict  # noqa: E402
from protocol_semantics_v03 import ProtocolSemanticsError, replay_terminal_semantics  # noqa: E402
from test_protocol_semantics_v03 import Store as SemanticsStore, event as semantics_event, H  # noqa: E402


V10_CONVERGENCE_GATES = {
    "VERIFIER_ADMISSION_MONOTONICITY",
    "RELEASE_GATE_MONOTONICITY",
    "SCHEMA_IDENTIFIER_IMMUTABILITY",
    "NORMATIVE_PROFILE_LINEAGE_VALID",
    "SIGNATURE_PREIMAGE_RESOLVER_DERIVED_REPLAY",
}

V11_HARDENING_GATES = {
    "ADMISSION_AUTHORITY_PARTIAL_ORDER_VALID",
    "INHERITED_GATE_SET_DERIVATION",
    "GATE_LINEAGE_EVIDENCE_RESOLUTION",
    "VALIDATOR_SEMANTICS_CONTENT_BINDING",
}


def result(grade, gates=None):
    return {
        "terminal_grade": grade,
        "gate_results": gates or {},
    }


def gate_doc(*gate_ids):
    return {
        "schema": "AIFC/conformance-release-gate/v1",
        "profile": "test",
        "status": "DRAFT_NOT_SATISFIED",
        "required_checks": [{"id": gate_id, "required": True} for gate_id in gate_ids],
    }


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AssuranceConvergenceTests(unittest.TestCase):
    def test_machine_partial_order_table_matches_frozen_conformance_object(self):
        order = load_json_strict(ROOT / "conformance" / "AIFC-ADMISSION-AUTHORITY-ORDER-v1.json")
        self.assertEqual(order["order_id"], "AIFC-ADMISSION-AUTHORITY-PARTIAL-ORDER-V1")
        frozen = {key: frozenset(value) for key, value in order["allowed_successor_outcomes"].items()}
        self.assertEqual(frozen, ADMISSION_ALLOWED_SUCCESSORS)
        self.assertIn(
            ["FORWARD_NULL_CONSISTENT_MISS", "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE"],
            order["incomparable_outcome_pairs"],
        )

    def test_successor_outcome_cannot_be_stronger(self):
        gates = gate_doc("TERMINAL_SUBTYPE_SEMANTICS")
        comparison = compare_verifier_results(
            result("INVALIDATED_EVIDENCE", {"TERMINAL_SUBTYPE_SEMANTICS": "FAIL"}),
            result("NOT_ADMITTED", {"TERMINAL_SUBTYPE_SEMANTICS": "FAIL"}),
            gates,
            gates,
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertTrue(any("SUCCESSOR_OUTCOME_STRONGER_THAN_PREDECESSOR" in x for x in comparison.failure_codes))

    def test_same_rank_authority_escalation_is_rejected(self):
        gates = gate_doc("STATISTICAL_ENGINE_REPLAY")
        comparison = compare_verifier_results(
            result("FORWARD_NULL_CONSISTENT_MISS", {"STATISTICAL_ENGINE_REPLAY": "PASS"}),
            result("FORWARD_NULL_INCOMPATIBILITY_CANDIDATE", {"STATISTICAL_ENGINE_REPLAY": "PASS"}),
            gates,
            gates,
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn(
            "SAME_RANK_AUTHORITY_ESCALATION:FORWARD_NULL_CONSISTENT_MISS:FORWARD_NULL_INCOMPATIBILITY_CANDIDATE",
            comparison.failure_codes,
        )

    def test_reverse_forward_null_semantic_rewrite_is_incomparable_not_silently_allowed(self):
        gates = gate_doc("STATISTICAL_ENGINE_REPLAY")
        comparison = compare_verifier_results(
            result("FORWARD_NULL_INCOMPATIBILITY_CANDIDATE", {"STATISTICAL_ENGINE_REPLAY": "PASS"}),
            result("FORWARD_NULL_CONSISTENT_MISS", {"STATISTICAL_ENGINE_REPLAY": "PASS"}),
            gates,
            gates,
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn(
            "INCOMPARABLE_ADMISSION_OUTCOME_REWRITE:FORWARD_NULL_INCOMPATIBILITY_CANDIDATE:FORWARD_NULL_CONSISTENT_MISS",
            comparison.failure_codes,
        )

    def test_inherited_gate_set_is_not_a_caller_argument(self):
        parameters = inspect.signature(compare_verifier_results).parameters
        self.assertNotIn("inherited_gate_ids", parameters)

    def test_inherited_gate_set_omission_attack_is_detected_by_derivation(self):
        predecessor_gate = gate_doc("TERMINAL_SUBTYPE_SEMANTICS", "TRIAL_CREATION_POLICY_REPLAY")
        successor_gate = copy.deepcopy(predecessor_gate)
        comparison = compare_verifier_results(
            result("INVALIDATED_EVIDENCE", {
                "TERMINAL_SUBTYPE_SEMANTICS": "FAIL",
                "TRIAL_CREATION_POLICY_REPLAY": "FAIL",
            }),
            result("INVALIDATED_EVIDENCE", {
                "TERMINAL_SUBTYPE_SEMANTICS": "FAIL",
                "TRIAL_CREATION_POLICY_REPLAY": "PASS",
            }),
            predecessor_gate,
            successor_gate,
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertTrue(any("INHERITED_HARDENING_LAYER_OMISSION:TRIAL_CREATION_POLICY_REPLAY" in x for x in comparison.failure_codes))
        self.assertIsNotNone(comparison.inherited_gate_set_hash)

    def test_inherited_gate_set_hash_binds_release_gate_documents(self):
        g1 = gate_doc("A", "B")
        g2 = gate_doc("A", "B")
        _, h1 = derive_inherited_gate_obligations(g1, g2)
        g3 = gate_doc("A", "B", "C")
        _, h2 = derive_inherited_gate_obligations(g1, g3)
        self.assertNotEqual(h1, h2)

    def test_blocked_gate_may_be_implemented_by_successor(self):
        gates = gate_doc("ED25519_SIGNATURE_CRYPTO")
        comparison = compare_verifier_results(
            result("NOT_ADMITTED", {"ED25519_SIGNATURE_CRYPTO": "BLOCKED"}),
            result("NOT_ADMITTED", {"ED25519_SIGNATURE_CRYPTO": "PASS"}),
            gates,
            gates,
        )
        self.assertEqual(comparison.status, "PASS")

    def test_historical_release_gate_is_exact_56_to_61_extension_by_id_set(self):
        previous = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.6-draft.json")
        current = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.7-draft.json")
        pred_ids = required_gate_ids(previous)
        current_ids = required_gate_ids(current)
        self.assertEqual(len(pred_ids), 56)
        self.assertEqual(len(current_ids), 61)
        self.assertEqual(current_ids - pred_ids, V10_CONVERGENCE_GATES)
        self.assertEqual(pred_ids - current_ids, set())
        self.assertEqual(compare_release_gate_sets(previous, current).status, "PASS")

    def test_v11_release_gate_is_exact_61_to_65_extension_by_id_set(self):
        previous = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.7-draft.json")
        current = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.8-draft.json")
        pred_ids = required_gate_ids(previous)
        current_ids = required_gate_ids(current)
        self.assertEqual(len(pred_ids), 61)
        self.assertEqual(len(current_ids), 65)
        self.assertEqual(current_ids - pred_ids, V11_HARDENING_GATES)
        self.assertEqual(pred_ids - current_ids, set())
        self.assertEqual(compare_release_gate_sets(previous, current).status, "PASS")
        self.assertEqual(current["status"], "DRAFT_NOT_SATISFIED")

    def test_release_gate_regression_is_detected_semantically_not_by_count(self):
        previous = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.7-draft.json")
        regressed = copy.deepcopy(previous)
        regressed["required_checks"] = [
            row for row in regressed["required_checks"] if row["id"] != "ED25519_SIGNATURE_CRYPTO"
        ]
        regressed["required_checks"].append({"id": "UNRELATED_NEW_GATE", "required": True})
        comparison = compare_release_gate_sets(previous, regressed)
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn("RELEASE_GATE_REGRESSION:ED25519_SIGNATURE_CRYPTO", comparison.failure_codes)

    def test_structurally_plausible_unverified_transition_is_rejected(self):
        previous = gate_doc("OLD_GATE")
        successor = gate_doc("NEW_GATE")
        fake_transition = {
            "schema": "AIFC/gate-lineage-transition/v1",
            "removed_gate_id": "OLD_GATE",
            "successor_gate_ids": ["NEW_GATE"],
            "previous_gate_definition_hash": "11" * 32,
            "successor_definition_hashes": ["22" * 32],
            "equivalence_or_strengthening_evidence_hash": "33" * 32,
            "migration_reason": "looks plausible but was never proof-replayed",
            "approved_protocol_version": "test-v2",
            "transition_hash": "44" * 32,
        }
        comparison = compare_release_gate_sets(previous, successor, [fake_transition])
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn("FAKE_GATE_STRENGTHENING_RECEIPT:OLD_GATE", comparison.failure_codes)

    def test_validator_semantics_manifest_binds_exact_runtime_and_dependency_lock(self):
        manifest_path = ROOT / "conformance" / "AIFC-VALIDATOR-SEMANTICS-MANIFEST-v1.json"
        manifest = load_json_strict(manifest_path)
        self.assertEqual(
            raw_sha256(manifest_path),
            "cfea30ba2ce6e8fac366718e5d23d581789eafd037cff17b3f61aacc1455a14e",
        )
        for source in manifest["source_files"]:
            path = ROOT / source["path"]
            self.assertEqual(git_blob_sha1(path), source["git_blob_sha1"])
            self.assertEqual(raw_sha256(path), source["raw_sha256"])
        lock = manifest["dependency_lock"]
        lock_path = ROOT / lock["path"]
        self.assertEqual(git_blob_sha1(lock_path), lock["git_blob_sha1"])
        self.assertEqual(raw_sha256(lock_path), lock["raw_sha256"])
        self.assertEqual(manifest["runtime"]["ref_resolution_policy"], "LOCAL_REPOSITORY_REGISTRY_ONLY_NO_NETWORK")
        self.assertEqual(manifest["runtime"]["duplicate_key_policy"], "REJECT")

    def test_schema_registry_v2_matches_git_and_raw_sha256_and_validator_manifest(self):
        registry = load_json_strict(ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v2.json")
        manifest_path = ROOT / registry["admission_semantics_manifest_path"]
        semantics_hash = raw_sha256(manifest_path)
        self.assertEqual(registry["admission_semantics_content_hash"], semantics_hash)
        seen = set()
        for record in registry["records"]:
            with self.subTest(schema_id=record["schema_id"]):
                self.assertNotIn(record["schema_id"], seen)
                seen.add(record["schema_id"])
                path = ROOT / record["source_path"]
                comparison = compare_schema_identity(
                    record,
                    current_schema_id=record["schema_id"],
                    current_dialect="https://json-schema.org/draft/2020-12/schema",
                    current_git_blob_sha1=git_blob_sha1(path),
                    current_raw_schema_sha256=raw_sha256(path),
                    current_admission_semantics_id=registry["admission_semantics_id"],
                    current_admission_semantics_content_hash=semantics_hash,
                )
                self.assertEqual(comparison.status, "PASS", msg=comparison.failure_codes)
                self.assertEqual(record["registered_immutable_at_commit"], "ba1cc627ec06355bb1054431b32e9f91fdd885a4")
                self.assertEqual(record["first_historical_appearance_status"], "NOT_ESTABLISHED")
                self.assertIsNone(record["first_historical_appearance_commit"])
        self.assertEqual(len(seen), 11)

    def test_same_semantics_label_with_changed_validator_content_is_rejected(self):
        registry = load_json_strict(ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v2.json")
        record = registry["records"][0]
        comparison = compare_schema_identity(
            record,
            current_schema_id=record["schema_id"],
            current_dialect=record["dialect"],
            current_git_blob_sha1=record["git_blob_sha1"],
            current_raw_schema_sha256=record["raw_schema_sha256"],
            current_admission_semantics_id=record["admission_semantics_id"],
            current_admission_semantics_content_hash="f" * 64,
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn("VALIDATOR_IMPLEMENTATION_CHANGED_WITH_SAME_SEMANTICS_ID", comparison.failure_codes)

    def test_same_schema_id_raw_source_mutation_is_rejected_even_if_git_locator_is_claimed_unchanged(self):
        registry = load_json_strict(ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v2.json")
        record = registry["records"][0]
        comparison = compare_schema_identity(
            record,
            current_schema_id=record["schema_id"],
            current_dialect=record["dialect"],
            current_git_blob_sha1=record["git_blob_sha1"],
            current_raw_schema_sha256="f" * 64,
            current_admission_semantics_id=record["admission_semantics_id"],
            current_admission_semantics_content_hash=record["admission_semantics_content_hash"],
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertIn("SAME_SCHEMA_ID_LANGUAGE_MUTATION:RAW_SHA256_CHANGED", comparison.failure_codes)

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
