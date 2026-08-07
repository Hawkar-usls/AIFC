import sys
import tempfile
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import canonical_json_bytes, protocol_hash  # noqa: E402
from resolver import EvidenceResolutionError, EvidenceResolver  # noqa: E402


class RuntimeSchemaAdmissionTests(unittest.TestCase):
    def _resolver_for(self, root: Path, obj):
        h = protocol_hash(obj)
        rel = f"objects/{h}.json"
        (root / "objects").mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(canonical_json_bytes(obj))
        index = {
            "schema": "AIFC/evidence-store-index/v1",
            "store_id": "runtime-schema-test",
            "entries": [{
                "content_hash": h,
                "relative_path": rel,
                "content_kind": "AIFC_PROTOCOL_JSON",
                "declared_schema": obj["schema"],
                "media_type": "application/json",
            }],
        }
        return EvidenceResolver(root, index), h

    def test_hash_valid_schema_valid_object_is_resolved(self):
        obj = {
            "schema": "AIFC/hard-witness/v1",
            "experiment_id": "exp-1",
            "run_id": "run-1",
            "trial_index": 1,
            "semantic_class": None,
            "payload128": "11" * 16,
            "nonce128": "22" * 16,
        }
        with tempfile.TemporaryDirectory() as td:
            resolver, h = self._resolver_for(Path(td), obj)
            resolved = resolver.resolve(h, expected_schema="AIFC/hard-witness/v1")
            self.assertEqual(resolved.content_hash, h)

    def test_hash_valid_but_schema_invalid_object_is_rejected(self):
        obj = {
            "schema": "AIFC/hard-witness/v1",
            "experiment_id": "exp-1",
            "run_id": "run-1",
            "trial_index": 1,
            "semantic_class": None,
            "payload128": "11",  # hash-valid JSON, invalid 128-bit payload field
            "nonce128": "22" * 16,
        }
        with tempfile.TemporaryDirectory() as td:
            resolver, h = self._resolver_for(Path(td), obj)
            with self.assertRaises(EvidenceResolutionError) as ctx:
                resolver.resolve(h, expected_schema="AIFC/hard-witness/v1")
            self.assertIn("RUNTIME_JSON_SCHEMA_REJECTED", str(ctx.exception))

    def test_store_index_is_runtime_schema_validated(self):
        bad_index = {
            "schema": "AIFC/evidence-store-index/v1",
            "store_id": "runtime-schema-test",
            "entries": [{
                "content_hash": "f" * 64,
                "relative_path": "../escape.bin",
                "content_kind": "RAW_BYTES",
                "media_type": "application/octet-stream",
            }],
        }
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(EvidenceResolutionError) as ctx:
                EvidenceResolver(td, bad_index)
            self.assertIn("EVIDENCE_STORE_INDEX_SCHEMA_REJECTED", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
