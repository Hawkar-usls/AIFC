#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference/verifier"))

import lineage_vertex_reference_closure_v1 as closure
import scientific_assurance_lineage_v111h as v111h
import scientific_assurance_lineage_v112 as sal


def _materialize_bound_predecessor_for_test_harness() -> None:
    """Make the exact bound predecessor available in shallow CI clones.

    Production verification never performs this fetch. The dedicated v1.12
    workflow already uses full history. This helper only repairs test-fixture
    availability in inherited workflows that intentionally checkout depth=1.
    The fetched object is accepted only if the exact commit and exact tree
    identities match the v1.12 constants.
    """
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{sal.SOURCE_MAIN_COMMIT}^{{commit}}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode != 0:
        subprocess.run(
            [
                "git",
                "fetch",
                "--no-tags",
                "--depth=1",
                "origin",
                sal.SOURCE_MAIN_COMMIT,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    actual = subprocess.check_output(
        ["git", "rev-parse", f"{sal.SOURCE_MAIN_COMMIT}^{{tree}}"],
        text=True,
    ).strip()
    if actual != sal.SOURCE_TREE_SHA:
        raise RuntimeError("V112_TEST_HARNESS_PREDECESSOR_TREE_REBINDING")


class TestSALLineageVertexUniverseClosureV112(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _materialize_bound_predecessor_for_test_harness()
        cls.profile = json.loads((ROOT / sal.PROFILE_PATH).read_text(encoding="utf-8"))
        cls.binding = v111h._load(v111h.BINDING_PATH)
        cls.index = closure.build_repository_object_index(
            sal.SOURCE_MAIN_COMMIT, sal.SOURCE_TREE_SHA, cls.profile
        )
        cls.seed = closure.derive_seed_from_inherited_binding(cls.binding, cls.index)

    def _index(self, *, identities=None, objects=None):
        return closure.RepositoryObjectIndex(
            source_commit=self.index.source_commit,
            source_tree=self.index.source_tree,
            vertices_by_path=self.index.vertices_by_path,
            objects_by_path=objects if objects is not None else self.index.objects_by_path,
            identity_index=identities if identities is not None else self.index.identity_index,
            index_hash=self.index.index_hash,
        )

    def test_exact_reference_closure_reaches_expected_fixed_point(self):
        result = closure.compute_order_independent_reference_closure(
            self.seed, self.index, self.profile
        )
        self.assertEqual(len(self.seed), 6)
        self.assertEqual(len(result.final_vertex_paths), 11)
        self.assertEqual(len(result.discovery_manifest), 31)
        self.assertEqual(
            result.final_vertex_universe_hash,
            "11dcf1039c7fc54248a7096eb74455fe9e3d1a030c884c74d5fa5c73e7306663",
        )
        self.assertEqual(
            result.discovery_manifest_hash,
            "a664f091f2e651758ff3e4ef771239b40b88cf8190fd2d522e19532467737ba5",
        )

    def test_bfs_and_dfs_have_same_canonical_outputs(self):
        bfs = closure.compute_reference_closure(
            self.seed, self.index, self.profile, strategy="BFS"
        )
        dfs = closure.compute_reference_closure(
            self.seed, self.index, self.profile, strategy="DFS"
        )
        self.assertEqual(bfs.final_vertex_paths, dfs.final_vertex_paths)
        self.assertEqual(bfs.final_vertex_universe_hash, dfs.final_vertex_universe_hash)
        self.assertEqual(bfs.discovery_manifest_hash, dfs.discovery_manifest_hash)
        self.assertEqual(bfs.discovery_manifest, dfs.discovery_manifest)

    def test_false_fixed_point_termination_is_rejected(self):
        with self.assertRaisesRegex(
            closure.LineageVertexReferenceClosureV1Error,
            "LINEAGE_VERTEX_FIXED_POINT_FALSE_TERMINATION",
        ):
            closure._full_fixed_point_replay(self.seed, self.index, self.profile)

    def test_repository_index_omission_blocks_required_reference(self):
        identities = dict(self.index.identity_index)
        identities.pop(
            ("SEMANTIC_REFERENCE_ID", "AIFC-SAL-V1.11-SEMANTIC-REF-A"), None
        )
        with self.assertRaisesRegex(
            closure.LineageVertexReferenceClosureV1Error,
            "BLOCKED_UNRESOLVED_LINEAGE_VERTEX_REFERENCE",
        ):
            closure.compute_reference_closure(
                self.seed, self._index(identities=identities), self.profile, strategy="BFS"
            )

    def test_repository_index_injection_creates_ambiguity(self):
        identities = dict(self.index.identity_index)
        identities[
            ("SEMANTIC_REFERENCE_ID", "AIFC-SAL-V1.11-SEMANTIC-REF-A")
        ] = (
            "conformance/AIFC-CANONICAL-SEMANTIC-REFERENCE-A-v1.json",
            "conformance/AIFC-CANONICAL-SEMANTIC-REFERENCE-B-v1.json",
        )
        with self.assertRaisesRegex(
            closure.LineageVertexReferenceClosureV1Error,
            "BLOCKED_AMBIGUOUS_LINEAGE_VERTEX_REFERENCE",
        ):
            closure.compute_reference_closure(
                self.seed, self._index(identities=identities), self.profile, strategy="BFS"
            )

    def test_reference_target_companion_hash_rebinding_is_rejected(self):
        objects = dict(self.index.objects_by_path)
        path = "conformance/AIFC-SEMANTIC-DERIVATION-PROFILE-v1.json"
        mutated = copy.deepcopy(objects[path])
        mutated["resolver_profile_content_hash"] = "0" * 64
        objects[path] = mutated
        with self.assertRaisesRegex(
            closure.LineageVertexReferenceClosureV1Error,
            "LINEAGE_VERTEX_REFERENCE_TARGET_REBINDING",
        ):
            closure.compute_reference_closure(
                self.seed, self._index(objects=objects), self.profile, strategy="BFS"
            )

    def test_question_context_rebinding_is_rejected(self):
        result = closure.compute_order_independent_reference_closure(
            self.seed, self.index, self.profile
        )
        objects = dict(self.index.objects_by_path)
        path = "conformance/AIFC-CANONICAL-SEMANTIC-RESOLVER-PROFILE-v1.json"
        mutated = copy.deepcopy(objects[path])
        mutated["entailment_question_id"] = "0" * 64
        objects[path] = mutated
        with self.assertRaisesRegex(
            closure.LineageVertexReferenceClosureV1Error,
            "LINEAGE_VERTEX_QUESTION_CONTEXT_REBINDING",
        ):
            closure.verify_question_context(
                result.final_vertex_paths, self._index(objects=objects), result.question_id
            )

    def test_object_index_profile_rebinding_is_rejected(self):
        mutated = copy.deepcopy(self.profile)
        mutated["reference_rules"] = mutated["reference_rules"][:-1]
        with self.assertRaisesRegex(
            closure.LineageVertexReferenceClosureV1Error,
            "REPOSITORY_OBJECT_INDEX_PROFILE_REBINDING",
        ):
            closure.verify_profile(mutated)

    def test_closure_nonmonotone_removal_is_rejected(self):
        with self.assertRaisesRegex(
            closure.LineageVertexReferenceClosureV1Error,
            "LINEAGE_VERTEX_CLOSURE_NONMONOTONE_REMOVAL",
        ):
            closure.assert_monotone(("A", "B"), ("A",))

    def test_unresolved_internal_reference_is_not_reclassified_external(self):
        proof_path = "conformance/AIFC-SEMANTIC-DERIVATION-PROOF-v1.json"
        proof = copy.deepcopy(self.index.objects_by_path[proof_path])
        proof["source_semantic_reference_ids"][0] = "AIFC-NONEXISTENT-INTERNAL-REF"
        candidate = next(
            item for item in closure.reference_candidates(proof, self.profile)
            if item["matched_identity"] == "AIFC-NONEXISTENT-INTERNAL-REF"
        )
        self.assertEqual(
            candidate["classification"], "REQUIRED_INTERNAL_OBJECT_REFERENCE"
        )
        with self.assertRaisesRegex(
            closure.LineageVertexReferenceClosureV1Error,
            "BLOCKED_UNRESOLVED_LINEAGE_VERTEX_REFERENCE",
        ):
            closure._resolve_required(candidate, self.index)

    def test_reference_closure_discovers_second_order_formula_vertices(self):
        result = closure.compute_order_independent_reference_closure(
            self.seed, self.index, self.profile
        )
        for path in (
            "conformance/AIFC-CANONICAL-SEMANTIC-RESOLVER-PROFILE-v1.json",
            "conformance/AIFC-CANONICAL-SEMANTIC-REFERENCE-A-v1.json",
            "conformance/AIFC-CANONICAL-SEMANTIC-REFERENCE-B-v1.json",
            "conformance/AIFC-PREDECESSOR-SEMANTIC-FORMULA-v1.json",
            "conformance/AIFC-TARGET-SEMANTIC-FORMULA-v1.json",
        ):
            self.assertIn(path, result.final_vertex_paths)

    def test_discovery_manifest_preserves_multiple_occurrences(self):
        result = closure.compute_order_independent_reference_closure(
            self.seed, self.index, self.profile
        )
        proof_question = [
            item for item in result.discovery_manifest
            if item["source_vertex_path"]
            == "conformance/AIFC-SEMANTIC-DERIVATION-PROOF-v1.json"
            and item["field_name"] == "entailment_question_id"
        ]
        self.assertEqual(len(proof_question), 2)
        self.assertEqual(
            {x["source_json_pointer"] for x in proof_question},
            {
                "/entailment_question_id",
                "/raw_derivation_ast/conclusion/entailment_question_id",
            },
        )

    def test_classification_precedes_resolution_outcome(self):
        rules = [
            x for x in self.profile["reference_rules"]
            if x["field_name"] == "source_semantic_reference_ids"
        ]
        self.assertEqual(len(rules), 1)
        self.assertEqual(
            rules[0]["classification"], "REQUIRED_INTERNAL_OBJECT_REFERENCE"
        )

    def test_test_harness_materialization_is_exact_tree_bound(self):
        actual = subprocess.check_output(
            ["git", "rev-parse", f"{sal.SOURCE_MAIN_COMMIT}^{{tree}}"],
            text=True,
        ).strip()
        self.assertEqual(actual, sal.SOURCE_TREE_SHA)


if __name__ == "__main__":
    unittest.main()
