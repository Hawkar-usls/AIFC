#!/usr/bin/env python3
from __future__ import annotations

import copy
import inspect
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference/verifier"))

from canonical import domain_hash
import semantic_lineage_edge_binding_v1 as old_edge
import semantic_lineage_edge_universe_v1 as universe
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v111 as v111
import scientific_assurance_lineage_v111h as v111h
import scientific_assurance_lineage_v111u as sal

class T(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def data(self):
        objects, raws = v111h._objects_and_raws()
        return (
            objects,
            raws,
            self.load(v111h.BINDING_PATH),
            self.load(v111h.AUDIT_PATH),
            self.load(sal.UNIVERSE_PATH),
        )

    def verify(self, receipt=None, binding=None, audit=None):
        objects, raws, b, a, u = self.data()
        return universe.verify_universe_receipt(
            u if receipt is None else receipt,
            b if binding is None else binding,
            a if audit is None else audit,
            objects,
            raws,
        )

    def test_current_universe_is_machine_derived(self):
        vertices, edges, graph_id = self.verify()
        self.assertEqual(len(vertices), 6)
        self.assertEqual(len(edges), 15)
        self.assertEqual(graph_id, sal.LINEAGE_GRAPH_IDENTITY_V2)
        self.assertEqual(
            tuple(edge["edge_id"] for edge in edges),
            tuple(sorted(edge["edge_id"] for edge in edges)),
        )

    def test_production_derivation_has_no_required_edge_list(self):
        self.assertFalse(hasattr(universe, "EDGE_SPECS"))
        self.assertFalse(hasattr(universe, "REQUIRED_EDGE_IDS"))
        source = inspect.getsource(universe.derive_edge_universe)
        self.assertNotIn("required_edge", source.lower())
        self.assertNotIn("edge_specs", source.lower())

    def test_six_additional_pairs_are_discovered_not_declared(self):
        _, edges, _ = self.verify()
        ids = {edge["edge_id"] for edge in edges}
        self.assertEqual(
            ids
            - {
                "PROOF_TO_PROFILE",
                "PROOF_TO_MANIFEST",
                "PROOF_TO_GRAPH",
                "MANIFEST_TO_PROFILE",
                "GRAPH_TO_QUESTION",
                "DERIVED_TO_PROFILE",
                "DERIVED_TO_PROOF",
                "DERIVED_TO_MANIFEST",
                "DERIVED_TO_GRAPH",
            },
            {
                "PROFILE_TO_QUESTION",
                "PROOF_TO_QUESTION",
                "MANIFEST_TO_QUESTION",
                "DERIVED_TO_QUESTION",
                "GRAPH_TO_DERIVED",
                "PROOF_TO_DERIVED",
            },
        )
        proof_to_derived = next(
            edge for edge in edges if edge["edge_id"] == "PROOF_TO_DERIVED"
        )
        self.assertEqual(
            proof_to_derived["evidence_occurrences"][0]["source_json_pointer"],
            "/raw_derivation_ast/conclusion/semantic_identity",
        )

    def test_proof_question_relation_preserves_multiple_occurrences(self):
        _, edges, _ = self.verify()
        proof_to_question = next(
            edge for edge in edges if edge["edge_id"] == "PROOF_TO_QUESTION"
        )
        self.assertEqual(
            [x["source_json_pointer"] for x in proof_to_question["evidence_occurrences"]],
            [
                "/entailment_question_id",
                "/raw_derivation_ast/conclusion/entailment_question_id",
            ],
        )

    def test_required_edge_universe_omission_and_injection_are_rejected(self):
        _, _, _, _, current = self.data()
        for kind in ("omit", "inject"):
            mutated = copy.deepcopy(current)
            if kind == "omit":
                mutated["derived_edge_pairs"] = [
                    edge_id
                    for edge_id in mutated["derived_edge_pairs"]
                    if edge_id != "PROFILE_TO_QUESTION"
                ]
            else:
                mutated["derived_edge_pairs"].append("QUESTION_TO_PROFILE")
            mutated["universe_content_hash"] = universe.universe_content_hash(mutated)
            with self.subTest(kind=kind), self.assertRaisesRegex(
                universe.SemanticLineageEdgeUniverseV1Error,
                "LINEAGE_REQUIRED_EDGE_UNIVERSE_OMISSION_OR_INJECTION",
            ):
                self.verify(receipt=mutated)

    def test_source_binding_question_context_rebinding_is_rejected(self):
        _, _, binding, _, _ = self.data()
        mutated = copy.deepcopy(binding)
        mutated["entailment_question_id"] = "0" * 64
        mutated["binding_content_hash"] = old_edge.binding_content_hash(mutated)
        with self.assertRaisesRegex(
            universe.SemanticLineageEdgeUniverseV1Error,
            "LINEAGE_BINDING_QUESTION_CONTEXT_REBINDING",
        ):
            self.verify(binding=mutated)

    def test_source_audit_question_context_rebinding_is_rejected(self):
        _, _, _, audit, _ = self.data()
        mutated = copy.deepcopy(audit)
        mutated["entailment_question_id"] = "0" * 64
        with self.assertRaisesRegex(
            universe.SemanticLineageEdgeUniverseV1Error,
            "LINEAGE_AUDIT_QUESTION_CONTEXT_REBINDING",
        ):
            self.verify(audit=mutated)

    def test_universe_receipt_question_context_rebinding_is_rejected(self):
        _, _, _, _, receipt = self.data()
        mutated = copy.deepcopy(receipt)
        mutated["entailment_question_id"] = "0" * 64
        mutated["universe_content_hash"] = universe.universe_content_hash(mutated)
        with self.assertRaisesRegex(
            universe.SemanticLineageEdgeUniverseV1Error,
            "LINEAGE_UNIVERSE_QUESTION_CONTEXT_REBINDING",
        ):
            self.verify(receipt=mutated)

    def test_new_audit_question_context_is_explicitly_checked(self):
        audit = self.load(sal.AUDIT_PATH)
        receipt = self.load(sal.UNIVERSE_PATH)
        mutated = copy.deepcopy(audit)
        mutated["entailment_question_id"] = "0" * 64
        material = dict(mutated)
        material.pop("audit_content_hash", None)
        new_hash = domain_hash(
            "AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-AUDIT:v1",
            material,
        )
        mutated["audit_content_hash"] = new_hash
        with patch.object(sal, "AUDIT_HASH", new_hash):
            with self.assertRaisesRegex(
                sal.ScientificAssuranceLineageV111UError,
                "LINEAGE_UNIVERSE_AUDIT_QUESTION_CONTEXT_REBINDING",
            ):
                sal._verify_audit_object(mutated, receipt, v17.QUESTION_ID)

    def test_vertex_and_semantic_relation_universe_are_not_overclaimed(self):
        objects, _, _, _, _ = self.data()
        _, raws, binding, _, _ = self.data()
        vertices, _, _ = old_edge.verify_binding_receipt(binding, objects, raws)
        vertex_ids = {v["object_id"] for v in vertices}
        self.assertNotIn(objects["PROFILE"]["resolver_profile_id"], vertex_ids)
        inherited = SimpleNamespace(
            solver_invocation_count=0,
            derived_semantic_authority="BLOCKED",
            edge_identity="ESTABLISHED_IN_TESTED_SCOPE",
            result="BLOCKED",
            blocked_subtype="BLOCKED_UNAUTHORIZED_INTERPRETATION",
        )
        with patch.object(
            sal.v111h,
            "audit_derived_semantic_lineage_edge_binding",
            return_value=inherited,
        ):
            report = sal.audit_derived_semantic_lineage_edge_universe(
                v17.PREDECESSOR_ID,
                v17.TARGET_PROFILE_ID,
                v17.QUESTION_ID,
            )
        self.assertEqual(report.vertex_universe_completeness, "NOT_ESTABLISHED")
        self.assertEqual(
            report.semantic_relation_universe_completeness,
            "NOT_ESTABLISHED",
        )
        self.assertEqual(report.derived_semantic_authority, "BLOCKED")
        self.assertEqual(report.solver_invocation_count, 0)

if __name__ == "__main__":
    unittest.main()
