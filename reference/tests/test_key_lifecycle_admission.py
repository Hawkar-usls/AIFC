import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from key_lifecycle import KeyLifecycleError  # noqa: E402
from key_lifecycle_admission import replay_historical_key_lifecycle_admitted  # noqa: E402
from signature_policy_admission import SignaturePreimageMaterial, SignaturePreimageReplaySummary  # noqa: E402


REGISTRY_HASH = "11" * 32


def registry(q=3, sequence=3):
    return {
        "schema": "AIFC/witness-registry/v1",
        "registry_sequence": sequence,
        "fault_model": {"n": 4, "f": 1, "q": q, "independence_unit": "FAILURE_DOMAIN"},
    }


class FakeResolver:
    def __init__(self, registry_obj):
        self.registry_obj = registry_obj

    def resolve(self, content_hash, expected_schema=None):
        self.last_hash = content_hash
        if expected_schema != "AIFC/witness-registry/v1":
            raise ValueError(f"unexpected schema {expected_schema}")
        return SimpleNamespace(parsed_json=self.registry_obj)


def summary(q=3, sequence=3):
    materials = []
    for i in range(3):
        materials.append(SignaturePreimageMaterial(
            receipt_schema="AIFC/witness-receipt/v1",
            receipt={"witness_id": f"w{i}"},
            preimage=f"m{i}".encode(),
            registry_hash=REGISTRY_HASH,
            registry_sequence=sequence,
            witness_id=f"w{i}",
            key_id=f"k{i}",
            certificate_group_id="certificate-A",
            required_q=q,
        ))
    return SignaturePreimageReplaySummary(
        receipt_count=3,
        preimage_sha256s=("aa" * 32, "bb" * 32, "cc" * 32),
        materials=tuple(materials),
    )


class KeyLifecycleAdmissionTests(unittest.TestCase):
    def test_matching_registry_q_and_sequence_reaches_lifecycle_core(self):
        expected = SimpleNamespace(external_completeness_proven=False)
        with patch("key_lifecycle_admission.replay_historical_key_lifecycle", return_value=expected) as core:
            result = replay_historical_key_lifecycle_admitted({}, FakeResolver(registry()), summary())
        self.assertIs(result, expected)
        core.assert_called_once()

    def test_required_q_cannot_be_lowered_after_crypto(self):
        with patch("key_lifecycle_admission.replay_historical_key_lifecycle") as core:
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle_admitted({}, FakeResolver(registry(q=3)), summary(q=2))
        core.assert_not_called()
        self.assertIn("HISTORICAL_QUORUM_Q_VS_REGISTRY_MISMATCH", str(ctx.exception))

    def test_registry_sequence_metadata_cannot_be_rebound_after_crypto(self):
        with patch("key_lifecycle_admission.replay_historical_key_lifecycle") as core:
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle_admitted({}, FakeResolver(registry(sequence=3)), summary(sequence=2))
        core.assert_not_called()
        self.assertIn("HISTORICAL_REGISTRY_SEQUENCE_REBINDING", str(ctx.exception))

    def test_intra_certificate_q_disagreement_is_rejected(self):
        s = summary(q=3)
        altered = list(s.materials)
        altered[2] = SignaturePreimageMaterial(
            receipt_schema=altered[2].receipt_schema,
            receipt=altered[2].receipt,
            preimage=altered[2].preimage,
            registry_hash=altered[2].registry_hash,
            registry_sequence=altered[2].registry_sequence,
            witness_id=altered[2].witness_id,
            key_id=altered[2].key_id,
            certificate_group_id=altered[2].certificate_group_id,
            required_q=2,
        )
        bad = SignaturePreimageReplaySummary(3, s.preimage_sha256s, tuple(altered))
        with self.assertRaises(KeyLifecycleError) as ctx:
            replay_historical_key_lifecycle_admitted({}, FakeResolver(registry()), bad)
        self.assertIn("HISTORICAL_QUORUM_Q_REBINDING", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
