from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "verifier"))

import aifc_internal_terminal_handoff_v1 as handoff


class AIFCInternalTerminalHandoffV1Tests(unittest.TestCase):
    def test_handoff_replays_pinned_boundary(self):
        result = handoff.verify()
        self.assertEqual(
            result["AIFC_INTERNAL_ASSURANCE_LINEAGE_TERMINAL"],
            "ESTABLISHED_IN_CURRENT_TESTED_SCOPE",
        )
        self.assertEqual(
            result["AIFC_ARTICLE_PUBLICATION_READINESS"],
            "READY_WITH_EXPLICIT_DRAFT_AND_CLAIM_CEILING",
        )
        self.assertFalse(result["AIFC_V1_FROZEN"])
        self.assertEqual(result["IMPLEMENTATION_B"], "NOT_ESTABLISHED")
        self.assertEqual(result["EXTERNAL_PUBLIC_RANDOMNESS_BENCH"], "NOT_ESTABLISHED")
        self.assertEqual(result["EXTERNAL_BOOTSTRAP_RATIFICATION"], "NOT_PERFORMED")
        self.assertEqual(result["BOOTSTRAP_AUTHORITY_LEGITIMACY"], "NOT_ESTABLISHED")
        self.assertEqual(result["GLOBAL_NOVELTY"], "NOT_ESTABLISHED")
        self.assertEqual(result["PHYSICAL_RETROCAUSALITY"], "NOT_OBSERVED")
        self.assertEqual(result["SOLVER_INVOCATION_COUNT"], 0)

    def test_release_gate_stays_fail_closed(self):
        result = handoff.verify()
        self.assertEqual(
            result["CURRENT_INTERNAL_PATH_TO_BOOTSTRAP_LEGITIMACY"], "ABSENT"
        )
        self.assertEqual(
            result["NEXT_PHASE"], "PUBLIC_COMMUNICATION_AND_EXTERNAL_FALSIFICATION"
        )


if __name__ == "__main__":
    unittest.main()
