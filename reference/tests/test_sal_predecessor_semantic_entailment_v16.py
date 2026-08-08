#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

import scientific_assurance_lineage_v16 as sal  # noqa: E402


class PredecessorSemanticEntailmentV16Tests(unittest.TestCase):
    def test_proved_in_decidable_fragment(self) -> None:
        premise = {"op": "AND", "args": [{"op": "ATOM", "id": "A"}, {"op": "ATOM", "id": "B"}]}
        target = {"op": "ATOM", "id": "A"}
        result = sal.classify_entailment((), premise=premise, target=target)
        self.assertEqual(result.state, "PROVED")
        self.assertIsNone(result.countermodel)

    def test_refuted_by_machine_countermodel(self) -> None:
        premise = {"op": "ATOM", "id": "A"}
        target = {"op": "AND", "args": [{"op": "ATOM", "id": "A"}, {"op": "ATOM", "id": "B"}]}
        result = sal.classify_entailment((), premise=premise, target=target)
        self.assertEqual(result.state, "REFUTED_BY_COUNTERMODEL")
        self.assertEqual(result.countermodel, {"A": True, "B": False})

    def test_missing_anchor_blocks_instead_of_refuting(self) -> None:
        premise = {"op": "ATOM", "id": "A"}
        target = {"op": "NOT", "arg": {"op": "ATOM", "id": "A"}}
        result = sal.classify_entailment(("MISSING",), premise=premise, target=target)
        self.assertEqual(result.state, "BLOCKED_UNANCHORED_SEMANTICS")
        self.assertIsNone(result.countermodel)

    def test_anchored_formula_is_required(self) -> None:
        with self.assertRaisesRegex(sal.ScientificAssuranceLineageV16Error, "ANCHORED_ENTAILMENT_FORMULA_REQUIRED"):
            sal.classify_entailment(())

    def test_atom_limit_is_fail_closed(self) -> None:
        premise = {"op": "OR", "args": [{"op": "ATOM", "id": f"A{i}"} for i in range(17)]}
        target = {"op": "ATOM", "id": "A0"}
        with self.assertRaisesRegex(sal.ScientificAssuranceLineageV16Error, "ENTAILMENT_ATOM_LIMIT_EXCEEDED"):
            sal.finite_propositional_entailment(premise, target)

    def test_bootstrap_lemma_instance_has_source(self) -> None:
        status = sal.verify_no_normative_authority_ex_nihilo_instance(
            {"R0", "R1", "R2"}, {("R0", "R1"), ("R1", "R2")}
        )
        self.assertEqual(status, "SOURCE_NODE_EXISTS")

    def test_bootstrap_lemma_rejects_cycle(self) -> None:
        with self.assertRaisesRegex(sal.ScientificAssuranceLineageV16Error, "CYCLE_OR_NO_SOURCE|AUTHORITY_GRAPH_CYCLE"):
            sal.verify_no_normative_authority_ex_nihilo_instance(
                {"R0", "R1"}, {("R0", "R1"), ("R1", "R0")}
            )

    def test_current_predecessor_audit_stays_blocked_until_anchors_exist(self) -> None:
        membership = {
            (sal.BOOTSTRAP_COMMIT, sal.RELEASE_V08_PATH): sal.RELEASE_V08_BLOB,
            (sal.BOOTSTRAP_COMMIT, sal.ADMISSION_ORDER_PATH): sal.ADMISSION_ORDER_BLOB,
        }
        for commit in sal.DEPENDENCY_LOCK_TESTED_COMMITS:
            membership[(commit, sal.DEPENDENCY_LOCK_PATH)] = sal.DEPENDENCY_LOCK_BLOB

        with patch.object(sal, "git_tree_blob", side_effect=lambda commit, path: membership[(commit, path)]):
            report = sal.verify_predecessor_semantic_entailment_audit()

        self.assertEqual(report.direct_predecessor_transition_profile_authority, "ABSENT_CONFIRMED")
        self.assertTrue(report.predecessor_anti_self_authentication_constraints)
        self.assertEqual(report.predecessor_semantic_entailment, "BLOCKED_UNANCHORED_SEMANTICS")
        self.assertEqual(set(report.missing_semantic_anchor_ids), set(sal.REQUIRED_SEMANTIC_ANCHOR_IDS))
        self.assertEqual(report.bootstrap_authority_basis_status, "IMPLICIT_NOT_YET_FIRST_CLASS")
        self.assertTrue(report.dependency_lock_identity_same)
        self.assertEqual(report.historical_replay_environment_identity_general, "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
