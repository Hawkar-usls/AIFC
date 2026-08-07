import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AssuranceCheckerCliTests(unittest.TestCase):
    def run_checker(self, name):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools" / name)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=60,
        )

    def test_historical_repository_assurance_convergence_checker_passes(self):
        proc = self.run_checker("check_assurance_convergence.py")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout)
        self.assertIn("RELEASE_GATE_MONOTONICITY = PASS", proc.stdout)
        self.assertIn("SCHEMA_IDENTIFIER_IMMUTABILITY = PASS_FOR_REGISTERED_ISSUED_GRAPH", proc.stdout)
        self.assertIn("CURRENT_V06_PREDECESSOR_COMPOSITION_GUARD = PASS", proc.stdout)
        self.assertIn("AIFC_V1_FROZEN = FALSE", proc.stdout)

    def test_repository_assurance_convergence_v11_checker_passes(self):
        proc = self.run_checker("check_assurance_convergence_v11.py")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout)
        self.assertIn("ADMISSION_AUTHORITY_PARTIAL_ORDER_VALID = PASS", proc.stdout)
        self.assertIn("VALIDATOR_SEMANTICS_CONTENT_BINDING = PASS", proc.stdout)
        self.assertIn("SCHEMA_IDENTIFIER_IMMUTABILITY = PASS_DUAL_HASH", proc.stdout)
        self.assertIn("INHERITED_GATE_SET_DERIVATION = IMPLEMENTED", proc.stdout)
        self.assertIn("GATE_LINEAGE_EVIDENCE_RESOLUTION = IMPLEMENTED_CANDIDATE", proc.stdout)
        self.assertIn("CLEAN_V0_7_VERSIONED_ENVELOPE = REQUIRED_NOT_IMPLEMENTED", proc.stdout)
        self.assertIn("AIFC_V1_FROZEN = FALSE", proc.stdout)


if __name__ == "__main__":
    unittest.main()
