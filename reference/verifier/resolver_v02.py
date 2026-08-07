#!/usr/bin/env python3
"""AIFC v0.2/v0.3 evidence resolver with plan-preregistration domains."""
from __future__ import annotations

from typing import Mapping

from canonical import CanonicalizationError, canonical_json_bytes, loads_strict, raw_evidence_hash
from canonical_v02 import protocol_hash_v02
from resolver import EvidenceResolutionError, EvidenceResolver, ResolvedEvidence
from schema_runtime import RuntimeSchemaError, validate_protocol_object


class EvidenceResolverV02(EvidenceResolver):
    def resolve(self, content_hash: str, expected_schema: str | None = None) -> ResolvedEvidence:
        entry = self.entries.get(content_hash)
        if entry is None:
            raise EvidenceResolutionError(f"DANGLING_EVIDENCE_HASH:{content_hash}")
        path = self._safe_path(str(entry.get("relative_path")))
        raw = path.read_bytes()
        kind = entry.get("content_kind")
        declared_schema = entry.get("declared_schema")
        media_type = entry.get("media_type")

        if kind == "RAW_BYTES":
            actual = raw_evidence_hash(raw)
            if actual != content_hash:
                raise EvidenceResolutionError(f"RAW_EVIDENCE_HASH_MISMATCH:{content_hash}:{actual}")
            if expected_schema is not None:
                raise EvidenceResolutionError("RAW_EVIDENCE_CANNOT_SATISFY_PROTOCOL_SCHEMA")
            return ResolvedEvidence(content_hash, kind, str(media_type), None, raw, None, path)

        if kind != "AIFC_PROTOCOL_JSON":
            raise EvidenceResolutionError(f"EVIDENCE_STORE_CONTENT_KIND_UNKNOWN:{kind}")
        try:
            text = raw.decode("utf-8", errors="strict")
            parsed = loads_strict(text)
        except (UnicodeDecodeError, CanonicalizationError) as exc:
            raise EvidenceResolutionError(f"PROTOCOL_JSON_PARSE_REJECTED:{content_hash}:{exc}") from exc
        if not isinstance(parsed, Mapping):
            raise EvidenceResolutionError("PROTOCOL_JSON_NOT_OBJECT")
        canonical = canonical_json_bytes(parsed)
        if raw != canonical:
            raise EvidenceResolutionError(f"NONCANONICAL_STORED_PROTOCOL_BYTES:{content_hash}")
        schema = parsed.get("schema")
        if declared_schema is not None and schema != declared_schema:
            raise EvidenceResolutionError(f"DECLARED_SCHEMA_REBINDING:{declared_schema}:{schema}")
        if expected_schema is not None and schema != expected_schema:
            raise EvidenceResolutionError(f"EXPECTED_SCHEMA_MISMATCH:{expected_schema}:{schema}")
        actual = protocol_hash_v02(parsed)
        if actual != content_hash:
            raise EvidenceResolutionError(f"PROTOCOL_OBJECT_HASH_MISMATCH:{content_hash}:{actual}")
        try:
            validate_protocol_object(parsed, expected_schema=expected_schema)
        except RuntimeSchemaError as exc:
            raise EvidenceResolutionError(f"RUNTIME_JSON_SCHEMA_REJECTED:{content_hash}:{exc}") from exc
        return ResolvedEvidence(content_hash, kind, str(media_type), str(schema), raw, parsed, path)
