import copy
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_DIR = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import load_json_strict  # noqa: E402
from schema_runtime import RuntimeSchemaError, validate_protocol_object  # noqa: E402


class SalConformanceV12Tests(unittest.TestCase):
    def test_repository_sal_conformance_checker_passes(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_sal_conformance_v12.py")],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout)
        self.assertIn("SAL_SCHEMA_HEADERS = PASS (5/5)", proc.stdout)
        self.assertIn("SAL_RUNTIME_SCHEMA_ADMISSION = PASS", proc.stdout)
        self.assertIn("SAL_RELEASE_GATE_65_TO_73 = PASS", proc.stdout)
        self.assertIn("SAL_NORMATIVE_RESOLUTION = PASS", proc.stdout)
        self.assertIn("SCIENTIFIC_ASSURANCE_LINEAGE_V1_2_CONFORMANCE = PASS", proc.stdout)

    def test_assurance_hash_profile_manifest_is_runtime_schema_closed(self):
        manifest = load_json_strict(
            ROOT / "conformance" / "AIFC-ASSURANCE-HASH-PROFILE-MANIFEST-v1.json"
        )
        validate_protocol_object(manifest, "AIFC/assurance-hash-profile-manifest/v1")
        tampered = copy.deepcopy(manifest)
        tampered["unexpected_claim"] = "PASS"
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(tampered, "AIFC/assurance-hash-profile-manifest/v1")

    def test_inherited_hash_profile_is_runtime_schema_closed(self):
        profile = load_json_strict(
            ROOT / "conformance" / "AIFC-INHERITED-GATE-HASH-PROFILE-v1.json"
        )
        validate_protocol_object(profile, "AIFC/inherited-gate-hash-profile/v1")
        tampered = copy.deepcopy(profile)
        tampered["historical_extension_policy"] = "ALLOW_SILENT_EXTENSION"
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(tampered, "AIFC/inherited-gate-hash-profile/v1")


if __name__ == "__main__":
    unittest.main()
