import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from assurance_monotonicity import compare_release_gate_sets  # noqa: E402
from gate_lineage_verifier import (  # noqa: E402
    GateLineageVerificationError,
    verify_gate_lineage_transition,
)
from test_protocol_semantics_v03 import Store  # noqa: E402


def gate_doc(*gate_ids):
    return {
        "schema": "AIFC/conformance-release-gate/v1",
        "profile": "test",
        "status": "DRAFT_NOT_SATISFIED",
        "required_checks": [{"id": gate_id, "required": True} for gate_id in gate_ids],
    }


def atom(name):
    return {"op": "ATOM", "id": name}


def gate_definition(gate_id, expr):
    return {
        "schema": "AIFC/gate-definition/v1",
        "gate_id": gate_id,
        "definition_version": "test-v1",
        "pass_condition": expr,
        "description": "test-only machine gate definition",
    }


class GateLineageVerifierTests(unittest.TestCase):
    def build_transition(self, store, predecessor_expr, successor_defs):
        previous_hash = store.protocol(gate_definition("OLD_GATE", predecessor_expr))
        successor_ids = []
        successor_hashes = []
        for gate_id, expr in successor_defs:
            successor_ids.append(gate_id)
            successor_hashes.append(store.protocol(gate_definition(gate_id, expr)))
        evidence_hash = store.protocol({
            "schema": "AIFC/gate-strengthening-evidence/v1",
            "proof_method": "BOOLEAN_TRUTH_TABLE_IMPLICATION_V1",
            "removed_gate_id": "OLD_GATE",
            "previous_gate_definition_hash": previous_hash,
            "successor_gate_ids": successor_ids,
            "successor_definition_hashes": successor_hashes,
            "claim": "SUCCESSOR_CONJUNCTION_IMPLIES_PREDECESSOR",
            "maximum_truth_table_atoms": 16,
        })
        transition_hash = store.protocol({
            "schema": "AIFC/gate-lineage-transition/v1",
            "removed_gate_id": "OLD_GATE",
            "successor_gate_ids": successor_ids,
            "previous_gate_definition_hash": previous_hash,
            "successor_definition_hashes": successor_hashes,
            "equivalence_or_strengthening_evidence_hash": evidence_hash,
            "migration_reason": "test-only strengthening",
            "approved_protocol_version": "test-v2",
        })
        return transition_hash

    def test_resolver_backed_truth_table_proof_confirms_strict_split(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            transition_hash = self.build_transition(
                store,
                {"op": "AND", "args": [atom("A"), atom("B")]},
                [("NEW_GATE_A", atom("A")), ("NEW_GATE_B", atom("B"))],
            )
            verified = verify_gate_lineage_transition(
                transition_hash,
                {"NEW_GATE_A", "NEW_GATE_B"},
                store.resolver(),
            )
            self.assertEqual(verified["verification_status"], "STRENGTHENING_CONFIRMED")
            self.assertEqual(verified["atom_count"], 2)
            self.assertEqual(verified["assignments_checked"], 4)
            comparison = compare_release_gate_sets(
                gate_doc("OLD_GATE"),
                gate_doc("NEW_GATE_A", "NEW_GATE_B"),
                [verified],
            )
            self.assertEqual(comparison.status, "PASS", comparison.failure_codes)

    def test_fake_gate_strengthening_receipt_hash_is_rejected_by_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            previous_hash = store.protocol(gate_definition("OLD_GATE", atom("A")))
            successor_hash = store.protocol(gate_definition("NEW_GATE", atom("A")))
            transition_hash = store.protocol({
                "schema": "AIFC/gate-lineage-transition/v1",
                "removed_gate_id": "OLD_GATE",
                "successor_gate_ids": ["NEW_GATE"],
                "previous_gate_definition_hash": previous_hash,
                "successor_definition_hashes": [successor_hash],
                "equivalence_or_strengthening_evidence_hash": "33" * 32,
                "migration_reason": "fake evidence pointer",
                "approved_protocol_version": "test-v2",
            })
            with self.assertRaises(GateLineageVerificationError) as ctx:
                verify_gate_lineage_transition(transition_hash, {"NEW_GATE"}, store.resolver())
            self.assertIn("GATE_LINEAGE_EVIDENCE_RESOLUTION_FAILED", str(ctx.exception))

    def test_false_strengthening_claim_yields_truth_table_counterexample(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            transition_hash = self.build_transition(
                store,
                atom("A"),
                [("NEW_GATE", atom("B"))],
            )
            with self.assertRaises(GateLineageVerificationError) as ctx:
                verify_gate_lineage_transition(transition_hash, {"NEW_GATE"}, store.resolver())
            self.assertIn("GATE_STRENGTHENING_COUNTEREXAMPLE:OLD_GATE", str(ctx.exception))

    def test_successor_definition_gate_id_rebinding_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            previous_hash = store.protocol(gate_definition("OLD_GATE", atom("A")))
            wrong_hash = store.protocol(gate_definition("DIFFERENT_GATE", atom("A")))
            evidence_hash = store.protocol({
                "schema": "AIFC/gate-strengthening-evidence/v1",
                "proof_method": "BOOLEAN_TRUTH_TABLE_IMPLICATION_V1",
                "removed_gate_id": "OLD_GATE",
                "previous_gate_definition_hash": previous_hash,
                "successor_gate_ids": ["NEW_GATE"],
                "successor_definition_hashes": [wrong_hash],
                "claim": "SUCCESSOR_CONJUNCTION_IMPLIES_PREDECESSOR",
                "maximum_truth_table_atoms": 16,
            })
            transition_hash = store.protocol({
                "schema": "AIFC/gate-lineage-transition/v1",
                "removed_gate_id": "OLD_GATE",
                "successor_gate_ids": ["NEW_GATE"],
                "previous_gate_definition_hash": previous_hash,
                "successor_definition_hashes": [wrong_hash],
                "equivalence_or_strengthening_evidence_hash": evidence_hash,
                "migration_reason": "definition rebinding attack",
                "approved_protocol_version": "test-v2",
            })
            with self.assertRaises(GateLineageVerificationError) as ctx:
                verify_gate_lineage_transition(transition_hash, {"NEW_GATE"}, store.resolver())
            self.assertIn("GATE_LINEAGE_SUCCESSOR_DEFINITION_REBINDING", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
