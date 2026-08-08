#!/usr/bin/env python3
"""SAL v1.11 canonical semantic-locus resolver candidate.

Resolution is deliberately authority-blind. It can return only RESOLVED,
AMBIGUOUS, or UNRESOLVED; normative authority is decided elsewhere.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from canonical import domain_hash
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v19 as v19

REFERENCE_DOMAIN = "AIFC:CANONICAL-SEMANTIC-REFERENCE:v1"
PROFILE_DOMAIN = "AIFC:CANONICAL-SEMANTIC-RESOLVER-PROFILE:v1"

class CanonicalSemanticResolverV1Error(ValueError):
    pass

@dataclass(frozen=True)
class CanonicalResolution:
    state: str
    semantic_reference_id: str
    canonical_semantic_identity: str | None
    canonical_source_identity: str | None
    resolved_semantic_role: str | None
    authority_scope_evidence: str | None
    ambiguity_candidates: tuple[str, ...]

def reference_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj)
    material.pop("reference_content_hash", None)
    return domain_hash(REFERENCE_DOMAIN, material)

def profile_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj)
    material.pop("profile_content_hash", None)
    return domain_hash(PROFILE_DOMAIN, material)

def classify_resolution_candidates(candidates: Sequence[str]) -> tuple[str, str | None, tuple[str, ...]]:
    unique = tuple(sorted(set(candidates)))
    if not unique:
        return "UNRESOLVED", None, ()
    if len(unique) > 1:
        return "AMBIGUOUS", None, unique
    return "RESOLVED", unique[0], unique

def _scope_evidence(identity: str) -> str:
    if identity.startswith(("REQUIRED_CHECK_ID:", "FORBIDDEN_SHORTCUT_EXACT:", "PROFILE_FIELD:")):
        return "CANDIDATE_NORMATIVE_LOCUS_SCOPE_EVIDENCE"
    return "NONNORMATIVE_OR_UNSUPPORTED_LOCUS"

def _role_for_formula(formula_role: str) -> str:
    if formula_role == "PREDECESSOR_PREMISE":
        return "PREDECESSOR_ATOM"
    if formula_role == "TARGET_TRANSITION_PROFILE":
        return "TARGET_ATOM"
    raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_FORMULA_ROLE_UNSUPPORTED")

def resolve_reference(ref: Mapping[str, Any], profile: Mapping[str, Any]) -> CanonicalResolution:
    if profile.get("schema") != "AIFC/canonical-semantic-resolver-profile/v1":
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_RESOLUTION_PROFILE_SUBSTITUTION")
    if ref.get("schema") != "AIFC/canonical-semantic-reference/v1":
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_REFERENCE_SCHEMA_REBINDING")
    if ref.get("resolver_profile_id") != profile.get("resolver_profile_id"):
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_RESOLUTION_PROFILE_SUBSTITUTION")
    if ref.get("reference_content_hash") != reference_content_hash(ref):
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_REFERENCE_CONTENT_REBINDING")
    locator = ref.get("semantic_locator")
    if not isinstance(locator, Mapping) or locator.get("kind") != "FORMULA_ATOM_BINDING":
        return CanonicalResolution("UNRESOLVED", str(ref.get("semantic_reference_id")), None, None, None, None, ())
    atom_id = locator.get("atom_id")
    if not isinstance(atom_id, str) or not atom_id:
        return CanonicalResolution("UNRESOLVED", str(ref.get("semantic_reference_id")), None, None, None, None, ())
    raw = v19._historical_bound_bytes(
        str(ref.get("source_commit_sha")),
        str(ref.get("source_path")),
        str(ref.get("source_git_blob_sha1")),
    )
    if hashlib.sha256(raw).hexdigest() != ref.get("source_raw_sha256"):
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_SOURCE_RAW_SHA256_REBINDING")
    try:
        source = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_SOURCE_DECODE_FAILED") from exc
    if source.get("schema") != ref.get("source_object_schema_id"):
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_SOURCE_SCHEMA_REBINDING")
    if source.get("entailment_question_id") != ref.get("entailment_question_id"):
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_SOURCE_QUESTION_REBINDING")
    if source.get("formula_content_hash") != ref.get("source_object_content_hash"):
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_SOURCE_CONTENT_REBINDING")
    bindings = source.get("atom_bindings")
    if not isinstance(bindings, Mapping) or atom_id not in bindings:
        return CanonicalResolution("UNRESOLVED", str(ref.get("semantic_reference_id")), None, None, None, None, ())
    candidate = bindings[atom_id]
    if not isinstance(candidate, str) or not candidate:
        return CanonicalResolution("UNRESOLVED", str(ref.get("semantic_reference_id")), None, None, None, None, ())
    state, canonical, ambiguity = classify_resolution_candidates([candidate])
    assert state == "RESOLVED" and canonical is not None
    role = _role_for_formula(str(source.get("formula_role")))
    if ref.get("declared_canonical_semantic_identity") != canonical:
        raise CanonicalSemanticResolverV1Error("SEMANTIC_LOCUS_TO_CANONICAL_IDENTITY_REBINDING")
    if ref.get("resolved_semantic_role") != role:
        raise CanonicalSemanticResolverV1Error("DERIVED_SEMANTIC_SOURCE_ROLE_REBINDING")
    scope = _scope_evidence(canonical)
    if ref.get("authority_scope_evidence") != scope:
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_LOCUS_AUTHORITY_SCOPE_REBINDING")
    source_identity = domain_hash(
        "AIFC:CANONICAL-SEMANTIC-SOURCE:v1",
        {
            "source_commit_sha": ref.get("source_commit_sha"),
            "source_git_blob_sha1": ref.get("source_git_blob_sha1"),
            "source_raw_sha256": ref.get("source_raw_sha256"),
            "semantic_locator": locator,
            "canonical_semantic_identity": canonical,
        },
    )
    if ref.get("canonical_source_identity") != source_identity:
        raise CanonicalSemanticResolverV1Error("CANONICAL_SEMANTIC_SOURCE_IDENTITY_REBINDING")
    return CanonicalResolution(
        "RESOLVED",
        str(ref.get("semantic_reference_id")),
        canonical,
        source_identity,
        role,
        scope,
        ambiguity,
    )
