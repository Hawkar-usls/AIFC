import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from ed25519_admission import Ed25519AdmissionError, replay_ed25519_signatures  # noqa: E402
from signature_policy_admission import SignaturePreimageMaterial, SignaturePreimageReplaySummary  # noqa: E402
from signature_preimage import compile_signature_preimage  # noqa: E402


RFC8032_SEED = bytes.fromhex(
    "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb"
)
RFC8032_PUBLIC = "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"
PKCS8_ED25519_SEED_PREFIX = bytes.fromhex("302e020100300506032b657004220420")


def openssl_sign(message: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="aifc-ed25519-test-sign-") as td:
        root = Path(td)
        private_path = root / "private.der"
        message_path = root / "message.bin"
        signature_path = root / "signature.bin"
        private_path.write_bytes(PKCS8_ED25519_SEED_PREFIX + RFC8032_SEED)
        message_path.write_bytes(message)
        proc = subprocess.run(
            [
                "openssl", "pkeyutl", "-sign",
                "-inkey", str(private_path), "-keyform", "DER",
                "-rawin", "-in", str(message_path), "-out", str(signature_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
        return signature_path.read_bytes()


def registry(key_status="ACTIVE", witness_status="ACTIVE", valid_until=None):
    return {
        "schema": "AIFC/witness-registry/v1",
        "registry_id": "r3",
        "experiment_id": "exp-1",
        "registry_sequence": 3,
        "previous_registry_hash": "11" * 32,
        "transition_certificate_hash": "22" * 32,
        "fault_model": {"n": 1, "f": 0, "q": 1, "independence_unit": "FAILURE_DOMAIN"},
        "witnesses": [{
            "witness_id": "w0",
            "failure_domain": "fd0",
            "status": witness_status,
            "keys": [{
                "key_id": "k0",
                "algorithm": "Ed25519",
                "public_key_encoding": "hex",
                "public_key": RFC8032_PUBLIC,
                "valid_from_registry_sequence": 0,
                "valid_until_registry_sequence": valid_until,
                "status": key_status,
                "predecessor_key_id": None,
                "revocation_reason": None,
            }],
        }],
    }


class FakeResolver:
    def __init__(self, registry_obj):
        self.registry_obj = registry_obj

    def resolve(self, content_hash, expected_schema=None):
        if expected_schema != "AIFC/witness-registry/v1":
            raise ValueError(f"unexpected schema {expected_schema}")
        return SimpleNamespace(parsed_json=self.registry_obj)


def signature_policy():
    return {
        "schema": "AIFC/signature-preimage-policy/v1",
        "policy_id": "AIFC-ED25519-SIGNATURE-PREIMAGE-POLICY-V1",
        "experiment_id": "exp-1",
        "protocol_version": "1.0-draft",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "signature_algorithm": "Ed25519",
        "domain_separator": "AIFC:SIGNATURE_PREIMAGE:v1",
        "framing": "TAG_U8_LENGTH_U64BE_V1",
        "prehash_mode": "NONE_DIRECT_ED25519",
        "public_key_encoding": "LOWERCASE_HEX_32_BYTES",
        "signature_encoding": "LOWERCASE_HEX_64_BYTES",
        "timestamp_semantics": "SIGNED_IF_PRESENT_INTEGRITY_ONLY_NOT_FRESHNESS",
        "field_tags": {
            "receipt_schema": 1,
            "protocol_version": 2,
            "signature_profile_id": 3,
            "scope_kind": 4,
            "experiment_id": 5,
            "trial_index_or_absent": 6,
            "logical_position_or_transition_role": 7,
            "content_schema": 8,
            "content_hash": 9,
            "registry_hash": 10,
            "registry_sequence": 11,
            "witness_id": 12,
            "key_id": 13,
            "timestamp_present": 14,
            "timestamp_utf8": 15,
        },
        "receipt_profiles": {
            "trial_witness": {
                "receipt_schema": "AIFC/witness-receipt/v1",
                "scope_kind": "TRIAL",
                "position_source": "logical_position",
                "content_hash_source": "content_hash",
                "registry_hash_source": "registry_hash",
            },
            "experiment_plan": {
                "receipt_schema": "AIFC/experiment-plan-receipt/v1",
                "scope_kind": "EXPERIMENT",
                "position_source": "logical_position",
                "content_hash_source": "content_hash",
                "registry_hash_source": "registry_hash",
            },
            "registry_transition": {
                "receipt_schema": "AIFC/registry-transition-receipt/v1",
                "scope_kind": "EXPERIMENT",
                "position_source": "role",
                "content_hash_source": "transition_body_hash",
                "registry_hash_source": "signing_registry_hash",
            },
        },
        "frozen_before_first_created": True,
    }


def signed_summary(registry_hash="33" * 32, message=b"AIFC-v0.6-crypto-integration-message"):
    sig = openssl_sign(message)
    receipt = {
        "schema": "AIFC/witness-receipt/v1",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "logical_position": "CREATED",
        "content_schema": "AIFC/trial-ledger-event/v1",
        "content_hash": "44" * 32,
        "registry_hash": registry_hash,
        "registry_sequence": 3,
        "witness_id": "w0",
        "key_id": "k0",
        "signature_algorithm": "Ed25519",
        "signature": sig.hex(),
        "wall_clock_timestamp": None,
    }
    material = SignaturePreimageMaterial(
        receipt_schema=receipt["schema"],
        receipt=receipt,
        preimage=message,
        registry_hash=registry_hash,
        registry_sequence=3,
        witness_id="w0",
        key_id="k0",
    )
    return SignaturePreimageReplaySummary(
        receipt_count=1,
        preimage_sha256s=(hashlib.sha256(message).hexdigest(),),
        materials=(material,),
    )


def typed_preimage_signed_summary(registry_hash="22" * 32):
    receipt = {
        "schema": "AIFC/witness-receipt/v1",
        "signature_profile_id": "AIFC-ED25519-DIRECT-TYPED-V1",
        "experiment_id": "exp-1",
        "trial_index": 7,
        "logical_position": "PRE_RETURN_FROZEN",
        "content_schema": "AIFC/trial-ledger-event/v1",
        "content_hash": "11" * 32,
        "registry_hash": registry_hash,
        "registry_sequence": 3,
        "witness_id": "w0",
        "key_id": "k0",
        "signature_algorithm": "Ed25519",
        "signature": "00" * 64,
        "wall_clock_timestamp": "2026-08-07T12:34:56Z",
    }
    preimage = compile_signature_preimage(receipt, signature_policy())
    receipt["signature"] = openssl_sign(preimage).hex()
    material = SignaturePreimageMaterial(
        receipt_schema=receipt["schema"],
        receipt=receipt,
        preimage=preimage,
        registry_hash=registry_hash,
        registry_sequence=3,
        witness_id="w0",
        key_id="k0",
    )
    return SignaturePreimageReplaySummary(
        receipt_count=1,
        preimage_sha256s=(hashlib.sha256(preimage).hexdigest(),),
        materials=(material,),
    )


class Ed25519AdmissionTests(unittest.TestCase):
    def test_registry_local_signature_verifies(self):
        summary = replay_ed25519_signatures(signed_summary(), FakeResolver(registry()))
        self.assertEqual(summary.receipt_count, 1)
        self.assertEqual(summary.verified_count, 1)
        self.assertTrue(summary.backend_version.startswith("OpenSSL "))
        self.assertEqual(len(summary.backend_executable_sha256), 64)

    def test_normative_aifc_typed_preimage_is_signed_and_verified(self):
        candidate = typed_preimage_signed_summary()
        self.assertEqual(len(candidate.materials[0].preimage), 381)
        self.assertEqual(
            candidate.preimage_sha256s[0],
            "2c2ad0fd73ebac49a048038941fc4cae0b616cb8ef8a7b174acc63c7c63b1297",
        )
        summary = replay_ed25519_signatures(candidate, FakeResolver(registry()))
        self.assertEqual(summary.verified_count, 1)

    def test_signature_bit_flip_is_rejected(self):
        summary = signed_summary()
        material = summary.materials[0]
        bad_receipt = dict(material.receipt)
        sig = bytearray(bytes.fromhex(bad_receipt["signature"]))
        sig[0] ^= 1
        bad_receipt["signature"] = bytes(sig).hex()
        bad_material = SignaturePreimageMaterial(
            receipt_schema=material.receipt_schema,
            receipt=bad_receipt,
            preimage=material.preimage,
            registry_hash=material.registry_hash,
            registry_sequence=material.registry_sequence,
            witness_id=material.witness_id,
            key_id=material.key_id,
        )
        bad_summary = SignaturePreimageReplaySummary(1, summary.preimage_sha256s, (bad_material,))
        with self.assertRaises(Ed25519AdmissionError) as ctx:
            replay_ed25519_signatures(bad_summary, FakeResolver(registry()))
        self.assertIn("ED25519_SIGNATURE_INVALID", str(ctx.exception))

    def test_message_tamper_is_rejected(self):
        summary = signed_summary()
        material = summary.materials[0]
        bad_material = SignaturePreimageMaterial(
            receipt_schema=material.receipt_schema,
            receipt=material.receipt,
            preimage=material.preimage + b"!",
            registry_hash=material.registry_hash,
            registry_sequence=material.registry_sequence,
            witness_id=material.witness_id,
            key_id=material.key_id,
        )
        bad_summary = SignaturePreimageReplaySummary(1, summary.preimage_sha256s, (bad_material,))
        with self.assertRaises(Ed25519AdmissionError) as ctx:
            replay_ed25519_signatures(bad_summary, FakeResolver(registry()))
        self.assertIn("ED25519_SIGNATURE_INVALID", str(ctx.exception))

    def test_key_id_substitution_is_rejected(self):
        summary = signed_summary()
        material = summary.materials[0]
        bad_material = SignaturePreimageMaterial(
            receipt_schema=material.receipt_schema,
            receipt=material.receipt,
            preimage=material.preimage,
            registry_hash=material.registry_hash,
            registry_sequence=material.registry_sequence,
            witness_id=material.witness_id,
            key_id="other-key",
        )
        bad_summary = SignaturePreimageReplaySummary(1, summary.preimage_sha256s, (bad_material,))
        with self.assertRaises(Ed25519AdmissionError) as ctx:
            replay_ed25519_signatures(bad_summary, FakeResolver(registry()))
        self.assertIn("KEY_ID_NOT_UNIQUE_FOR_WITNESS", str(ctx.exception))

    def test_registry_local_revoked_key_is_rejected(self):
        with self.assertRaises(Ed25519AdmissionError) as ctx:
            replay_ed25519_signatures(signed_summary(), FakeResolver(registry(key_status="REVOKED")))
        self.assertIn("KEY_NOT_ACTIVE_AT_SIGNING_REGISTRY", str(ctx.exception))

    def test_registry_local_compromised_key_is_rejected(self):
        with self.assertRaises(Ed25519AdmissionError) as ctx:
            replay_ed25519_signatures(signed_summary(), FakeResolver(registry(key_status="COMPROMISED")))
        self.assertIn("KEY_NOT_ACTIVE_AT_SIGNING_REGISTRY", str(ctx.exception))

    def test_key_expired_before_receipt_registry_sequence_is_rejected(self):
        with self.assertRaises(Ed25519AdmissionError) as ctx:
            replay_ed25519_signatures(signed_summary(), FakeResolver(registry(valid_until=2)))
        self.assertIn("KEY_EXPIRED_AT_REGISTRY_SEQUENCE", str(ctx.exception))

    def test_offline_witness_cannot_produce_new_receipt_in_signing_snapshot(self):
        with self.assertRaises(Ed25519AdmissionError) as ctx:
            replay_ed25519_signatures(signed_summary(), FakeResolver(registry(witness_status="OFFLINE")))
        self.assertIn("WITNESS_NOT_ACTIVE_AT_SIGNING_REGISTRY", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
