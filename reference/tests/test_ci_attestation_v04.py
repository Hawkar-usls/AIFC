import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "reference" / "verifier"
TOOLS = ROOT / "tools"
sys.path.insert(0, str(VERIFIER))
sys.path.insert(0, str(TOOLS))

from canonical import raw_evidence_hash  # noqa: E402
from verify_verifier_ci_attestation_v04 import (  # noqa: E402
    AttestationRejected,
    parse_test_count_bytes,
    require,
    verify_report,
)


def evidence_row(path: Path):
    raw = path.read_bytes()
    return {
        "path": path.name,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "aifc_raw_evidence_hash": raw_evidence_hash(raw),
    }


class CIAttestationV04Tests(unittest.TestCase):
    def test_ci_exit_code_rebinding_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output = root / "report.txt"
            exit_file = root / "report.exit"
            output.write_bytes(b"checker failed\n")
            exit_file.write_bytes(b"1\n")
            row = {
                "output": evidence_row(output),
                "exit_evidence": evidence_row(exit_file),
                "declared_exit_code": 0,
            }
            with self.assertRaises(AttestationRejected) as ctx:
                verify_report(row, root, "attack")
            self.assertIn("CI_EXIT_CODE_REBINDING:attack", str(ctx.exception))

    def test_ci_test_count_rebinding_is_rejected(self):
        report = (
            b"test_one ... ok\n"
            b"----------------------------------------------------------------------\n"
            b"Ran 46 tests in 0.500s\n\nOK\n"
        )
        declared = 47
        with self.assertRaises(AttestationRejected) as ctx:
            require(parse_test_count_bytes(report) == declared, "CI_TEST_COUNT_REBINDING")
        self.assertEqual(str(ctx.exception), "CI_TEST_COUNT_REBINDING")

    def test_unittest_summary_must_be_unique(self):
        report = b"Ran 1 test in 0.1s\nRan 2 tests in 0.2s\n"
        with self.assertRaises(AttestationRejected) as ctx:
            parse_test_count_bytes(report)
        self.assertIn("CI_UNITTEST_SUMMARY_AMBIGUOUS", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
