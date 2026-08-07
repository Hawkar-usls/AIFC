import sys
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from aifc_verify_v04 import exit_code_for_result, load_exit_taxonomy  # noqa: E402


class CLIExitTaxonomyV04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = load_exit_taxonomy()

    def test_not_admitted_is_nonzero(self):
        self.assertEqual(exit_code_for_result({"terminal_grade": "NOT_ADMITTED"}, self.taxonomy), 3)

    def test_structural_match_only_is_nonzero(self):
        self.assertEqual(exit_code_for_result({"terminal_grade": "STRUCTURAL_MATCH_ONLY"}, self.taxonomy), 4)

    def test_invalidated_evidence_is_nonzero(self):
        self.assertEqual(exit_code_for_result({"terminal_grade": "INVALIDATED_EVIDENCE"}, self.taxonomy), 2)

    def test_protocol_outcome_grades_use_zero_without_implying_physical_claim(self):
        self.assertEqual(exit_code_for_result({"terminal_grade": "FORWARD_NULL_CONSISTENT_MISS"}, self.taxonomy), 0)
        self.assertEqual(exit_code_for_result({"terminal_grade": "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE"}, self.taxonomy), 0)
        self.assertIn("NOT_A_PHYSICAL_RETROCAUSALITY_CLAIM", self.taxonomy["zero_exit_semantics"])
        self.assertIn("MUST_PARSE_AND_VALIDATE_THE_VERIFIER_RESULT_JSON", self.taxonomy["external_automation_rule"])


if __name__ == "__main__":
    unittest.main()
