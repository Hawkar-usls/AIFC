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

import scientific_assurance_lineage_v17 as sal  # noqa: E402
import semantic_compiler_v1 as compiler  # noqa: E402


class AuthoritativeSemanticCompilationV17Tests(unittest.TestCase):
    def _membership(self) -> dict[tuple[str, str], str]:
        return {
            (sal.PREDECESSOR_COMMIT, sal.PREDECESSOR_PATH): sal.PREDECESSOR_BLOB,
            (sal.TARGET_PROFILE_COMMIT, sal.TARGET_PROFILE_PATH): sal.TARGET_PROFILE_BLOB,
        }

    def test_production_api_forbids_caller_normative_formula_and_compiler(self) -> None:
        params = set(inspect.signature(sal.audit_authoritative_semantic_compilation).parameters)
        self.assertEqual(params, {"predecessor_identity", "target_profile_identity", "entailment_question_identity"})
        self.assertFalse({"premise", "target", "compiler", "anchors", "formula"} & params)

    def test_entailment_question_identity_is_compiler_independent(self) -> None:
        actual = compiler.entailment_question_id(
            sal.PREDECESSOR_ID,
            sal.PREDECESSOR_BLOB,
            sal.TARGET_PROFILE_ID,
            sal.TARGET_PROFILE_BLOB,
            sal.ENTAILMENT_METHOD,
        )
        self.assertEqual(actual, sal.QUESTION_ID)

    def test_current_production_path_blocks_before_solver(self) -> None:
        with patch.object(sal, "git_tree_blob", side_effect=lambda commit, path: self._membership()[(commit, path)]), \
             patch.object(sal, "finite_propositional_entailment", side_effect=AssertionError("solver must not run")) as solver:
            report = sal.audit_authoritative_semantic_compilation(
                sal.PREDECESSOR_ID, sal.TARGET_PROFILE_ID, sal.QUESTION_ID
            )
        self.assertEqual(report.result, "BLOCKED")
        self.assertEqual(report.blocked_subtype, "BLOCKED_UNAUTHORIZED_INTERPRETATION")
        self.assertEqual(report.solver_invocation_count, 0)
        solver.assert_not_called()

    def test_semantic_locator_value_rebinding_is_rejected(self) -> None:
        source = sal._read_exact_source
        with patch.object(sal, "git_tree_blob", return_value=sal.PREDECESSOR_BLOB):
            doc = source(sal.PREDECESSOR_PATH, sal.PREDECESSOR_BLOB, sal.PREDECESSOR_COMMIT)
        anchor = copy.deepcopy(dict(sal._strict(sal.ANCHOR_PATHS[0], "AIFC/historical-semantic-anchor/v1")))
        anchor["semantic_loci"][0]["located_value_sha256"] = "0" * 64
        with self.assertRaisesRegex(sal.ScientificAssuranceLineageV17Error, "SEMANTIC_LOCATOR_VALUE_REBINDING"):
            sal._verify_anchor(anchor, doc)

    def test_retroactive_executable_semantics_claim_is_rejected(self) -> None:
        with patch.object(sal, "git_tree_blob", return_value=sal.PREDECESSOR_BLOB):
            doc = sal._read_exact_source(sal.PREDECESSOR_PATH, sal.PREDECESSOR_BLOB, sal.PREDECESSOR_COMMIT)
        anchor = copy.deepcopy(dict(sal._strict(sal.ANCHOR_PATHS[0], "AIFC/historical-semantic-anchor/v1")))
        anchor["retroactive_discovery_of_preexisting_executable_semantics"] = True
        with self.assertRaisesRegex(sal.ScientificAssuranceLineageV17Error, "RETROACTIVE_SEMANTIC_INTERPRETATION_REBINDING"):
            sal._verify_anchor(anchor, doc)

    def test_normative_semantic_coverage_omission_is_rejected(self) -> None:
        with self.assertRaisesRegex(compiler.SemanticCompilerV1Error, "NORMATIVE_SEMANTIC_COVERAGE_OMISSION"):
            compiler.verify_exact_coverage(["A", "B"], ["A"])

    def test_deterministic_ambiguity_does_not_choose_a_semantic_locus(self) -> None:
        doc = {"required_checks": [{"id":"X","required":True},{"id":"X","required":True}]}
        with self.assertRaisesRegex(compiler.SemanticCompilerV1Error, "CARDINALITY"):
            compiler.located_value(doc, "REQUIRED_CHECK_ID", "X")

    def test_compiler_identity_does_not_imply_compiler_authority(self) -> None:
        profile = sal._verify_compilation_profile()
        self.assertEqual(profile["compiler_authority_status"], "SUCCESSOR_CREATED_COMPILER_IDENTITY_ONLY")
        self.assertEqual(profile["profile_authority_status"], "SUCCESSOR_CANDIDATE_REQUIRES_PREDECESSOR_AUTHORITY")

    def test_theorem_substitution_is_rejected_after_deterministic_compilation(self) -> None:
        anchors = [sal._strict(path, "AIFC/historical-semantic-anchor/v1") for path in sal.ANCHOR_PATHS]
        ast, bindings = compiler.compile_predecessor_formula(anchors)
        tampered = copy.deepcopy(ast)
        tampered["args"] = tampered["args"][:-1]
        with self.assertRaisesRegex(sal.ScientificAssuranceLineageV17Error, "ENTAILMENT_THEOREM_SUBSTITUTION"):
            sal._verify_formula(
                sal.PREDECESSOR_FORMULA_PATH,
                "PREDECESSOR_PREMISE",
                sal.PREDECESSOR_FORMULA_HASH,
                [
                    "AIFC-SEMANTIC-ANCHOR-AUTHORITY-CLOSED-PROOF-V1",
                    "AIFC-SEMANTIC-ANCHOR-GATE-DEFINITION-HISTORICAL-ANCHOR-V1",
                    "AIFC-SEMANTIC-ANCHOR-GATE-ATOM-SEMANTIC-IDENTITY-V1",
                ],
                "AIFC-SAL-V1.7-PREDECESSOR-SEMANTIC-COVERAGE-V1",
                tampered,
                bindings,
            )

    def test_semantic_closure_can_only_open_after_interpretation_compiler_and_coverage_authority(self) -> None:
        anchors = [copy.deepcopy(dict(sal._strict(path, "AIFC/historical-semantic-anchor/v1"))) for path in sal.ANCHOR_PATHS]
        anchors.append(copy.deepcopy(dict(sal._strict(sal.TARGET_ANCHOR_PATH, "AIFC/historical-semantic-anchor/v1"))))
        for anchor in anchors:
            anchor["interpretation_status"] = "AUTHORITY_RATIFIED_INTERPRETATION"
            anchor["authority_lineage_status"] = "AUTHORITY_LINEAGE_ESTABLISHED"
        profile = copy.deepcopy(dict(sal._verify_compilation_profile()))
        profile["compiler_authority_status"] = "PREDECESSOR_AUTHORITY_ADMITTED_COMPILER"
        profile["profile_authority_status"] = "AUTHORITY_ADMISSIBLE"
        pred_cov = copy.deepcopy(dict(sal._strict(sal.PREDECESSOR_COVERAGE_PATH, "AIFC/semantic-coverage-manifest/v1")))
        target_cov = copy.deepcopy(dict(sal._strict(sal.TARGET_COVERAGE_PATH, "AIFC/semantic-coverage-manifest/v1")))
        pred_cov["coverage_status"] = "AUTHORITY_ADMISSIBLE_EXACT_COVERAGE"
        target_cov["coverage_status"] = "AUTHORITY_ADMISSIBLE_EXACT_COVERAGE"
        self.assertIsNone(sal._semantic_closure_blocker(anchors, profile, pred_cov, target_cov))


if __name__ == "__main__":
    unittest.main()
