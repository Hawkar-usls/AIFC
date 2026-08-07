#!/usr/bin/env python3
"""Content-addressed evidence resolver for AIFC Verifier A v0.3.

Admission order for protocol evidence:
    exact stored bytes
      -> strict parse/canonical-byte equality
      -> domain-separated content-hash recomputation
      -> Draft 2020-12 runtime JSON Schema validation
      -> semantic replay by the caller

URLs/locators are metadata, not evidence. Network acquisition and source-specific
cryptographic proof remain separate gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from canonical import (
    CanonicalizationError,
    canonical_json_bytes,
    load_json_strict,
    loads_strict,
    protocol_hash,
    raw_evidence_hash,
)
from schema_runtime import RuntimeSchemaError, validate_protocol_object, validate_store_index


class EvidenceResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedEvidence:
    content_hash: str
    content_kind: str
    media_type: str
    declared_schema: str | None
    exact_bytes: bytes
    parsed_json: Mapping[str, Any] | None
    path: Path


class EvidenceResolver:
    def __init__(self, store_root: str | Path, index: Mapping[str, Any]):
        self.root = Path(store_root).resolve()
        try:
            validate_store_index(index)
        except RuntimeSchemaError as exc:
            raise EvidenceResolutionError(f"EVIDENCE_STORE_INDEX_SCHEMA_REJECTED:{exc}") from exc
        entries = index.get("entries")
        self.entries: dict[str, Mapping[str, Any]] = {}
        for entry in entries:
            content_hash = entry.get("content_hash")
            if content_hash in self.entries:
                raise EvidenceResolutionError(f"EVIDENCE_STORE_DUPLICATE_HASH:{content_hash}")
            self.entries[str(content_hash)] = entry

    @classmethod
    def from_index_file(cls, store_root: str | Path, index_path: str | Path) -> "EvidenceResolver":
        index = load_json_strict(index_path)
        if not isinstance(index, Mapping):
            raise EvidenceResolutionError("EVIDENCE_STORE_INDEX_NOT_OBJECT")
        return cls(store_root, index)

    def _safe_path(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str) or not relative_path:
            raise EvidenceResolutionError("EVIDENCE_STORE_RELATIVE_PATH_INVALID")
        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise EvidenceResolutionError("EVIDENCE_STORE_PATH_ESCAPE") from exc
        if not candidate.is_file():
            raise EvidenceResolutionError(f"EVIDENCE_STORE_OBJECT_MISSING:{relative_path}")
        return candidate

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

        # Identity is recomputed before schema admission, by design. A malformed but
        # content-addressed object is still rejected at the next explicit gate.
        actual = protocol_hash(parsed)
        if actual != content_hash:
            raise EvidenceResolutionError(f"PROTOCOL_OBJECT_HASH_MISMATCH:{content_hash}:{actual}")

        try:
            validate_protocol_object(parsed, expected_schema=expected_schema)
        except RuntimeSchemaError as exc:
            raise EvidenceResolutionError(f"RUNTIME_JSON_SCHEMA_REJECTED:{content_hash}:{exc}") from exc

        return ResolvedEvidence(content_hash, kind, str(media_type), str(schema), raw, parsed, path)
