#!/usr/bin/env python3
"""AIFC Assurance Evidence v1 content identity and resolver.

This module intentionally does NOT extend historical protocol_hash_v02 or the
predecessor protocol hash domain maps. Assurance-convergence metadata introduced
after those profiles receives a new, explicit content-addressing domain.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from canonical import CanonicalizationError, canonical_json_bytes, loads_strict, raw_evidence_hash
from resolver import EvidenceResolutionError, EvidenceResolver, ResolvedEvidence
from schema_runtime import RuntimeSchemaError, validate_protocol_object


ASSURANCE_EVIDENCE_HASH_PROFILE = "AIFC/assurance-evidence-hash/v1"
ASSURANCE_EVIDENCE_DOMAIN = b"AIFC:ASSURANCE-EVIDENCE:v1\x00"
ASSURANCE_PROTOCOL_SCHEMAS = frozenset({
    "AIFC/gate-definition/v1",
    "AIFC/gate-strengthening-evidence/v1",
    "AIFC/gate-lineage-transition/v1",
})


class AssuranceEvidenceError(ValueError):
    pass


def assurance_protocol_hash_v1(value: Mapping[str, Any]) -> str:
    """Return the v1 content hash for assurance-only protocol metadata.

    The schema ID is included explicitly in the preimage even though it is also
    present in canonical JSON. This makes cross-schema domain separation an
    intentional protocol property rather than an incidental property of fields.
    """
    schema = value.get("schema")
    if schema not in ASSURANCE_PROTOCOL_SCHEMAS:
        raise AssuranceEvidenceError(f"ASSURANCE_EVIDENCE_SCHEMA_NOT_IN_PROFILE:{schema}")
    schema_bytes = str(schema).encode("utf-8", errors="strict")
    canonical = canonical_json_bytes(value)
    return hashlib.sha256(
        ASSURANCE_EVIDENCE_DOMAIN
        + schema_bytes
        + b"\x00"
        + canonical
    ).hexdigest()


class AssuranceEvidenceResolverV1(EvidenceResolver):
    """Resolve assurance metadata without changing predecessor hash semantics."""

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
            raise EvidenceResolutionError(f"ASSURANCE_PROTOCOL_JSON_PARSE_REJECTED:{content_hash}:{exc}") from exc
        if not isinstance(parsed, Mapping):
            raise EvidenceResolutionError("ASSURANCE_PROTOCOL_JSON_NOT_OBJECT")

        canonical = canonical_json_bytes(parsed)
        if raw != canonical:
            raise EvidenceResolutionError(f"NONCANONICAL_ASSURANCE_PROTOCOL_BYTES:{content_hash}")

        schema = parsed.get("schema")
        if schema not in ASSURANCE_PROTOCOL_SCHEMAS:
            raise EvidenceResolutionError(f"ASSURANCE_EVIDENCE_SCHEMA_NOT_IN_PROFILE:{schema}")
        if declared_schema is not None and schema != declared_schema:
            raise EvidenceResolutionError(f"DECLARED_SCHEMA_REBINDING:{declared_schema}:{schema}")
        if expected_schema is not None and schema != expected_schema:
            raise EvidenceResolutionError(f"EXPECTED_SCHEMA_MISMATCH:{expected_schema}:{schema}")

        try:
            actual = assurance_protocol_hash_v1(parsed)
        except AssuranceEvidenceError as exc:
            raise EvidenceResolutionError(str(exc)) from exc
        if actual != content_hash:
            raise EvidenceResolutionError(f"ASSURANCE_PROTOCOL_OBJECT_HASH_MISMATCH:{content_hash}:{actual}")

        try:
            validate_protocol_object(parsed, expected_schema=expected_schema)
        except RuntimeSchemaError as exc:
            raise EvidenceResolutionError(f"RUNTIME_JSON_SCHEMA_REJECTED:{content_hash}:{exc}") from exc

        return ResolvedEvidence(content_hash, kind, str(media_type), str(schema), raw, parsed, path)
