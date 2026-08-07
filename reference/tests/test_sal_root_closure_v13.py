import hashlib
import inspect
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from schema_runtime import validate_protocol_object  # noqa: E402
from scientific_assurance_lineage_v13 import (  # noqa: E402
    AUTHORITY_RECEIPT_ID,
    NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
    NORMATIVE_ROOT_REGISTRY_ID,
    NORMATIVE_ROOT_REGISTRY_PATH,
    PREDECESSOR_EXACT_MAIN_COMMIT,
    PREDECESSOR_NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
    NormativeRootClosureError,
    RootClosedNormativeRepositoryResolver,
    _load_authority_receipt,
    _read_bound_json,
    build_assurance_monotonicity_record_v4,
    compare_verifier_results_root_closed,
    git_blob_sha1_bytes,
)

V13_ROOT_CLOSURE_GATES = {
    "NORMATIVE_ROOT_REGISTRY_CONTENT_IDENTITY",
    "NORMATIVE_RESOLVER_PROVENANCE",
    "AUTHORITY_STATUS_TRANSITION_ENFORCED",
    "SAL_SCHEMA_IDENTITY_REGISTRATION",
    "INHERITED_HASH_PROFILE_IMPLEMENTATION_BINDING",
}

V12_ISSUED_SAL_SCHEMAS = {
    "AIFC/normative-assurance-root-registry/v1",
    "AIFC/inherited-gate-obligation-set/v1",
    "AIFC/assurance-monotonicity-record/v3",
    "AIFC/assurance-hash-profile-manifest/v1",
    "AIFC/inherited-gate-hash-profile/v1",
}


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def result(grade="NOT_ADMITTED", gates=None):
    return {"terminal_grade": grade, "gate_results": gates or {}}


def required_ids(doc):
    return {row["id"] for row in doc["required_checks"] if row.get("required") is True}


class SalRootClosureV13Tests(unittest.TestCase):
    def resolver(self):
        return RootClosedNormativeRepositoryResolver.from_repository_authority()

    def test_root_closed_comparator_has_no_resolver_or_registry_injection_surface(self):
        params = inspect.signature(compare_verifier_results_root_closed).parameters
        for forbidden in ("normative_resolver", "registry", "registry_path", "repository_root", "root"):
            self.assertNotIn(forbidden, params)
        self.assertIn("predecessor_release_gate_id", params)
        self.assertIn("successor_release_gate_id", params)

    def test_direct_resolver_construction_is_forbidden(self):
        with self.assertRaises(TypeError) as ctx:
            RootClosedNormativeRepositoryResolver(ROOT, {})
        self.assertIn("CALLER_SUPPLIED_ROOT_REGISTRY_FORBIDDEN", str(ctx.exception))

    def test_root_registry_itself_is_content_identified(self):
        raw = (ROOT / NORMATIVE_ROOT_REGISTRY_PATH).read_bytes()
        self.assertEqual(git_blob_sha1_bytes(raw), NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1)
        registry = load(NORMATIVE_ROOT_REGISTRY_PATH)
        self.assertEqual(registry["registry_id"], NORMATIVE_ROOT_REGISTRY_ID)
        self.assertEqual(
            registry["predecessor_registry_git_blob_sha1"],
            PREDECESSOR_NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
        )
        self.assertEqual(registry["predecessor_exact_main_commit"], PREDECESSOR_EXACT_MAIN_COMMIT)

    def test_wrong_root_registry_content_identity_is_rejected(self):
        with self.assertRaises(NormativeRootClosureError) as ctx:
            _read_bound_json(NORMATIVE_ROOT_REGISTRY_PATH, "0" * 40, "ATTACK_ROOT")
        self.assertIn("NORMATIVE_CONTENT_IDENTITY_MISMATCH", str(ctx.exception))

    def test_exact_v12_receipt_is_runtime_closed_and_head_bound(self):
        receipt = _load_authority_receipt(AUTHORITY_RECEIPT_ID, PREDECESSOR_EXACT_MAIN_COMMIT)
        self.assertEqual(receipt["tested_source_commit"], PREDECESSOR_EXACT_MAIN_COMMIT)
        self.assertEqual(receipt["unit_test_count"], 165)
        self.assertEqual(len(receipt["artifacts"]), 3)
        self.assertTrue(all(a["head_sha"] == PREDECESSOR_EXACT_MAIN_COMMIT for a in receipt["artifacts"]))

    def test_authority_receipt_commit_rebinding_is_rejected(self):
        with self.assertRaises(NormativeRootClosureError) as ctx:
            _load_authority_receipt(AUTHORITY_RECEIPT_ID, "0" * 40)
        self.assertIn("NORMATIVE_AUTHORITY_RECEIPT_REBINDING", str(ctx.exception))

    def test_attested_successor_is_promoted_only_through_exact_receipt(self):
        resolved = self.resolver().resolve("AIFC-RELEASE-GATE-v1.0.9-draft", "RELEASE_GATE")
        self.assertEqual(resolved.authority_status, "ATTESTED_SUCCESSOR_AT_COMMIT")
        self.assertEqual(resolved.authority_commit, PREDECESSOR_EXACT_MAIN_COMMIT)
        self.assertEqual(resolved.authority_receipt_id, AUTHORITY_RECEIPT_ID)

    def test_unattested_successor_normative_promotion_is_rejected(self):
        with self.assertRaises(NormativeRootClosureError) as ctx:
            self.resolver().resolve("AIFC-RELEASE-GATE-v1.0.10-draft", "RELEASE_GATE")
        self.assertIn("UNATTESTED_SUCCESSOR_NORMATIVE_PROMOTION", str(ctx.exception))

    def test_schema_registry_v3_registers_v12_and_v13_sal_schemas_by_dual_hash(self):
        registry = load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v3.json")
        validate_protocol_object(registry, "AIFC/schema-identity-registry/v3")
        self.assertEqual(registry["predecessor_registry_git_blob_sha1"], "bb7ef880d9fced16ee42ea266d1f97409457877b")
        records = {row["schema_id"]: row for row in registry["records"]}
        self.assertTrue(V12_ISSUED_SAL_SCHEMAS.issubset(records))
        self.assertGreaterEqual(len(records), 10)
        for schema_id, row in records.items():
            raw = (ROOT / row["source_path"]).read_bytes()
            self.assertEqual(git_blob_sha1_bytes(raw), row["git_blob_sha1"], schema_id)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["raw_schema_sha256"], schema_id)

    def test_inherited_hash_implementation_binding_resolves_exact_source_bytes(self):
        binding = load("conformance/AIFC-INHERITED-GATE-HASH-IMPLEMENTATION-BINDING-v1.json")
        validate_protocol_object(binding, "AIFC/inherited-gate-hash-implementation-binding/v1")
        self.assertEqual(binding["source_observed_at_commit"], "7f3f3662dd99bfb2baec7f91d2c39ec61631898c")
        for key in ("canonicalization_source", "hash_implementation_source"):
            src = binding[key]
            self.assertEqual(git_blob_sha1_bytes((ROOT / src["path"]).read_bytes()), src["git_blob_sha1"])

    def test_v13_release_frontier_is_exact_additive_73_to_78(self):
        previous = load("conformance/AIFC-RELEASE-GATE-v1.0.9-draft.json")
        current = load("conformance/AIFC-RELEASE-GATE-v1.0.10-draft.json")
        pred, succ = required_ids(previous), required_ids(current)
        self.assertEqual(len(pred), 73)
        self.assertEqual(len(succ), 78)
        self.assertEqual(pred - succ, set())
        self.assertEqual(succ - pred, V13_ROOT_CLOSURE_GATES)
        self.assertEqual(current["status"], "DRAFT_NOT_SATISFIED")

    def test_root_closed_comparison_replays_current_attested_v12_transition(self):
        comparison = compare_verifier_results_root_closed(
            result(),
            result(),
            predecessor_release_gate_id="AIFC-RELEASE-GATE-v1.0.8-draft",
            successor_release_gate_id="AIFC-RELEASE-GATE-v1.0.9-draft",
        )
        self.assertEqual(comparison.status, "PASS", comparison.failure_codes)
        self.assertEqual(comparison.normative_root_registry_git_blob_sha1, NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1)
        record = build_assurance_monotonicity_record_v4(
            comparison,
            predecessor_verifier="AIFC-Verifier-A-v0.6",
            successor_verifier="AIFC-Verifier-A-v0.7-candidate",
            predecessor_release_gate_id="AIFC-RELEASE-GATE-v1.0.8-draft",
            successor_release_gate_id="AIFC-RELEASE-GATE-v1.0.9-draft",
        )
        self.assertTrue(record["resolver_provenance_closed"])
        self.assertTrue(record["authority_status_enforced"])
        self.assertEqual(record["normative_root_registry_git_blob_sha1"], NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1)

    def test_inherited_fail_still_cannot_disappear(self):
        comparison = compare_verifier_results_root_closed(
            result(gates={"ED25519_SIGNATURE_CRYPTO": "FAIL"}),
            result(gates={"ED25519_SIGNATURE_CRYPTO": "PASS"}),
            predecessor_release_gate_id="AIFC-RELEASE-GATE-v1.0.8-draft",
            successor_release_gate_id="AIFC-RELEASE-GATE-v1.0.9-draft",
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertTrue(any(x.startswith("INHERITED_HARDENING_LAYER_OMISSION:ED25519_SIGNATURE_CRYPTO") for x in comparison.failure_codes))


if __name__ == "__main__":
    unittest.main()
