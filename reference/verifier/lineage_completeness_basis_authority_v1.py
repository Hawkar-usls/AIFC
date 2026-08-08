#!/usr/bin/env python3
"""SAL v1.13 lineage completeness-basis authority boundary.

This layer does not establish global lineage completeness. It binds the exact
local v1.12 closure to three independently identified completeness bases:
the inherited seed, repository-object recognition, and reference semantics.
It then fails closed because normative/global adequacy authority for those
bases is not established.

A local least fixed point is evidence about closure under chosen semantics;
it is not authority for the choice or global adequacy of those semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from canonical import domain_hash
import lineage_vertex_reference_closure_v1 as v112

ROOT = Path(__file__).resolve().parents[2]

SOURCE_MAIN_COMMIT = "356c8444218cdecdbb5bd89480967d31173d7fd5"
SOURCE_TREE_SHA = "098a6275fcb0ccfa21b874ff70a4f89f7c03a02b"
QUESTION_ID = "994c979c702b81a0940f28b8039ad36cb48060c426f42eb1f333bf1630e473b6"

V112_CLOSURE_PATH = "conformance/AIFC-LINEAGE-VERTEX-UNIVERSE-CLOSURE-v1.json"
V112_CLOSURE_ID = "AIFC-SAL-V1.12-LINEAGE-VERTEX-UNIVERSE-CLOSURE-V1"
V112_CLOSURE_HASH = "ff7fc0679a6de91f776e2def53e43005a138e531304c4b60f06774fb3184c388"

SEED_BINDING_PATH = "conformance/AIFC-DERIVED-SEMANTIC-LINEAGE-EDGE-BINDING-v1.json"
SEED_BINDING_ID = "AIFC-SAL-V1.11H-DERIVED-SEMANTIC-LINEAGE-EDGE-BINDING-V1"
SEED_BINDING_HASH = "42489c49e177f600317bc579fb0d875995216920cbb80327abe2091d2190bbd7"

OBJECT_INDEX_PROFILE_PATH = "conformance/AIFC-REPOSITORY-OBJECT-INDEX-PROFILE-v1.json"
OBJECT_INDEX_PROFILE_ID = "AIFC-SAL-V1.12-REPOSITORY-OBJECT-INDEX-PROFILE-V1"
OBJECT_INDEX_PROFILE_HASH = "7c0a0f9d05664dded7a4320854c5699e6371ebffca427b7fc3900a094bf832a0"

BASIS_PROFILE_PATH = "conformance/AIFC-LINEAGE-COMPLETENESS-BASIS-PROFILE-v1.json"
BASIS_PROFILE_ID = "AIFC-SAL-V1.13-LINEAGE-COMPLETENESS-BASIS-PROFILE-V1"
BASIS_PROFILE_HASH = "4b5a2921ebca347c35a890c3fcc5b8dfa949a8caca37101c6da1faf2c11e414e"

AUDIT_PATH = "conformance/AIFC-LINEAGE-COMPLETENESS-AUTHORITY-AUDIT-v1.json"
AUDIT_ID = "AIFC-SAL-V1.13-LINEAGE-COMPLETENESS-AUTHORITY-AUDIT-V1"
AUDIT_HASH = "2f950e57d1fbe80f9446e4bd6b5e3aec0b68793e29d72506c4799c6cf7f923fc"

SEED_BASIS_DOMAIN = "AIFC:LINEAGE-SEED-BASIS:v1"
OBJECT_RECOGNITION_BASIS_DOMAIN = "AIFC:OBJECT-RECOGNITION-BASIS:v1"
REFERENCE_SEMANTICS_BASIS_DOMAIN = "AIFC:REFERENCE-SEMANTICS-BASIS:v1"
PROFILE_DOMAIN = "AIFC:LINEAGE-COMPLETENESS-BASIS-PROFILE:v1"
AUDIT_DOMAIN = "AIFC:LINEAGE-COMPLETENESS-AUTHORITY-AUDIT:v1"

SEED_BASIS_HASH = "a88f36387fe0f54e5fb19ec7bf3ebe9850aea799ded0a89be9a190c55b9ab433"
OBJECT_RECOGNITION_BASIS_HASH = "9293dec8f2570332c2e5642f4db74ed9faedb48abcaac69177e65c931a1be33b"
REFERENCE_SEMANTICS_BASIS_HASH = "be565b8e4e1b216db7d9e71df14db863cf83d012305457bf2ad38b718b5375d5"

LOCAL_CLOSURE = "ESTABLISHED_IN_TESTED_SCOPE_FROM_INHERITED_SEED"
BLOCKED_COMPLETENESS = "BLOCKED_UNAUTHORIZED_COMPLETENESS_BASIS"
NOT_ESTABLISHED = "NOT_ESTABLISHED"


class LineageCompletenessBasisAuthorityV1Error(ValueError):
    pass


@dataclass(frozen=True)
class CompletenessBasisAuthorityReport:
    seed_basis_projection_hash: str
    object_recognition_basis_projection_hash: str
    reference_semantics_basis_projection_hash: str
    local_reference_closure: str
    seed_basis_identity: str
    seed_completeness_authority: str
    object_recognition_basis_identity: str
    object_recognition_global_adequacy_authority: str
    reference_semantics_basis_identity: str
    reference_semantics_global_adequacy_authority: str
    normative_lineage_completeness: str
    local_fixed_point_to_global_completeness_promotion: str
    exact_seed_identity_to_seed_completeness_promotion: str
    exact_profile_identity_to_global_adequacy_promotion: str
    successor_defined_completeness_authority: str
    completeness_basis_authority_input_surface: str
    global_lineage_seed_completeness: str
    object_index_profile_global_adequacy: str
    global_repository_object_universe_completeness: str
    lineage_semantic_relation_universe_completeness: str
    derived_semantic_authority: str
    solver_invocation_count: int
    status: str


def _load(path: str) -> Mapping[str, Any]:
    obj = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(obj, Mapping):
        raise LineageCompletenessBasisAuthorityV1Error("V113_OBJECT_NOT_MAPPING:" + path)
    return obj


def profile_content_hash(profile: Mapping[str, Any]) -> str:
    material = dict(profile)
    material.pop("profile_content_hash", None)
    return domain_hash(PROFILE_DOMAIN, material)


def audit_content_hash(audit: Mapping[str, Any]) -> str:
    material = dict(audit)
    material.pop("audit_content_hash", None)
    return domain_hash(AUDIT_DOMAIN, material)


def seed_basis_projection_hash(
    closure: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> str:
    material = {
        "source_seed_binding_id": binding.get("lineage_edge_binding_id"),
        "source_seed_binding_content_hash": binding.get("binding_content_hash"),
        "seed_derivation": closure.get("seed_derivation"),
        "vertices": binding.get("vertices"),
    }
    return domain_hash(SEED_BASIS_DOMAIN, material)


def object_recognition_basis_projection_hash(profile: Mapping[str, Any]) -> str:
    material = {
        "source_object_index_profile_id": profile.get("object_index_profile_id"),
        "source_object_index_profile_content_hash": profile.get("profile_content_hash"),
        "index_scope_prefix": profile.get("index_scope_prefix"),
        "file_suffix": profile.get("file_suffix"),
        "strict_json": profile.get("strict_json"),
        "recognized_schemas": profile.get("recognized_schemas"),
        "implementation_path": profile.get("implementation_path"),
        "implementation_git_blob_sha1": profile.get("implementation_git_blob_sha1"),
        "implementation_raw_sha256": profile.get("implementation_raw_sha256"),
    }
    return domain_hash(OBJECT_RECOGNITION_BASIS_DOMAIN, material)


def reference_semantics_basis_projection_hash(profile: Mapping[str, Any]) -> str:
    material = {
        "source_object_index_profile_id": profile.get("object_index_profile_id"),
        "source_object_index_profile_content_hash": profile.get("profile_content_hash"),
        "reference_rules": profile.get("reference_rules"),
        "implementation_path": profile.get("implementation_path"),
        "implementation_git_blob_sha1": profile.get("implementation_git_blob_sha1"),
        "implementation_raw_sha256": profile.get("implementation_raw_sha256"),
    }
    return domain_hash(REFERENCE_SEMANTICS_BASIS_DOMAIN, material)


def verify_basis_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("schema") != "AIFC/lineage-completeness-basis-profile/v1":
        raise LineageCompletenessBasisAuthorityV1Error("V113_BASIS_PROFILE_SCHEMA_REBINDING")
    if profile.get("profile_id") != BASIS_PROFILE_ID:
        raise LineageCompletenessBasisAuthorityV1Error("V113_BASIS_PROFILE_ID_REBINDING")
    if profile.get("entailment_question_id") != QUESTION_ID:
        raise LineageCompletenessBasisAuthorityV1Error("V113_BASIS_PROFILE_QUESTION_REBINDING")
    if profile.get("profile_content_hash") != profile_content_hash(profile):
        raise LineageCompletenessBasisAuthorityV1Error("V113_BASIS_PROFILE_CONTENT_REBINDING")
    if profile.get("profile_content_hash") != BASIS_PROFILE_HASH:
        raise LineageCompletenessBasisAuthorityV1Error("V113_BASIS_PROFILE_EXACT_HASH_REBINDING")

    expected_refs = {
        "source_v112_closure_id": V112_CLOSURE_ID,
        "source_v112_closure_content_hash": V112_CLOSURE_HASH,
        "source_seed_binding_id": SEED_BINDING_ID,
        "source_seed_binding_content_hash": SEED_BINDING_HASH,
        "source_object_index_profile_id": OBJECT_INDEX_PROFILE_ID,
        "source_object_index_profile_content_hash": OBJECT_INDEX_PROFILE_HASH,
        "seed_basis_projection_hash": SEED_BASIS_HASH,
        "object_recognition_basis_projection_hash": OBJECT_RECOGNITION_BASIS_HASH,
        "reference_semantics_basis_projection_hash": REFERENCE_SEMANTICS_BASIS_HASH,
        "local_reference_closure_requirement": LOCAL_CLOSURE,
        "seed_completeness_authority_requirement":
            "REQUIRED_FOR_GLOBAL_NORMATIVE_LINEAGE_COMPLETENESS",
        "object_recognition_global_adequacy_authority_requirement":
            "REQUIRED_FOR_GLOBAL_NORMATIVE_LINEAGE_COMPLETENESS",
        "reference_semantics_global_adequacy_authority_requirement":
            "REQUIRED_FOR_GLOBAL_NORMATIVE_LINEAGE_COMPLETENESS",
        "profile_authority_status": "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
        "global_normative_lineage_completeness": BLOCKED_COMPLETENESS,
    }
    for key, expected in expected_refs.items():
        if profile.get(key) != expected:
            raise LineageCompletenessBasisAuthorityV1Error(
                "V113_BASIS_PROFILE_FIELD_REBINDING:" + key
            )

    forbidden = {
        "seed_completeness_authority",
        "object_recognition_global_adequacy_authority",
        "reference_semantics_global_adequacy_authority",
        "authority_lineage_ref",
        "authority_status",
        "global_completeness_authority",
    }
    if forbidden.intersection(profile):
        raise LineageCompletenessBasisAuthorityV1Error(
            "SUCCESSOR_DEFINED_COMPLETENESS_AUTHORITY"
        )


def verify_current_basis_sources(
    closure: Mapping[str, Any],
    binding: Mapping[str, Any],
    object_index_profile: Mapping[str, Any],
    basis_profile: Mapping[str, Any],
) -> CompletenessBasisAuthorityReport:
    if closure.get("schema") != "AIFC/lineage-vertex-universe-closure/v1":
        raise LineageCompletenessBasisAuthorityV1Error("V113_SOURCE_CLOSURE_SCHEMA_REBINDING")
    if closure.get("closure_id") != V112_CLOSURE_ID:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SOURCE_CLOSURE_ID_REBINDING")
    if closure.get("closure_content_hash") != v112.closure_content_hash(closure):
        raise LineageCompletenessBasisAuthorityV1Error("V113_SOURCE_CLOSURE_CONTENT_REBINDING")
    if closure.get("closure_content_hash") != V112_CLOSURE_HASH:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SOURCE_CLOSURE_EXACT_HASH_REBINDING")
    if closure.get("entailment_question_id") != QUESTION_ID:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SOURCE_CLOSURE_QUESTION_REBINDING")
    if closure.get("reference_closure_status") != LOCAL_CLOSURE:
        raise LineageCompletenessBasisAuthorityV1Error("V113_LOCAL_REFERENCE_CLOSURE_NOT_ESTABLISHED")
    if closure.get("fixed_point_status") != "MACHINE_VERIFIED_BY_FINAL_REPLAY":
        raise LineageCompletenessBasisAuthorityV1Error("V113_FIXED_POINT_NOT_REPLAYED")
    if closure.get("seed_derivation") != "FROM_INHERITED_V1_11H_BINDING_VERTICES":
        raise LineageCompletenessBasisAuthorityV1Error("V113_SEED_DERIVATION_REBINDING")
    if closure.get("source_lineage_edge_binding_id") != SEED_BINDING_ID:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SEED_BINDING_ID_REBINDING")
    if closure.get("source_lineage_edge_binding_content_hash") != SEED_BINDING_HASH:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SEED_BINDING_HASH_REBINDING")

    for key in (
        "global_lineage_seed_completeness",
        "object_index_profile_global_adequacy",
        "global_repository_object_universe_completeness",
        "semantic_relation_universe_completeness",
    ):
        if closure.get(key) != NOT_ESTABLISHED:
            raise LineageCompletenessBasisAuthorityV1Error(
                "V113_LOCAL_CLOSURE_FALSE_GLOBAL_PROMOTION:" + key
            )
    if closure.get("derived_semantic_authority") != "BLOCKED":
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_DERIVED_AUTHORITY_FALSE_PROMOTION"
        )
    if closure.get("solver_invocation_count") != 0:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SOLVER_INVOCATION_FORBIDDEN")

    if binding.get("lineage_edge_binding_id") != SEED_BINDING_ID:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SEED_BINDING_OBJECT_ID_REBINDING")
    if binding.get("binding_content_hash") != SEED_BINDING_HASH:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SEED_BINDING_OBJECT_HASH_REBINDING")
    if binding.get("binding_status") != "SUCCESSOR_CANDIDATE_EXECUTION_EDGE_CLOSURE":
        raise LineageCompletenessBasisAuthorityV1Error("V113_SEED_BINDING_STATUS_REBINDING")
    vertices = binding.get("vertices")
    if not isinstance(vertices, list) or len(vertices) != 6:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SEED_VERTEX_SET_REBINDING")

    v112.verify_profile(object_index_profile)
    if object_index_profile.get("object_index_profile_id") != OBJECT_INDEX_PROFILE_ID:
        raise LineageCompletenessBasisAuthorityV1Error("V113_OBJECT_INDEX_PROFILE_ID_REBINDING")
    if object_index_profile.get("profile_content_hash") != v112.profile_content_hash(
        object_index_profile
    ):
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_OBJECT_INDEX_PROFILE_CONTENT_REBINDING"
        )
    if object_index_profile.get("profile_content_hash") != OBJECT_INDEX_PROFILE_HASH:
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_OBJECT_INDEX_PROFILE_EXACT_HASH_REBINDING"
        )
    if object_index_profile.get("profile_authority_status") != (
        "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE"
    ):
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_OBJECT_INDEX_PROFILE_AUTHORITY_SELF_ASSERTION"
        )
    if object_index_profile.get("global_adequacy") != NOT_ESTABLISHED:
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_OBJECT_INDEX_PROFILE_GLOBAL_ADEQUACY_FALSE_PROMOTION"
        )

    seed_hash = seed_basis_projection_hash(closure, binding)
    recognition_hash = object_recognition_basis_projection_hash(object_index_profile)
    reference_hash = reference_semantics_basis_projection_hash(object_index_profile)
    if seed_hash != SEED_BASIS_HASH:
        raise LineageCompletenessBasisAuthorityV1Error("V113_SEED_BASIS_PROJECTION_REBINDING")
    if recognition_hash != OBJECT_RECOGNITION_BASIS_HASH:
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_OBJECT_RECOGNITION_BASIS_PROJECTION_REBINDING"
        )
    if reference_hash != REFERENCE_SEMANTICS_BASIS_HASH:
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_REFERENCE_SEMANTICS_BASIS_PROJECTION_REBINDING"
        )

    verify_basis_profile(basis_profile)
    if basis_profile.get("seed_basis_projection_hash") != seed_hash:
        raise LineageCompletenessBasisAuthorityV1Error("V113_PROFILE_SEED_BASIS_DISCONNECT")
    if basis_profile.get("object_recognition_basis_projection_hash") != recognition_hash:
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_PROFILE_OBJECT_RECOGNITION_BASIS_DISCONNECT"
        )
    if basis_profile.get("reference_semantics_basis_projection_hash") != reference_hash:
        raise LineageCompletenessBasisAuthorityV1Error(
            "V113_PROFILE_REFERENCE_SEMANTICS_BASIS_DISCONNECT"
        )

    return CompletenessBasisAuthorityReport(
        seed_basis_projection_hash=seed_hash,
        object_recognition_basis_projection_hash=recognition_hash,
        reference_semantics_basis_projection_hash=reference_hash,
        local_reference_closure=LOCAL_CLOSURE,
        seed_basis_identity="CONFIRMED_EXACT_INHERITED_BINDING_PROJECTION",
        seed_completeness_authority=NOT_ESTABLISHED,
        object_recognition_basis_identity="CONFIRMED_CONTENT_BOUND_PROJECTION",
        object_recognition_global_adequacy_authority=NOT_ESTABLISHED,
        reference_semantics_basis_identity="CONFIRMED_CONTENT_BOUND_PROJECTION",
        reference_semantics_global_adequacy_authority=NOT_ESTABLISHED,
        normative_lineage_completeness=BLOCKED_COMPLETENESS,
        local_fixed_point_to_global_completeness_promotion="REJECTED",
        exact_seed_identity_to_seed_completeness_promotion="REJECTED",
        exact_profile_identity_to_global_adequacy_promotion="REJECTED",
        successor_defined_completeness_authority="REJECTED",
        completeness_basis_authority_input_surface="FORBIDDEN",
        global_lineage_seed_completeness=NOT_ESTABLISHED,
        object_index_profile_global_adequacy=NOT_ESTABLISHED,
        global_repository_object_universe_completeness=NOT_ESTABLISHED,
        lineage_semantic_relation_universe_completeness=NOT_ESTABLISHED,
        derived_semantic_authority="BLOCKED",
        solver_invocation_count=0,
        status="OBSTRUCTION_CONFIRMED_IN_CURRENT_TESTED_PATH",
    )


def verify_audit_object(
    audit: Mapping[str, Any],
    report: CompletenessBasisAuthorityReport,
) -> None:
    if audit.get("schema") != "AIFC/lineage-completeness-authority-audit/v1":
        raise LineageCompletenessBasisAuthorityV1Error("V113_AUDIT_SCHEMA_REBINDING")
    if audit.get("audit_id") != AUDIT_ID:
        raise LineageCompletenessBasisAuthorityV1Error("V113_AUDIT_ID_REBINDING")
    if audit.get("audit_content_hash") != audit_content_hash(audit):
        raise LineageCompletenessBasisAuthorityV1Error("V113_AUDIT_CONTENT_REBINDING")
    if audit.get("audit_content_hash") != AUDIT_HASH:
        raise LineageCompletenessBasisAuthorityV1Error("V113_AUDIT_EXACT_HASH_REBINDING")

    expected = {
        "entailment_question_id": QUESTION_ID,
        "basis_profile_id": BASIS_PROFILE_ID,
        "basis_profile_content_hash": BASIS_PROFILE_HASH,
        "source_main_commit": SOURCE_MAIN_COMMIT,
        "source_tree_sha": SOURCE_TREE_SHA,
        "source_v112_closure_id": V112_CLOSURE_ID,
        "source_v112_closure_content_hash": V112_CLOSURE_HASH,
        "seed_basis_projection_hash": report.seed_basis_projection_hash,
        "object_recognition_basis_projection_hash":
            report.object_recognition_basis_projection_hash,
        "reference_semantics_basis_projection_hash":
            report.reference_semantics_basis_projection_hash,
        "local_reference_closure": report.local_reference_closure,
        "seed_basis_identity": report.seed_basis_identity,
        "seed_completeness_authority": report.seed_completeness_authority,
        "object_recognition_basis_identity": report.object_recognition_basis_identity,
        "object_recognition_global_adequacy_authority":
            report.object_recognition_global_adequacy_authority,
        "reference_semantics_basis_identity": report.reference_semantics_basis_identity,
        "reference_semantics_global_adequacy_authority":
            report.reference_semantics_global_adequacy_authority,
        "normative_lineage_completeness": report.normative_lineage_completeness,
        "local_fixed_point_to_global_completeness_promotion":
            report.local_fixed_point_to_global_completeness_promotion,
        "exact_seed_identity_to_seed_completeness_promotion":
            report.exact_seed_identity_to_seed_completeness_promotion,
        "exact_profile_identity_to_global_adequacy_promotion":
            report.exact_profile_identity_to_global_adequacy_promotion,
        "successor_defined_completeness_authority":
            report.successor_defined_completeness_authority,
        "completeness_basis_authority_input_surface":
            report.completeness_basis_authority_input_surface,
        "global_lineage_seed_completeness": report.global_lineage_seed_completeness,
        "object_index_profile_global_adequacy":
            report.object_index_profile_global_adequacy,
        "global_repository_object_universe_completeness":
            report.global_repository_object_universe_completeness,
        "lineage_semantic_relation_universe_completeness":
            report.lineage_semantic_relation_universe_completeness,
        "derived_semantic_authority": report.derived_semantic_authority,
        "solver_invocation_count": report.solver_invocation_count,
        "status": report.status,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            raise LineageCompletenessBasisAuthorityV1Error(
                "V113_AUDIT_FIELD_REBINDING:" + key
            )


def audit_lineage_completeness_basis() -> CompletenessBasisAuthorityReport:
    """Replay the exact current basis obstruction with no caller authority inputs."""
    closure = _load(V112_CLOSURE_PATH)
    binding = _load(SEED_BINDING_PATH)
    object_index_profile = _load(OBJECT_INDEX_PROFILE_PATH)
    basis_profile = _load(BASIS_PROFILE_PATH)
    report = verify_current_basis_sources(
        closure,
        binding,
        object_index_profile,
        basis_profile,
    )
    verify_audit_object(_load(AUDIT_PATH), report)
    return report
