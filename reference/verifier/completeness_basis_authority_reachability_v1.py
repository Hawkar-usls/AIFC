#!/usr/bin/env python3
"""SAL v1.14: current root-closed completeness-basis authority reachability."""
from __future__ import annotations
from dataclasses import dataclass
import inspect
import json
from pathlib import Path
from typing import Any, Mapping

from canonical import domain_hash
import lineage_completeness_basis_authority_v1 as v113
from scientific_assurance_lineage_v13 import (
    NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
    NORMATIVE_ROOT_REGISTRY_ID,
    NORMATIVE_ROOT_REGISTRY_PATH,
    NormativeRootClosureError,
    RootClosedNormativeRepositoryResolver,
    git_blob_sha1_bytes,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_MAIN_COMMIT = "880ef146214e85b32f0974d5fee80a61a299e0b9"
SOURCE_TREE_SHA = "fb91405c02d9df7747fd95ad2bdef507b6877721"
QUESTION_ID = "994c979c702b81a0940f28b8039ad36cb48060c426f42eb1f333bf1630e473b6"
V113_BASIS_PROFILE_PATH = "conformance/AIFC-LINEAGE-COMPLETENESS-BASIS-PROFILE-v1.json"
V113_BASIS_PROFILE_ID = "AIFC-SAL-V1.13-LINEAGE-COMPLETENESS-BASIS-PROFILE-V1"
V113_BASIS_PROFILE_HASH = "4b5a2921ebca347c35a890c3fcc5b8dfa949a8caca37101c6da1faf2c11e414e"
REACHABILITY_PROFILE_PATH = "conformance/AIFC-COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-PROFILE-v1.json"
REACHABILITY_PROFILE_ID = "AIFC-SAL-V1.14-COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-PROFILE-V1"
REACHABILITY_PROFILE_HASH = "239be79f273b6ebea67639b0c414780c941a41a5ea85e2c2d13741a8ee27ae5e"
ROOT_REGISTRY_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V2"
ROOT_REGISTRY_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json"
ROOT_REGISTRY_GIT_BLOB_SHA1 = "d2bb7f3917f8761836825a4e80f03c1e282fc37d"
ROOT_RESOLVER_IMPLEMENTATION_PATH = "reference/verifier/scientific_assurance_lineage_v13.py"
ROOT_RESOLVER_IMPLEMENTATION_GIT_BLOB_SHA1 = "6cd5477969300ae9fcb92c9822ab488360c39262"
SEED_BASIS_SOURCE_ID = "AIFC-SAL-V1.11H-DERIVED-SEMANTIC-LINEAGE-EDGE-BINDING-V1"
OBJECT_RECOGNITION_BASIS_SOURCE_ID = "AIFC-SAL-V1.12-REPOSITORY-OBJECT-INDEX-PROFILE-V1"
REFERENCE_SEMANTICS_BASIS_SOURCE_ID = "AIFC-SAL-V1.12-REPOSITORY-OBJECT-INDEX-PROFILE-V1"
PROFILE_DOMAIN = "AIFC:COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-PROFILE:v1"
AUDIT_DOMAIN = "AIFC:COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-AUDIT:v1"
NOT_REGISTERED = "NOT_REGISTERED_IN_CURRENT_NORMATIVE_ROOT_REGISTRY"
ABSENT_PATH = "ABSENT_IN_CURRENT_ROOT_CLOSED_REGISTRY_SCOPE"
BLOCKED_COMPLETENESS = "BLOCKED_UNAUTHORIZED_COMPLETENESS_BASIS"

class CompletenessBasisAuthorityReachabilityV1Error(ValueError):
    pass

@dataclass(frozen=True)
class AuthorityReachabilityReport:
    normative_root_registry_identity: str
    root_closed_resolver_identity: str
    seed_source_authority_reachability: str
    object_recognition_source_authority_reachability: str
    reference_semantics_source_authority_reachability: str
    v113_completeness_basis_profile_authority_reachability: str
    seed_completeness_authority_path: str
    object_recognition_completeness_authority_path: str
    reference_semantics_completeness_authority_path: str
    caller_root_registry_injection: str
    authority_receipt_caller_input_surface: str
    ci_receipt_to_normative_authority_promotion: str
    successor_defined_authority_edge_promotion: str
    external_bootstrap_ratification: str
    normative_lineage_completeness: str
    derived_semantic_authority: str
    solver_invocation_count: int
    status: str

def _load(path: str) -> Mapping[str, Any]:
    obj = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(obj, Mapping):
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_OBJECT_NOT_MAPPING:" + path)
    return obj

def profile_content_hash(profile: Mapping[str, Any]) -> str:
    m = dict(profile); m.pop("profile_content_hash", None)
    return domain_hash(PROFILE_DOMAIN, m)

def audit_content_hash(audit: Mapping[str, Any]) -> str:
    m = dict(audit); m.pop("audit_content_hash", None)
    return domain_hash(AUDIT_DOMAIN, m)

def verify_reachability_profile(profile: Mapping[str, Any]) -> None:
    expected = {
        "schema": "AIFC/completeness-basis-authority-reachability-profile/v1",
        "profile_id": REACHABILITY_PROFILE_ID,
        "entailment_question_id": QUESTION_ID,
        "source_main_commit": SOURCE_MAIN_COMMIT,
        "source_tree_sha": SOURCE_TREE_SHA,
        "source_v113_basis_profile_id": V113_BASIS_PROFILE_ID,
        "source_v113_basis_profile_content_hash": V113_BASIS_PROFILE_HASH,
        "normative_root_registry_id": ROOT_REGISTRY_ID,
        "normative_root_registry_path": ROOT_REGISTRY_PATH,
        "normative_root_registry_git_blob_sha1": ROOT_REGISTRY_GIT_BLOB_SHA1,
        "root_closed_resolver_implementation_path": ROOT_RESOLVER_IMPLEMENTATION_PATH,
        "root_closed_resolver_implementation_git_blob_sha1": ROOT_RESOLVER_IMPLEMENTATION_GIT_BLOB_SHA1,
        "seed_basis_source_artifact_id": SEED_BASIS_SOURCE_ID,
        "object_recognition_basis_source_artifact_id": OBJECT_RECOGNITION_BASIS_SOURCE_ID,
        "reference_semantics_basis_source_artifact_id": REFERENCE_SEMANTICS_BASIS_SOURCE_ID,
        "authority_resolution_mode": "ROOT_CLOSED_NORMATIVE_REPOSITORY_RESOLVER_ONLY",
        "unregistered_target_policy": "BLOCK",
        "caller_root_registry_injection": "FORBIDDEN",
        "ci_receipt_as_normative_authority": "FORBIDDEN",
        "successor_defined_authority_edge": "FORBIDDEN",
        "profile_authority_status": "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
        "normative_lineage_completeness": BLOCKED_COMPLETENESS,
    }
    for k, v in expected.items():
        if profile.get(k) != v:
            raise CompletenessBasisAuthorityReachabilityV1Error("V114_PROFILE_REBINDING:" + k)
    if profile.get("profile_content_hash") != profile_content_hash(profile):
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_PROFILE_CONTENT_REBINDING")
    if profile.get("profile_content_hash") != REACHABILITY_PROFILE_HASH:
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_PROFILE_EXACT_HASH_REBINDING")
    forbidden = {"authority_status","authority_lineage_ref","authority_receipt_id","root_registry","registry","resolver"}
    if forbidden.intersection(profile):
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_AUTHORITY_INPUT_SURFACE")

def _require_unregistered(resolver: RootClosedNormativeRepositoryResolver, artifact_id: str) -> None:
    if artifact_id in resolver.records:
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_TARGET_REGISTERED:" + artifact_id)
    try:
        resolver.resolve(artifact_id)
    except NormativeRootClosureError as exc:
        if str(exc) != "NORMATIVE_OBJECT_ID_NOT_REGISTERED:" + artifact_id:
            raise CompletenessBasisAuthorityReachabilityV1Error("V114_RESOLUTION_ERROR_REBINDING:" + artifact_id) from exc
    else:
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_UNREGISTERED_TARGET_RESOLVED:" + artifact_id)

def audit_current_reachability() -> AuthorityReachabilityReport:
    verify_reachability_profile(_load(REACHABILITY_PROFILE_PATH))
    v113.verify_basis_profile(_load(V113_BASIS_PROFILE_PATH))
    raw = (ROOT / ROOT_REGISTRY_PATH).read_bytes()
    if git_blob_sha1_bytes(raw) != ROOT_REGISTRY_GIT_BLOB_SHA1:
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_ROOT_REGISTRY_IDENTITY_REBINDING")
    if (NORMATIVE_ROOT_REGISTRY_ID, NORMATIVE_ROOT_REGISTRY_PATH, NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1) != (ROOT_REGISTRY_ID, ROOT_REGISTRY_PATH, ROOT_REGISTRY_GIT_BLOB_SHA1):
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_ROOT_RESOLVER_CONSTANT_REBINDING")
    if inspect.signature(RootClosedNormativeRepositoryResolver.from_repository_authority).parameters:
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_ROOT_RESOLVER_CALLER_SURFACE")
    try:
        RootClosedNormativeRepositoryResolver(ROOT, {})
    except TypeError as exc:
        if "CALLER_SUPPLIED_ROOT_REGISTRY_FORBIDDEN" not in str(exc):
            raise CompletenessBasisAuthorityReachabilityV1Error("V114_ROOT_INJECTION_REJECTION_REBINDING") from exc
    else:
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_ROOT_INJECTION_ACCEPTED")
    resolver = RootClosedNormativeRepositoryResolver.from_repository_authority()
    for artifact_id in (SEED_BASIS_SOURCE_ID, OBJECT_RECOGNITION_BASIS_SOURCE_ID, REFERENCE_SEMANTICS_BASIS_SOURCE_ID, V113_BASIS_PROFILE_ID):
        _require_unregistered(resolver, artifact_id)
    return AuthorityReachabilityReport(
        "CONFIRMED_PINNED_GIT_BLOB",
        "CONFIRMED_FIXED_REPOSITORY_AUTHORITY_FACTORY",
        NOT_REGISTERED, NOT_REGISTERED, NOT_REGISTERED, NOT_REGISTERED,
        ABSENT_PATH, ABSENT_PATH, ABSENT_PATH,
        "REJECTED",
        "FORBIDDEN_NO_CALLER_INPUT_SURFACE",
        "FORBIDDEN_NO_AUTHORITY_INPUT_SURFACE",
        "REJECTED",
        "NOT_PERFORMED",
        BLOCKED_COMPLETENESS,
        "BLOCKED",
        0,
        "AUTHORITY_REACHABILITY_OBSTRUCTION_CONFIRMED_IN_CURRENT_TESTED_SCOPE",
    )

def verify_declared_audit(audit: Mapping[str, Any]) -> AuthorityReachabilityReport:
    static = {
        "schema": "AIFC/completeness-basis-authority-reachability-audit/v1",
        "audit_id": "AIFC-SAL-V1.14-COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-AUDIT-V1",
        "entailment_question_id": QUESTION_ID,
        "source_main_commit": SOURCE_MAIN_COMMIT,
        "source_tree_sha": SOURCE_TREE_SHA,
        "reachability_profile_id": REACHABILITY_PROFILE_ID,
        "reachability_profile_content_hash": REACHABILITY_PROFILE_HASH,
        "normative_root_registry_id": ROOT_REGISTRY_ID,
        "normative_root_registry_git_blob_sha1": ROOT_REGISTRY_GIT_BLOB_SHA1,
    }
    for k, v in static.items():
        if audit.get(k) != v:
            raise CompletenessBasisAuthorityReachabilityV1Error("V114_AUDIT_REBINDING:" + k)
    if audit.get("audit_content_hash") != audit_content_hash(audit):
        raise CompletenessBasisAuthorityReachabilityV1Error("V114_AUDIT_CONTENT_REBINDING")
    report = audit_current_reachability()
    for k, v in report.__dict__.items():
        if audit.get(k) != v:
            raise CompletenessBasisAuthorityReachabilityV1Error("V114_AUDIT_REPORT_REBINDING:" + k)
    return report
