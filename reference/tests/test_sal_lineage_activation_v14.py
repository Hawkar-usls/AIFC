#!/usr/bin/env python3
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

import scientific_assurance_lineage_v14 as sal14


class SalLineageActivationV14Tests(unittest.TestCase):
    def _bound(self, path: str, blob: str, label: str):
        return sal14._read_bound_json(path, blob, label)

    def test_historical_membership_rebinding_is_rejected(self):
        path = "conformance/AIFC-RELEASE-GATE-v1.0.8-draft.json"
        fake = f"100644 blob {'0' * 40}\t{path}"
        with mock.patch.object(sal14, "_git", return_value=fake):
            with self.assertRaisesRegex(sal14.ScientificAssuranceLineageV14Error, "FALSE_HISTORICAL_TREE_MEMBERSHIP"):
                sal14.require_git_membership(sal14.HISTORICAL_COMMIT, path, "656bda0bae1d1af515a642f157149450c78d879e", "FALSE_HISTORICAL_TREE_MEMBERSHIP")

    def test_exact_historical_membership_accepts_declared_blob(self):
        path = "conformance/AIFC-RELEASE-GATE-v1.0.8-draft.json"
        blob = "656bda0bae1d1af515a642f157149450c78d879e"
        fake = f"100644 blob {blob}\t{path}"
        with mock.patch.object(sal14, "_git", return_value=fake):
            sal14.require_git_membership(sal14.HISTORICAL_COMMIT, path, blob, "FALSE_HISTORICAL_TREE_MEMBERSHIP")

    def test_schema_registry_v4_dual_hashes_resolve_exact_source_bytes(self):
        sal14._verify_schema_registry_v4()

    def test_successor_registry_is_structurally_non_self_promoting(self):
        v3 = self._bound(sal14.ROOT_V3_PATH, sal14.ROOT_V3_BLOB, "v3")
        self.assertEqual(v3["registry_authority_status"], "SUCCESSOR_REGISTRY_CANDIDATE_REQUIRES_NEXT_LINEAGE_ATTESTATION")
        self.assertNotIn(sal14.ROOT_V3_ID, {r["artifact_id"] for r in v3["records"]})

    def test_only_exact_v13_candidates_are_activated(self):
        v2 = self._bound(sal14.ROOT_V2_PATH, sal14.ROOT_V2_BLOB, "v2")
        v3 = self._bound(sal14.ROOT_V3_PATH, sal14.ROOT_V3_BLOB, "v3")
        transition = self._bound(sal14.TRANSITION_PATH, sal14.TRANSITION_BLOB, "transition")
        with mock.patch.object(sal14, "require_git_membership"):
            sal14._verify_registry_transition(v2, v3, transition)

    def test_extra_activation_is_rejected(self):
        v2 = self._bound(sal14.ROOT_V2_PATH, sal14.ROOT_V2_BLOB, "v2")
        v3 = self._bound(sal14.ROOT_V3_PATH, sal14.ROOT_V3_BLOB, "v3")
        transition = copy.deepcopy(self._bound(sal14.TRANSITION_PATH, sal14.TRANSITION_BLOB, "transition"))
        transition["activated_artifact_ids"].append("AIFC-RELEASE-GATE-v1.0.11-draft")
        with mock.patch.object(sal14, "require_git_membership"):
            with self.assertRaisesRegex(sal14.ScientificAssuranceLineageV14Error, "LINEAGE_ACTIVATED_SET_REBINDING"):
                sal14._verify_registry_transition(v2, v3, transition)

    def test_next_generation_candidate_cannot_self_promote(self):
        v2 = self._bound(sal14.ROOT_V2_PATH, sal14.ROOT_V2_BLOB, "v2")
        v3 = copy.deepcopy(self._bound(sal14.ROOT_V3_PATH, sal14.ROOT_V3_BLOB, "v3"))
        transition = self._bound(sal14.TRANSITION_PATH, sal14.TRANSITION_BLOB, "transition")
        row = next(r for r in v3["records"] if r["artifact_id"] == "AIFC-RELEASE-GATE-v1.0.11-draft")
        row["authority_status"] = "ATTESTED_SUCCESSOR_AT_COMMIT"
        row["authority_commit"] = sal14.PREDECESSOR_COMMIT
        row["authority_receipt_id"] = sal14.RECEIPT_V13_ID
        with mock.patch.object(sal14, "require_git_membership"):
            with self.assertRaises(sal14.ScientificAssuranceLineageV14Error):
                sal14._verify_registry_transition(v2, v3, transition)

    def test_retroactive_receipt_without_live_replay_flag_is_rejected(self):
        provenance = copy.deepcopy(self._bound(sal14.PROVENANCE_PATH, sal14.PROVENANCE_BLOB, "provenance"))
        provenance["receipts"][0]["live_replay_required"] = False
        with self.assertRaisesRegex(sal14.ScientificAssuranceLineageV14Error, "RETROACTIVE_AUTHORITY_RECEIPT_SELF_ASSERTION"):
            sal14._verify_provenance_records(provenance, lambda url: {})

    def test_receipt_provenance_metadata_rebinding_is_rejected(self):
        provenance = self._bound(sal14.PROVENANCE_PATH, sal14.PROVENANCE_BLOB, "provenance")
        run_lookup = {}
        artifact_lookup = {}
        for receipt in provenance["receipts"]:
            commit = receipt["tested_source_commit"]
            for run in receipt["workflow_runs"]:
                run_lookup[run["run_id"]] = {"id": run["run_id"], "name": run["workflow_name"], "head_sha": commit, "status": "completed", "conclusion": "success"}
            for artifact in receipt["artifacts"]:
                artifact_lookup[artifact["artifact_id"]] = {"id": artifact["artifact_id"], "name": artifact["name"], "digest": artifact["digest"], "expired": False, "workflow_run": {"head_sha": commit}}
        first = next(iter(run_lookup))
        run_lookup[first]["head_sha"] = "0" * 40

        def api_get(url: str):
            tail = int(url.rstrip("/").split("/")[-1])
            return artifact_lookup[tail] if "/artifacts/" in url else run_lookup[tail]

        trees = {r["tested_source_commit"]: r["tested_tree_sha"] for r in provenance["receipts"]}
        with mock.patch.object(sal14, "git_tree_sha", side_effect=lambda commit: trees[commit]):
            with self.assertRaisesRegex(sal14.ScientificAssuranceLineageV14Error, "AUTHORITY_RECEIPT_WORKFLOW_PROVENANCE_REJECTED"):
                sal14._verify_provenance_records(provenance, api_get)

    def test_release_frontier_is_exact_78_to_83(self):
        old = self._bound(sal14.RELEASE_GATE_V10_PATH, sal14.RELEASE_GATE_V10_BLOB, "gate10")
        new = self._bound(sal14.RELEASE_GATE_V11_PATH, sal14.RELEASE_GATE_V11_BLOB, "gate11")
        old_ids, new_ids = sal14._required_gate_ids(old), sal14._required_gate_ids(new)
        self.assertEqual(len(old_ids), 78)
        self.assertEqual(len(new_ids), 83)
        self.assertEqual(new_ids - old_ids, sal14.NEW_FRONTIER_GATES)

    def test_public_live_activation_api_has_no_registry_injection_surface(self):
        params = set(inspect.signature(sal14.verify_lineage_activation_live).parameters)
        self.assertEqual(params, {"token"})
        forbidden = {"registry", "resolver", "root", "repository_root", "transition", "provenance"}
        self.assertTrue(params.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
