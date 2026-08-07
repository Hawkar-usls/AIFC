import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AssuranceCheckerCliTests(unittest.TestCase):
    def test_repository_assurance_convergence_checker_passes(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_assurance_convergence.py")],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout)
        self.assertIn("RELEASE_GATE_MONOTONICITY = PASS", proc.stdout)
        self.assertIn("SCHEMA_IDENTIFIER_IMMUTABILITY = PASS_FOR_REGISTERED_ISSUED_GRAPH", proc.stdout)
        self.assertIn("CURRENT_V06_PREDECESSOR_COMPOSITION_GUARD = PASS", proc.stdout)
        self.assertIn("AIFC_V1_FROZEN = FALSE", proc.stdout)


if __name__ == "__main__":
    unittest.main()
