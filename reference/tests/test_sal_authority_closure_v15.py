import copy
import inspect
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "reference" / "verifier"
import sys
sys.path.insert(0, str(VERIFIER))

import scientific_assurance_lineage_v15 as v15


class SalAuthorityClosureV15Tests(unittest.TestCase):
    def load_json(self, relative_path):
        return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))

    def tree_map(self):
        return {
            v15.HISTORICAL_COMMIT: "e3aa8a8cd09f0faa9a6f9e976d0f5cbe8291f2c9",
            v15.V13_PREDECESSOR_COMMIT: "2e939271d22d0a1906c93bd7e0fced77780aa88c",
            v15.V14_MAIN_COMMIT: "495188b12f8b8d728732ee44a502b2089203ebb9",
        }

    def workflow_blob_map(self):
        provenance = self.load_json(v15.PROVENANCE_V2_PATH)
        return {
            (receipt["tested_source_commit"], run["workflow_path"]): run["workflow_git_blob_sha1"]
            for receipt in provenance["receipts"]
            for run in receipt["workflow_runs"]
        }

    def test_local_hardening_passes_but_authority_closed_induction_stays_blocked(self):
        trees = self.tree_map()
        workflow_blobs = self.workflow_blob_map()
        with patch.object(v15, "verify_lineage_activation_local", return_value=None):
            with patch.object(v15, "git_tree_sha", side_effect=lambda commit: trees[commit]):
                with patch.object(v15, "git_tree_blob", side_effect=lambda commit, path: workflow_blobs[(commit, path)]):
                    report = v15.verify_authority_closure_local()
        self.assertTrue(report.provenance_receipt_content_binding)
        self.assertTrue(report.historical_workflow_definition_identity)
        self.assertTrue(report.successor_registry_exact_delta)
        self.assertFalse(report.lineage_transition_profile_authority_anchor)
        self.assertFalse(report.historical_artifact_semantic_replay)
        self.assertEqual(report.receipt_count, 3)
        self.assertEqual(report.workflow_count, 15)
        self.assertEqual(report.artifact_count, 9)
        self.assertFalse(report.authority_closed_finite_induction)

    def test_provenance_receipt_workflow_content_disconnect_is_rejected(self):
        provenance = self.load_json(v15.PROVENANCE_V2_PATH)
        tampered = copy.deepcopy(provenance)
        tampered["receipts"][1]["workflow_runs"][0]["run_id"] += 1
        trees = self.tree_map()
        with patch.object(v15, "git_tree_sha", side_effect=lambda commit: trees[commit]):
            with self.assertRaisesRegex(v15.ScientificAssuranceLineageV15Error, "PROVENANCE_RECEIPT_WORKFLOW_CONTENT_DISCONNECT"):
                v15._verify_receipt_content_binding(tampered)

    def test_provenance_receipt_artifact_content_disconnect_is_rejected(self):
        provenance = self.load_json(v15.PROVENANCE_V2_PATH)
        tampered = copy.deepcopy(provenance)
        tampered["receipts"][2]["artifacts"][0]["artifact_id"] += 1
        trees = self.tree_map()
        with patch.object(v15, "git_tree_sha", side_effect=lambda commit: trees[commit]):
            with self.assertRaisesRegex(v15.ScientificAssuranceLineageV15Error, "PROVENANCE_RECEIPT_ARTIFACT_CONTENT_DISCONNECT"):
                v15._verify_receipt_content_binding(tampered)

    def test_historical_workflow_definition_rebinding_is_rejected(self):
        provenance = self.load_json(v15.PROVENANCE_V2_PATH)
        tampered = copy.deepcopy(provenance)
        original_blob = provenance["receipts"][0]["workflow_runs"][0]["workflow_git_blob_sha1"]
        tampered["receipts"][0]["workflow_runs"][0]["workflow_git_blob_sha1"] = "0" * 40
        with patch.object(v15, "git_tree_blob", return_value=original_blob):
            with self.assertRaisesRegex(v15.ScientificAssuranceLineageV15Error, "HISTORICAL_WORKFLOW_DEFINITION_REBINDING"):
                v15._verify_workflow_definition_membership(tampered)

    def test_successor_registry_extra_record_injection_is_rejected(self):
        v2 = self.load_json(v15.ROOT_V2_PATH)
        v3 = self.load_json(v15.ROOT_V3_PATH)
        injected = copy.deepcopy(v3)
        evil = copy.deepcopy(injected["records"][-1])
        evil["artifact_id"] = "EVIL_EXTRA_ARTIFACT"
        evil["relative_path"] = "conformance/EVIL-EXTRA.json"
        evil["git_blob_sha1"] = "1" * 40
        evil["authority_status"] = "ATTESTED_SUCCESSOR_AT_COMMIT"
        evil["authority_commit"] = v15.V13_PREDECESSOR_COMMIT
        evil["authority_receipt_id"] = "AIFC-SAL-V1.3-EXACT-MAIN-RECEIPT-eeee61c"
        injected["records"].append(evil)

        original = v15._read_bound_json
        def fake_read(path, blob, label):
            if path == v15.ROOT_V2_PATH:
                return v2
            if path == v15.ROOT_V3_PATH:
                return injected
            return original(path, blob, label)

        with patch.object(v15, "_read_bound_json", side_effect=fake_read):
            with patch.object(v15, "_validate", return_value=None):
                with self.assertRaisesRegex(v15.ScientificAssuranceLineageV15Error, "SUCCESSOR_REGISTRY_EXTRA_RECORD_INJECTION"):
                    v15._verify_registry_exact_delta()

    def test_exact_v2_to_v3_registry_delta_passes(self):
        v15._verify_registry_exact_delta()

    def test_successor_created_transition_profile_is_not_mistaken_for_predecessor_authority(self):
        self.assertFalse(v15._verify_transition_profile_authority_anchor())

    def test_fake_predecessor_profile_authority_invalidates_frozen_obstruction(self):
        v2 = self.load_json(v15.ROOT_V2_PATH)
        injected = copy.deepcopy(v2)
        injected["records"].append({
            "artifact_id": v15.PROFILE_ID,
            "kind": "LINEAGE_TRANSITION_PROFILE",
            "expected_schema": "AIFC/lineage-transition-profile/v1",
            "relative_path": v15.PROFILE_PATH,
            "git_blob_sha1": v15.PROFILE_BLOB,
            "authority_status": "ATTESTED_SUCCESSOR_AT_COMMIT",
            "authority_commit": v15.V13_PREDECESSOR_COMMIT,
            "authority_receipt_id": "AIFC-SAL-V1.3-EXACT-MAIN-RECEIPT-eeee61c",
        })
        original = v15._read_bound_json
        def fake_read(path, blob, label):
            if path == v15.ROOT_V2_PATH:
                return injected
            return original(path, blob, label)
        with patch.object(v15, "_read_bound_json", side_effect=fake_read):
            with self.assertRaisesRegex(v15.ScientificAssuranceLineageV15Error, "AUTHORITY_CLOSURE_OBSTRUCTION_FALSE_NEGATIVE"):
                v15._verify_transition_profile_authority_anchor()

    def test_release_frontier_is_exact_83_to_88(self):
        v15._verify_release_frontier()

    def test_schema_registry_v5_dual_hashes_resolve_exact_source_bytes(self):
        v15._verify_schema_registry_v5()

    def test_public_live_api_has_no_registry_or_transition_injection_surface(self):
        params = set(inspect.signature(v15.verify_authority_closure_live).parameters)
        self.assertEqual(params, {"token"})

    def test_v1_receipt_binding_uses_exact_role_run_id_projection(self):
        receipt = self.load_json("conformance/AIFC-NORMATIVE-AUTHORITY-RECEIPT-7e58b47-v1.json")
        provenance = self.load_json(v15.PROVENANCE_V2_PATH)
        first = copy.deepcopy(provenance["receipts"][0])
        mode, receipt_projection = v15._receipt_workflow_projection(receipt)
        self.assertEqual(mode, "v1")
        self.assertEqual(receipt_projection, v15._provenance_workflow_projection(first, mode))
        first["workflow_runs"][0]["workflow_name"] = "different live metadata name"
        self.assertEqual(receipt_projection, v15._provenance_workflow_projection(first, mode))


if __name__ == "__main__":
    unittest.main()
