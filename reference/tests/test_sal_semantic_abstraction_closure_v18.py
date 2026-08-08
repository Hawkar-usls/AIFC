#!/usr/bin/env python3
from __future__ import annotations

import copy
import inspect
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

import scientific_assurance_lineage_v17 as v17  # noqa: E402
import scientific_assurance_lineage_v18 as sal  # noqa: E402


class SemanticAbstractionClosureV18Tests(unittest.TestCase):
    def _membership(self) -> dict[tuple[str, str], str]:
        return {
            (v17.PREDECESSOR_COMMIT, v17.PREDECESSOR_PATH): v17.PREDECESSOR_BLOB,
            (v17.TARGET_PROFILE_COMMIT, v17.TARGET_PROFILE_PATH): v17.TARGET_PROFILE_BLOB,
        }

    def test_production_api_remains_identity_only(self) -> None:
        params = set(inspect.signature(sal.audit_semantic_abstraction_closure).parameters)
        self.assertEqual(params, {"predecessor_identity", "target_profile_identity", "entailment_question_identity"})
        self.assertFalse({"premise", "target", "compiler", "anchors", "formula", "bridge", "surface", "solver"} & params)

    def test_required_surface_is_resolved_from_content_identified_objects_not_v18_constants(self) -> None:
        pred = sal._verify_surface_definition(sal.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR")
        target = sal._verify_surface_definition(sal.TARGET_SURFACE_DEFINITION_PATH, role="TARGET")
        self.assertEqual(pred["selection_authority_status"], "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE")
        self.assertEqual(target["selection_authority_status"], "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE")
        self.assertEqual(pred["completeness_claim"], "NOT_ESTABLISHED")
        self.assertEqual(target["completeness_claim"], "NOT_ESTABLISHED")

    def test_surface_selection_rebinding_is_rejected(self) -> None:
        definition = copy.deepcopy(dict(sal._verify_surface_definition(
            sal.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR"
        )))
        definition["surface_role"] = "TARGET"
        with patch.object(v17, "_strict", return_value=definition):
            with self.assertRaisesRegex(sal.ScientificAssuranceLineageV18Error, "CONTENT_IDENTITY_REBINDING|SURFACE_SELECTION_REBINDING"):
                sal._verify_surface_definition(sal.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR")

    def test_coverage_universe_injection_is_rejected(self) -> None:
        definition = copy.deepcopy(dict(sal._verify_surface_definition(
            sal.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR"
        )))
        definition["coverage_manifest_id"] = "ATTACKER-COVERAGE"
        with patch.object(v17, "_strict", return_value=definition):
            with self.assertRaisesRegex(sal.ScientificAssuranceLineageV18Error, "CONTENT_IDENTITY_REBINDING|COVERAGE_UNIVERSE_INJECTION"):
                sal._verify_surface_definition(sal.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR")

    def test_required_surface_omission_is_rejected_relative_to_bound_surface(self) -> None:
        definition = sal._verify_surface_definition(sal.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR")
        coverage = copy.deepcopy(dict(v17._strict(
            v17.PREDECESSOR_COVERAGE_PATH, "AIFC/semantic-coverage-manifest/v1"
        )))
        coverage["covered_semantic_surface"] = coverage["covered_semantic_surface"][:-1]
        actual = set(definition["required_normative_semantic_surface"])
        with patch.object(v17, "_strict", return_value=coverage):
            with self.assertRaisesRegex(sal.ScientificAssuranceLineageV18Error, "NORMATIVE_SEMANTIC_COVERAGE_OMISSION|REQUIRED_SEMANTIC_SURFACE_OMISSION"):
                sal._verify_coverage_against_definition(v17.PREDECESSOR_COVERAGE_PATH, definition, actual)

    def test_bridge_is_content_identified_but_empty_and_unauthorized(self) -> None:
        bridge = sal._verify_bridge_theory()
        self.assertEqual(bridge["bridge_axioms"], [])
        self.assertEqual(bridge["bridge_status"], "ABSENT_NO_AUTHORITY_ADMISSIBLE_AXIOMS")
        self.assertEqual(bridge["bridge_authority_status"], "NOT_ESTABLISHED")
        self.assertEqual(bridge["abstraction_adequacy_status"], "NOT_ESTABLISHED")

    def test_disjoint_vocabulary_has_latent_non_normative_countervaluation(self) -> None:
        anchors = [v17._strict(path, "AIFC/historical-semantic-anchor/v1") for path in v17.ANCHOR_PATHS]
        predecessor_ast, _ = __import__("semantic_compiler_v1").compile_predecessor_formula(anchors)
        target = v17._read_exact_source
        with patch.object(v17, "git_tree_blob", return_value=v17.TARGET_PROFILE_BLOB):
            target_doc = target(v17.TARGET_PROFILE_PATH, v17.TARGET_PROFILE_BLOB, v17.TARGET_PROFILE_COMMIT)
        target_surface = sal._verify_surface_definition(sal.TARGET_SURFACE_DEFINITION_PATH, role="TARGET")
        target_ast, _ = __import__("semantic_compiler_v1").compile_target_formula(
            target_doc, target_surface["required_normative_semantic_surface"]
        )
        disjoint, latent, count = sal._latent_disjoint_refutation(predecessor_ast, target_ast)
        self.assertEqual(disjoint, "CONFIRMED")
        self.assertEqual(latent, "LATENT_IF_SOLVER_PREMATURELY_ENABLED")
        self.assertEqual(count, 18)

    def test_method_label_is_bound_to_exact_solver_source_and_formal_semantics(self) -> None:
        question = v17._verify_question()
        method = sal._verify_entailment_method_profile(question, 18)
        self.assertEqual(method["solver_git_blob_sha1"], sal.METHOD_SOLVER_GIT_BLOB_SHA1)
        self.assertEqual(method["formal_semantics"]["max_atoms"], 16)
        self.assertEqual(method["issued_question_atom_count"], 18)
        self.assertEqual(method["method_authority_status"], "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE")

    def test_method_capacity_blocks_current_18_atom_question(self) -> None:
        pred = sal._verify_surface_definition(sal.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR")
        target = sal._verify_surface_definition(sal.TARGET_SURFACE_DEFINITION_PATH, role="TARGET")
        bridge = sal._verify_bridge_theory()
        method = sal._verify_entailment_method_profile(v17._verify_question(), 18)
        binding = sal._verify_question_source_binding(v17._verify_question())
        blockers = sal._abstraction_closure_blockers(pred, target, bridge, method, binding)
        self.assertIn("BLOCKED_ENTAILMENT_METHOD_CAPACITY_FOR_ISSUED_QUESTION", blockers)

    def test_existing_question_is_not_mutated_to_add_dual_identity(self) -> None:
        question = v17._verify_question()
        self.assertNotIn("predecessor_raw_sha256", question)
        self.assertNotIn("target_profile_raw_sha256", question)
        binding = sal._verify_question_source_binding(question)
        self.assertEqual(binding["binding_status"], "NOT_ESTABLISHED_RAW_SHA256_MISSING")
        self.assertIsNone(binding["predecessor_raw_sha256"])
        self.assertIsNone(binding["target_profile_raw_sha256"])

    def test_old_authority_pass_would_still_not_admit_solver(self) -> None:
        pred = copy.deepcopy(dict(sal._verify_surface_definition(
            sal.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR"
        )))
        target = copy.deepcopy(dict(sal._verify_surface_definition(
            sal.TARGET_SURFACE_DEFINITION_PATH, role="TARGET"
        )))
        bridge = copy.deepcopy(dict(sal._verify_bridge_theory()))
        method = copy.deepcopy(dict(sal._verify_entailment_method_profile(v17._verify_question(), 18)))
        binding = copy.deepcopy(dict(sal._verify_question_source_binding(v17._verify_question())))
        blockers = sal._abstraction_closure_blockers(pred, target, bridge, method, binding)
        self.assertEqual(blockers[0], "BLOCKED_NORMATIVE_SEMANTIC_SURFACE_AUTHORITY")
        self.assertIn("BLOCKED_SEMANTIC_ABSTRACTION_ADEQUACY", blockers)
        self.assertIn("BLOCKED_CROSS_FORMULA_SEMANTIC_BRIDGE_ABSENT", blockers)

    def test_current_production_path_keeps_solver_at_zero(self) -> None:
        with patch.object(v17, "git_tree_blob", side_effect=lambda commit, path: self._membership()[(commit, path)]), \
             patch.object(sal, "finite_propositional_entailment", side_effect=AssertionError("solver must not run")) as solver:
            report = sal.audit_semantic_abstraction_closure(
                v17.PREDECESSOR_ID, v17.TARGET_PROFILE_ID, v17.QUESTION_ID
            )
        self.assertEqual(report.result, "BLOCKED")
        self.assertEqual(report.blocked_subtype, "BLOCKED_UNAUTHORIZED_INTERPRETATION")
        self.assertEqual(report.solver_invocation_count, 0)
        self.assertEqual(report.semantic_abstraction_adequacy, "NOT_ESTABLISHED")
        self.assertEqual(report.cross_formula_semantic_bridge, "ABSENT")
        self.assertEqual(report.entailment_method_capacity_for_issued_question, "BLOCKED_ATOM_LIMIT_18_GT_16")
        solver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
