import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
VERIFIER_DIR = TEST_DIR.parents[0] / "verifier"
sys.path.insert(0, str(TEST_DIR))
sys.path.insert(0, str(VERIFIER_DIR))

from test_replay import build_fixture  # noqa: E402
from admission import verify_replay_manifest  # noqa: E402


class ReplayForensicsV03Tests(unittest.TestCase):
    def test_honest_fixture_emits_forensic_result_on_unexpected_invalidation(self):
        with tempfile.TemporaryDirectory() as td:
            store, package, _ = build_fixture(Path(td))
            result = verify_replay_manifest(package, store.resolver())
            self.assertNotEqual(
                result.get("terminal_grade"),
                "INVALIDATED_EVIDENCE",
                msg=f"HONEST_REPLAY_FORENSIC_RESULT={result!r}",
            )


if __name__ == "__main__":
    unittest.main()
