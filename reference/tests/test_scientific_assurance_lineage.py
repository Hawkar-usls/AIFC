import hashlib
import inspect
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import canonical_json_bytes, load_json_strict  # noqa: E402
from scientific_assurance_lineage import (  # noqa: E402
    ADMISSION_ORDER_ARTIFACT_ID,
    INHERITED_GATE_HASH_PROFILE_ID,
    NORMATIVE_ROOT_REGISTRY_ID,
    SAL_BOOTSTRAP_ROOT_COMMIT,
    NormativeIdentityError,
    NormativeRepositoryResolver,
    compare_verifier_results_anchored,
    git_blob_sha1_bytes,
    inherited_gate_obligation_hash_v1,
)


V12_PROOF_ANCHORING_GATES = {
    "NORMATIVE_RELEASE_GATE_IDENTITY",
    "NORMATIVE_ROOT_LINEAGE_VALID",
    "ADMISSION_ORDER_PROFILE_CONTENT_IDENTITY",
    "INHERITED_GATE_SET_DOMAIN_IDENTITY",
    "ASSURANCE_HASH_PROFILE_CONTENT_IDENTITY",
    "GATE_DEFINITION_HISTORICAL_ANCHOR",
    "GATE_ATOM_SEMANTIC_IDENTITY",
    "AUTHORITY_CLOSED_PROOF",
}


def result(grade, gates=None):
    return {
        "terminal_grade": grade,
        "gate_results": gates or {},
    }


def required_ids(doc):
    return {row["id"] for row in doc["required_checks"] if row.get("required") is True}


def write_json(path: Path, value) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return git_blob_sha1_bytes(raw)


class ScientificAssuranceLineageTests(unittest.TestCase):
    def resolver(self):
        return NormativeRepositoryResolver.from_file(ROOT)

    def test_bootstrap_root_is_exact_post_merge_v11_main(self):
        registry = load_json_strict(ROOT / "conformance" / "AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json")
        self.assertEqual(registry["registry_id"], NORMATIVE_ROOT_REGISTRY_ID)
        self.assertEqual(registry["bootstrap_root_commit"], SAL_BOOTSTRAP_ROOT_COMMIT)
        self.assertEqual(SAL_BOOTSTRAP_ROOT_COMMIT, "908de7afddcf9f72c98c2b3fb696a41be1e438e0")

    def test_anchored_api_does_not_accept_raw_normative_gate_documents(self):
        params = inspect.signature(compare_verifier_results_anchored).parameters
        self.assertIn("predecessor_release_gate_id", params)
        self.assertIn("successor_release_gate_id", params)
        self.assertIn("normative_resolver", params)
        self.assertNotIn("predecessor_release_gate", params)
        self.assertNotIn("successor_release_gate", params)
        self.assertNotIn("admission_order", params)
        self.assertNotIn("inherited_gate_ids", params)

    def test_v12_release_frontier_is_exact_additive_65_to_73(self):
        previous = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.8-draft.json")
        current = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.9-draft.json")
        previous_ids = required_ids(previous)
        current_ids = required_ids(current)
        self.assertEqual(len(previous_ids), 65)
        self.assertEqual(len(current_ids), 73)
        self.assertEqual(current_ids - previous_ids, V12_PROOF_ANCHORING_GATES)
        self.assertEqual(previous_ids - current_ids, set())
        self.assertEqual(current["status"], "DRAFT_NOT_SATISFIED")

    def test_real_v11_root_to_v12_candidate_additive_comparison_is_anchored(self):
        comparison = compare_verifier_results_anchored(
            result("NOT_ADMITTED"),
            result("NOT_ADMITTED"),
            predecessor_release_gate_id="AIFC-RELEASE-GATE-v1.0.8-draft",
            successor_release_gate_id="AIFC-RELEASE-GATE-v1.0.9-draft",
            normative_resolver=self.resolver(),
        )
        self.assertEqual(comparison.status, "PASS", msg=comparison.failure_codes)
        self.assertEqual(comparison.inherited_gate_hash_profile_id, INHERITED_GATE_HASH_PROFILE_ID)
        self.assertEqual(
            comparison.predecessor_release_gate_git_blob_sha1,
            "656bda0bae1d1af515a642f157149450c78d879e",
        )
        self.assertEqual(
            comparison.admission_order_git_blob_sha1,
            "38eeb695caf781dcdc79115d4903c743db7311f9",
        )

    def test_release_gate_document_rebinding_is_rejected_before_derivation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "conformance").mkdir(parents=True)
            shutil.copy2(
                ROOT / "conformance" / "AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json",
                root / "conformance" / "AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json",
            )
            source = ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.8-draft.json"
            target = root / "conformance" / source.name
            target.write_bytes(source.read_bytes() + b"\n")
            resolver = NormativeRepositoryResolver.from_file(root)
            with self.assertRaises(NormativeIdentityError) as ctx:
                resolver.resolve("AIFC-RELEASE-GATE-v1.0.8-draft", "RELEASE_GATE")
            self.assertIn("RELEASE_GATE_DOCUMENT_REBINDING", str(ctx.exception))

    def test_same_admission_order_id_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "conformance").mkdir(parents=True)
            shutil.copy2(
                ROOT / "conformance" / "AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json",
                root / "conformance" / "AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json",
            )
            source = ROOT / "conformance" / "AIFC-ADMISSION-AUTHORITY-ORDER-v1.json"
            target = root / "conformance" / source.name
            target.write_bytes(source.read_bytes() + b"\n")
            resolver = NormativeRepositoryResolver.from_file(root)
            with self.assertRaises(NormativeIdentityError) as ctx:
                resolver.resolve(ADMISSION_ORDER_ARTIFACT_ID, "ADMISSION_ORDER")
            self.assertIn("SAME_ADMISSION_ORDER_ID_MUTATION", str(ctx.exception))

    def test_assurance_hash_profile_semantics_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "conformance").mkdir(parents=True)
            shutil.copy2(
                ROOT / "conformance" / "AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json",
                root / "conformance" / "AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json",
            )
            source = ROOT / "conformance" / "AIFC-ASSURANCE-HASH-PROFILE-MANIFEST-v1.json"
            target = root / "conformance" / source.name
            target.write_bytes(source.read_bytes() + b"\n")
            resolver = NormativeRepositoryResolver.from_file(root)
            with self.assertRaises(NormativeIdentityError) as ctx:
                resolver.resolve("AIFC/assurance-evidence-hash/v1", "ASSURANCE_HASH_PROFILE")
            self.assertIn("ASSURANCE_HASH_PROFILE_SEMANTICS_MUTATION", str(ctx.exception))

    def test_assurance_hash_profile_manifest_binds_historical_v1_sources(self):
        manifest = self.resolver().resolve(
            "AIFC/assurance-evidence-hash/v1", "ASSURANCE_HASH_PROFILE"
        ).parsed_json
        self.assertEqual(manifest["historical_source_commit"], SAL_BOOTSTRAP_ROOT_COMMIT)
        self.assertEqual(
            set(manifest["member_schema_ids"]),
            {
                "AIFC/gate-definition/v1",
                "AIFC/gate-strengthening-evidence/v1",
                "AIFC/gate-lineage-transition/v1",
            },
        )
        for key in ("canonicalization_source", "hash_implementation_source"):
            source = manifest[key]
            raw = (ROOT / source["path"]).read_bytes()
            self.assertEqual(git_blob_sha1_bytes(raw), source["git_blob_sha1"])

    def test_inherited_obligation_hash_has_dedicated_domain_identity(self):
        material = {
            "schema": "AIFC/inherited-gate-obligation-set/v1",
            "hash_profile_id": INHERITED_GATE_HASH_PROFILE_ID,
            "predecessor_release_gate_id": "P",
            "predecessor_release_gate_git_blob_sha1": "1" * 40,
            "successor_release_gate_id": "S",
            "successor_release_gate_git_blob_sha1": "2" * 40,
            "obligations": [
                {
                    "predecessor_gate_id": "A",
                    "successor_gate_ids": ["A"],
                    "transition_hash": None,
                }
            ],
        }
        h1 = inherited_gate_obligation_hash_v1(material)
        h2 = inherited_gate_obligation_hash_v1(material)
        legacy_plain = hashlib.sha256(canonical_json_bytes(material)).hexdigest()
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, legacy_plain)

    def test_gate_removal_is_blocked_until_definition_and_atom_semantics_are_anchored(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            order = load_json_strict(ROOT / "conformance" / "AIFC-ADMISSION-AUTHORITY-ORDER-v1.json")
            order_path = root / "conformance" / "order.json"
            order_blob = write_json(order_path, order)

            pred = {
                "schema": "AIFC/conformance-release-gate/v1",
                "required_checks": [
                    {"id": "OLD_GATE", "required": True},
                    {"id": "KEEP_GATE", "required": True},
                ],
            }
            succ = {
                "schema": "AIFC/conformance-release-gate/v1",
                "required_checks": [
                    {"id": "KEEP_GATE", "required": True},
                    {"id": "NEW_GATE", "required": True},
                ],
            }
            pred_blob = write_json(root / "conformance" / "pred.json", pred)
            succ_blob = write_json(root / "conformance" / "succ.json", succ)
            registry = {
                "schema": "AIFC/normative-assurance-root-registry/v1",
                "registry_id": NORMATIVE_ROOT_REGISTRY_ID,
                "bootstrap_root_commit": SAL_BOOTSTRAP_ROOT_COMMIT,
                "records": [
                    {
                        "artifact_id": "PRED",
                        "kind": "RELEASE_GATE",
                        "expected_schema": "AIFC/conformance-release-gate/v1",
                        "relative_path": "conformance/pred.json",
                        "git_blob_sha1": pred_blob,
                        "authority_status": "HISTORICAL_ROOT_AT_BOOTSTRAP_COMMIT",
                    },
                    {
                        "artifact_id": "SUCC",
                        "kind": "RELEASE_GATE",
                        "expected_schema": "AIFC/conformance-release-gate/v1",
                        "relative_path": "conformance/succ.json",
                        "git_blob_sha1": succ_blob,
                        "authority_status": "SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION",
                    },
                    {
                        "artifact_id": ADMISSION_ORDER_ARTIFACT_ID,
                        "kind": "ADMISSION_ORDER",
                        "expected_schema": "AIFC/admission-authority-order/v1",
                        "relative_path": "conformance/order.json",
                        "git_blob_sha1": order_blob,
                        "authority_status": "HISTORICAL_ROOT_AT_BOOTSTRAP_COMMIT",
                    },
                ],
            }
            comparison = compare_verifier_results_anchored(
                result("NOT_ADMITTED"),
                result("NOT_ADMITTED"),
                predecessor_release_gate_id="PRED",
                successor_release_gate_id="SUCC",
                normative_resolver=NormativeRepositoryResolver(root, registry),
            )
            self.assertEqual(comparison.status, "FAIL")
            self.assertIn(
                "GATE_DEFINITION_HISTORICAL_ANCHOR_NOT_ESTABLISHED:OLD_GATE",
                comparison.failure_codes,
            )
            self.assertIn(
                "GATE_ATOM_SEMANTIC_IDENTITY_NOT_ESTABLISHED:OLD_GATE",
                comparison.failure_codes,
            )

    def test_inherited_fail_still_cannot_disappear_under_anchored_path(self):
        comparison = compare_verifier_results_anchored(
            result("NOT_ADMITTED", {"ED25519_SIGNATURE_CRYPTO": "FAIL"}),
            result("NOT_ADMITTED", {"ED25519_SIGNATURE_CRYPTO": "PASS"}),
            predecessor_release_gate_id="AIFC-RELEASE-GATE-v1.0.8-draft",
            successor_release_gate_id="AIFC-RELEASE-GATE-v1.0.9-draft",
            normative_resolver=self.resolver(),
        )
        self.assertEqual(comparison.status, "FAIL")
        self.assertTrue(
            any(
                code.startswith("INHERITED_HARDENING_LAYER_OMISSION:ED25519_SIGNATURE_CRYPTO")
                for code in comparison.failure_codes
            )
        )


if __name__ == "__main__":
    unittest.main()
