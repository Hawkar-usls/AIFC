#!/usr/bin/env python3
from __future__ import annotations

import copy
import inspect
import json
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import domain_hash  # noqa: E402
from scientific_assurance_lineage_v16 import EntailmentResult, finite_propositional_entailment  # noqa: E402
import scientific_assurance_lineage_v17 as v17  # noqa: E402
import scientific_assurance_lineage_v18 as v18  # noqa: E402
import scientific_assurance_lineage_v19 as sal  # noqa: E402
import semantic_bridge_execution_v1 as bridge_exec  # noqa: E402


def make_axiom(ast: dict, bindings: dict, *, status: str = "AUTHORITY_ADMISSIBLE") -> dict:
    axiom = {
        "schema": "AIFC/semantic-bridge-axiom/v1",
        "axiom_id": "TEST-AXIOM",
        "entailment_question_id": v17.QUESTION_ID,
        "logical_fragment": "FINITE_CLASSICAL_PROPOSITIONAL_V1",
        "normalized_formula_ast": ast,
        "atom_bindings": bindings,
        "axiom_authority_status": status,
    }
    axiom["axiom_content_hash"] = bridge_exec.bridge_axiom_content_hash(axiom)
    return axiom


class SemanticBridgeExecutionClosureV19Tests(unittest.TestCase):
    def _membership(self) -> dict[tuple[str, str], str]:
        return {
            (v17.PREDECESSOR_COMMIT, v17.PREDECESSOR_PATH): v17.PREDECESSOR_BLOB,
            (v17.TARGET_PROFILE_COMMIT, v17.TARGET_PROFILE_PATH): v17.TARGET_PROFILE_BLOB,
        }

    def test_production_api_remains_identity_only(self) -> None:
        params = set(inspect.signature(sal.audit_semantic_bridge_execution_closure).parameters)
        self.assertEqual(params, {"predecessor_identity", "target_profile_identity", "entailment_question_identity"})
        self.assertFalse({"premise", "target", "bridge", "axiom", "solver", "surface", "compiler", "raw_sha256"} & params)

    def test_production_path_has_no_direct_finite_solver_call(self) -> None:
        source = inspect.getsource(sal.audit_semantic_bridge_execution_closure)
        self.assertIn("bridge_exec.bridge_bound_entailment", source)
        self.assertNotIn("finite_propositional_entailment(", source)

    def test_bridge_theory_v2_is_empty_candidate_successor_of_v1(self) -> None:
        theory = sal._verify_bridge_theory_v2()
        self.assertEqual(theory["predecessor_bridge_theory_git_blob_sha1"], sal.BRIDGE_THEORY_V1_BLOB)
        self.assertEqual(theory["bridge_axiom_refs"], [])
        self.assertEqual(theory["bridge_status"], "ABSENT_NO_AUTHORITY_ADMISSIBLE_AXIOMS")
        self.assertEqual(theory["bridge_authority_status"], "NOT_ESTABLISHED")

    def test_execution_profile_binds_exact_composition_implementation(self) -> None:
        method = v18._verify_entailment_method_profile(v17._verify_question(), 18)
        profile = sal._verify_execution_profile(sal._verify_bridge_theory_v2(), method)
        self.assertEqual(profile["composition_rule"], "PREMISE_AND_ORDERED_BRIDGE_AXIOMS_V1")
        self.assertEqual(profile["execution_implementation_git_blob_sha1"], sal.EXECUTION_IMPL_BLOB)
        self.assertEqual(profile["execution_implementation_raw_sha256"], sal.EXECUTION_IMPL_RAW_SHA256)
        self.assertEqual(profile["execution_authority_status"], "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE")

    def test_bridge_axiom_unknown_operator_is_rejected(self) -> None:
        with self.assertRaisesRegex(bridge_exec.SemanticBridgeExecutionV1Error, "OPERATOR_INVALID"):
            bridge_exec.formula_atoms({"op": "IMPLIES", "args": []})

    def test_bridge_axiom_atom_namespace_must_cover_exact_ast_atoms(self) -> None:
        axiom = make_axiom(
            {"op": "OR", "args": [{"op": "ATOM", "id": "A"}, {"op": "ATOM", "id": "B"}]},
            {"A": {"semantic_role": "PREDECESSOR_ATOM", "semantic_identity": "X:A"}},
        )
        with self.assertRaisesRegex(bridge_exec.SemanticBridgeExecutionV1Error, "ATOM_NAMESPACE_BINDING_MISMATCH"):
            bridge_exec.verify_bridge_axiom_semantics(
                axiom, expected_question_id=v17.QUESTION_ID, require_authority=True
            )

    def test_nonempty_bridge_has_demonstrable_solver_effect(self) -> None:
        direct, bridged, count = bridge_exec.bridge_effect_test_vector()
        self.assertEqual(direct, "REFUTED_BY_COUNTERMODEL")
        self.assertEqual(bridged, "PROVED")
        self.assertEqual(count, 2)

    def test_bridge_bound_solver_receives_composed_premise(self) -> None:
        premise = {"op": "ATOM", "id": "A"}
        target = {"op": "ATOM", "id": "C"}
        ast = {
            "op": "OR",
            "args": [
                {"op": "NOT", "arg": {"op": "ATOM", "id": "A"}},
                {"op": "ATOM", "id": "C"},
            ],
        }
        axiom = make_axiom(
            ast,
            {
                "A": {"semantic_role": "PREDECESSOR_ATOM", "semantic_identity": "P:A"},
                "C": {"semantic_role": "TARGET_ATOM", "semantic_identity": "T:C"},
            },
        )
        fake = EntailmentResult("PROVED", None)
        with patch.object(bridge_exec, "finite_propositional_entailment", return_value=fake) as solver:
            result, composition = bridge_exec.bridge_bound_entailment(
                premise, [axiom], target, expected_question_id=v17.QUESTION_ID, max_atoms=16
            )
        self.assertEqual(result.state, "PROVED")
        called_premise = solver.call_args.args[0]
        self.assertEqual(called_premise, composition.composed_premise)
        self.assertEqual(called_premise["op"], "AND")
        self.assertEqual(called_premise["args"][1], ast)

    def test_bridge_aware_capacity_counts_bridge_only_atoms(self) -> None:
        premise = {"op": "ATOM", "id": "A"}
        target = {"op": "ATOM", "id": "C"}
        ast = {"op": "ATOM", "id": "BRIDGE_ONLY_D"}
        axiom = make_axiom(
            ast,
            {"BRIDGE_ONLY_D": {"semantic_role": "BRIDGE_DERIVED_ATOM", "semantic_identity": "B:D"}},
            status="SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
        )
        count = bridge_exec.bridge_aware_atom_count(
            premise, [axiom], target, expected_question_id=v17.QUESTION_ID
        )
        self.assertEqual(count, 3)

    def test_false_raw_sha256_dual_identity_promotion_is_rejected(self) -> None:
        fake = {"binding_status": "DUAL_IDENTITY_ESTABLISHED",
                "predecessor_raw_sha256": "0" * 64,
                "target_profile_raw_sha256": "1" * 64}
        with self.assertRaisesRegex(sal.ScientificAssuranceLineageV19Error, "RAW_SHA256_SELF_ASSERTION"):
            sal._enforce_dual_identity_claim(fake, "2" * 64, "3" * 64)

    def test_question_source_recomputation_requires_exact_historical_membership(self) -> None:
        with patch.object(v17, "git_tree_blob", return_value="0" * 40):
            with self.assertRaisesRegex(sal.ScientificAssuranceLineageV19Error, "HISTORICAL_MEMBERSHIP_REBINDING"):
                sal._historical_bound_bytes(v17.PREDECESSOR_COMMIT, v17.PREDECESSOR_PATH, v17.PREDECESSOR_BLOB)

    def test_current_binding_v2_recomputes_but_does_not_self_promote(self) -> None:
        with patch.object(v17, "git_tree_blob", side_effect=lambda commit, path: self._membership()[(commit, path)]):
            binding, pred_sha, target_sha = sal._verify_question_source_binding_v2(v17._verify_question())
        self.assertEqual(binding["binding_status"], "SUCCESSOR_CANDIDATE_RECOMPUTATION_REQUIRED_NOT_AUTHORITY_ADMISSIBLE")
        self.assertIsNone(binding["predecessor_raw_sha256"])
        self.assertIsNone(binding["target_profile_raw_sha256"])
        self.assertRegex(pred_sha, r"^[0-9a-f]{64}$")
        self.assertRegex(target_sha, r"^[0-9a-f]{64}$")

    def test_current_production_path_keeps_bridge_bound_solver_at_zero(self) -> None:
        with patch.object(v17, "git_tree_blob", side_effect=lambda commit, path: self._membership()[(commit, path)]), \
             patch.object(bridge_exec, "bridge_bound_entailment", side_effect=AssertionError("solver must not run")) as solver:
            report = sal.audit_semantic_bridge_execution_closure(
                v17.PREDECESSOR_ID, v17.TARGET_PROFILE_ID, v17.QUESTION_ID
            )
        self.assertEqual(report.result, "BLOCKED")
        self.assertEqual(report.blocked_subtype, "BLOCKED_UNAUTHORIZED_INTERPRETATION")
        self.assertEqual(report.current_bridge_axiom_count, 0)
        self.assertEqual(report.current_bridge_aware_atom_count, 18)
        self.assertEqual(report.bridge_aware_method_capacity, "BLOCKED_ATOM_LIMIT_18_GT_16")
        self.assertEqual(report.entailment_question_source_dual_identity, "NOT_ESTABLISHED")
        self.assertEqual(report.solver_invocation_count, 0)
        solver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
