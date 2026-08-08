#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "verifier"))

import scientific_assurance_lineage_v110 as sal  # noqa: E402


class SemanticEndpointReferenceBindingV110Tests(unittest.TestCase):
    def _axiom(self) -> dict:
        return {
            "schema": "AIFC/semantic-bridge-axiom/v2",
            "axiom_id": "AXIOM-A",
            "axiom_content_hash": "a" * 64,
        }

    def test_theory_axiom_id_reference_rebinding_is_rejected(self) -> None:
        ref = {
            "axiom_schema_id": "AIFC/semantic-bridge-axiom/v2",
            "axiom_id": "AXIOM-B",
            "axiom_content_hash": "a" * 64,
        }
        with self.assertRaisesRegex(
            sal.ScientificAssuranceLineageV110Error,
            "BRIDGE_THEORY_AXIOM_REFERENCE_REBINDING:ID",
        ):
            sal._verify_axiom_reference_binding(ref, self._axiom())

    def test_theory_axiom_content_hash_reference_rebinding_is_rejected(self) -> None:
        ref = {
            "axiom_schema_id": "AIFC/semantic-bridge-axiom/v2",
            "axiom_id": "AXIOM-A",
            "axiom_content_hash": "b" * 64,
        }
        with self.assertRaisesRegex(
            sal.ScientificAssuranceLineageV110Error,
            "BRIDGE_THEORY_AXIOM_REFERENCE_REBINDING:CONTENT_HASH",
        ):
            sal._verify_axiom_reference_binding(ref, self._axiom())


if __name__ == "__main__":
    unittest.main()
