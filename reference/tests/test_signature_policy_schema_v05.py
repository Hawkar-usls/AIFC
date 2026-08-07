import copy
import sys
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from schema_runtime import RuntimeSchemaError, validate_protocol_object  # noqa: E402
from signature_preimage_v05 import normative_policy  # noqa: E402


class SignaturePolicySchemaV05Tests(unittest.TestCase):
    def test_normative_policy_is_discovered_and_validated_by_runtime_catalog(self):
        validate_protocol_object(normative_policy("exp-1"), "AIFC/signature-preimage-policy/v1")

    def test_claimant_defined_ed25519ph_variant_is_schema_rejected(self):
        bad = copy.deepcopy(normative_policy("exp-1"))
        bad["ed25519_variant"] = "Ed25519ph"
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(bad, "AIFC/signature-preimage-policy/v1")

    def test_claimant_defined_receipt_family_is_schema_rejected(self):
        bad = copy.deepcopy(normative_policy("exp-1"))
        bad["supported_receipt_schemas"].append("AIFC/future-receipt/v1")
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(bad, "AIFC/signature-preimage-policy/v1")


if __name__ == "__main__":
    unittest.main()
