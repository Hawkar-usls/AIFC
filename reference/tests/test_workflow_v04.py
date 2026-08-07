import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "verifier-self-audit-v03.yml"


class WorkflowV04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_platform_receipt_job_is_part_of_active_workflow(self):
        self.assertIn("\n  platform_receipt:\n", self.text)
        self.assertIn("python tools/build_ci_platform_receipt.py", self.text)
        self.assertIn("python tools/verify_ci_platform_receipt.py", self.text)
        self.assertIn("needs: verifier_self_audit", self.text)

    def test_hash_lock_install_uses_yaml_literal_blocks(self):
        command = (
            "python -m pip install --disable-pip-version-check "
            "--only-binary=:all: --require-hashes -r reference/verifier/requirements.lock.txt"
        )
        self.assertEqual(self.text.count(command), 2)
        self.assertNotRegex(
            self.text,
            re.compile(r"^\s*run:\s+python\s+-m\s+pip\s+install.*--only-binary=:all:", re.MULTILINE),
        )
        self.assertGreaterEqual(self.text.count("run: |\n"), 2)

    def test_verifier_actions_are_immutable_commit_refs(self):
        self.assertNotIn("@v", self.text)
        for expected in (
            "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
            "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
        ):
            self.assertIn(expected, self.text)


if __name__ == "__main__":
    unittest.main()
