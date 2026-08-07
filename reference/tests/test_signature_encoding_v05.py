import sys
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from schema_runtime import RuntimeSchemaError, validate_protocol_object  # noqa: E402


def witness_receipt():
    return {
        "schema": "AIFC/witness-receipt/v1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "logical_position": "PRE_RETURN_FROZEN",
        "content_hash": "11" * 32,
        "registry_hash": "22" * 32,
        "witness_id": "w0",
        "key_id": "k0",
        "signature_algorithm": "Ed25519",
        "signature": "ab" * 64,
    }


def registry():
    return {
        "schema": "AIFC/witness-registry/v1",
        "registry_id": "r0",
        "experiment_id": "exp-1",
        "registry_sequence": 0,
        "previous_registry_hash": "33" * 32,
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
                "public_key": "01" * 32,
                "valid_from_registry_sequence": 0,
                "valid_until_registry_sequence": None,
                "status": "ACTIVE",
                "predecessor_key_id": None,
                "revocation_reason": None,
            }],
        }],
    }


class SignatureEncodingV05Tests(unittest.TestCase):
    def test_canonical_signature_and_public_key_encodings_are_schema_valid(self):
        validate_protocol_object(witness_receipt(), "AIFC/witness-receipt/v1")
        validate_protocol_object(registry(), "AIFC/witness-registry/v1")

    def test_signature_encoding_malleability_is_rejected(self):
        attacks = {
            "SIGNATURE_ENCODING_MALLEABILITY_UPPERCASE": "AB" * 64,
            "SIGNATURE_ENCODING_MALLEABILITY_BASE64_LIKE": "A" * 88,
            "SIGNATURE_ENCODING_MALLEABILITY_SHORT": "ab" * 63,
            "SIGNATURE_ENCODING_MALLEABILITY_LONG": "ab" * 65,
        }
        for attack, value in attacks.items():
            with self.subTest(attack=attack):
                obj = witness_receipt()
                obj["signature"] = value
                with self.assertRaises(RuntimeSchemaError):
                    validate_protocol_object(obj, "AIFC/witness-receipt/v1")

    def test_public_key_encoding_ambiguity_is_rejected(self):
        obj = registry()
        obj["witnesses"][0]["keys"][0]["public_key_encoding"] = "base64"
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(obj, "AIFC/witness-registry/v1")

        for attack, value in {
            "PUBLIC_KEY_ENCODING_AMBIGUITY_UPPERCASE": "AA" * 32,
            "PUBLIC_KEY_ENCODING_AMBIGUITY_SHORT": "01" * 31,
            "PUBLIC_KEY_ENCODING_AMBIGUITY_LONG": "01" * 33,
        }.items():
            with self.subTest(attack=attack):
                obj = registry()
                obj["witnesses"][0]["keys"][0]["public_key"] = value
                with self.assertRaises(RuntimeSchemaError):
                    validate_protocol_object(obj, "AIFC/witness-registry/v1")

    def test_algorithm_substitution_is_rejected_before_crypto(self):
        obj = witness_receipt()
        obj["signature_algorithm"] = "Ed25519ph"
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(obj, "AIFC/witness-receipt/v1")

        obj = registry()
        obj["witnesses"][0]["keys"][0]["algorithm"] = "Ed448"
        with self.assertRaises(RuntimeSchemaError):
            validate_protocol_object(obj, "AIFC/witness-registry/v1")


if __name__ == "__main__":
    unittest.main()
