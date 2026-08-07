import copy
import sys
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from schema_runtime import RuntimeSchemaError, validate_protocol_object  # noqa: E402


def registry():
    return {
        "schema": "AIFC/witness-registry/v1",
        "registry_id": "r0",
        "experiment_id": "exp-1",
        "registry_sequence": 0,
        "previous_registry_hash": "00" * 32,
        "transition_certificate_hash": None,
        "fault_model": {"n": 1, "f": 0, "q": 1, "independence_unit": "FAILURE_DOMAIN"},
        "witnesses": [{
            "witness_id": "w0",
            "failure_domain": "fd0",
            "status": "ACTIVE",
            "keys": [{
                "key_id": "k0",
                "algorithm": "Ed25519",
                "public_key_encoding": "hex",
                "public_key": "11" * 32,
                "valid_from_registry_sequence": 0,
                "valid_until_registry_sequence": None,
                "status": "ACTIVE",
                "predecessor_key_id": None,
                "revocation_reason": None,
            }],
        }],
    }


def strongest_receipt():
    return {
        "schema": "AIFC/witness-receipt/v1",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "logical_position": "CREATED",
        "content_schema": "AIFC/trial-ledger-event/v1",
        "content_hash": "22" * 32,
        "registry_hash": "33" * 32,
        "registry_sequence": 0,
        "witness_id": "w0",
        "key_id": "k0",
        "signature_algorithm": "Ed25519",
        "signature": "ab" * 64,
        "wall_clock_timestamp": None,
    }


class SignatureEncodingTests(unittest.TestCase):
    def test_lowercase_hex_32_byte_public_key_is_admitted(self):
        validate_protocol_object(registry(), "AIFC/witness-registry/v1")

    def test_base64_public_key_encoding_is_rejected(self):
        bad = registry()
        bad["witnesses"][0]["keys"][0]["public_key_encoding"] = "base64"
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(bad, "AIFC/witness-registry/v1")

    def test_mixed_case_public_key_is_rejected(self):
        bad = registry()
        bad["witnesses"][0]["keys"][0]["public_key"] = "AA" * 32
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(bad, "AIFC/witness-registry/v1")

    def test_lowercase_hex_64_byte_signature_is_admitted_for_strongest_profile(self):
        validate_protocol_object(strongest_receipt(), "AIFC/witness-receipt/v1")

    def test_uppercase_signature_is_rejected_for_strongest_profile(self):
        bad = strongest_receipt()
        bad["signature"] = "AB" * 64
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(bad, "AIFC/witness-receipt/v1")

    def test_wrong_length_signature_is_rejected_for_strongest_profile(self):
        bad = strongest_receipt()
        bad["signature"] = "ab" * 63
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(bad, "AIFC/witness-receipt/v1")

    def test_legacy_receipt_remains_readable_but_is_not_strongest_profile(self):
        legacy = strongest_receipt()
        legacy.pop("signature_profile_id")
        legacy.pop("content_schema")
        legacy.pop("registry_sequence")
        legacy.pop("wall_clock_timestamp")
        validate_protocol_object(legacy, "AIFC/witness-receipt/v1")
        self.assertNotIn("signature_profile_id", legacy)


if __name__ == "__main__":
    unittest.main()
