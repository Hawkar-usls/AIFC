#!/usr/bin/env python3
"""SAL v1.12 Lineage Vertex Universe Reference Closure.

This successor hardening layer starts from the inherited six exact v1.11h
vertices, enumerates the exact v1.11u predecessor Git tree, builds the
recognized repository-object index under a content-bound candidate profile,
and computes the least fixed point of recursively resolvable classified
references. It preserves the authority and solver ceilings.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping

from canonical import domain_hash, loads_strict
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v111h as v111h
import scientific_assurance_lineage_v111u as v111u
import lineage_vertex_reference_closure_v1 as closure

ROOT = Path(__file__).resolve().parents[2]

SOURCE_MAIN_COMMIT = "b71ee1d6606dd41fcf24346e324c56e4407fd537"
SOURCE_TREE_SHA = "8a67c43ee6429c48c30e350b0ffd8f802c5c0ab0"

PROFILE_PATH = "conformance/AIFC-REPOSITORY-OBJECT-INDEX-PROFILE-v1.json"
PROFILE_ID = "AIFC-SAL-V1.12-REPOSITORY-OBJECT-INDEX-PROFILE-V1"
PROFILE_HASH = "7c0a0f9d05664dded7a4320854c5699e6371ebffca427b7fc3900a094bf832a0"

CLOSURE_PATH = "conformance/AIFC-LINEAGE-VERTEX-UNIVERSE-CLOSURE-v1.json"
CLOSURE_ID = "AIFC-SAL-V1.12-LINEAGE-VERTEX-UNIVERSE-CLOSURE-V1"
CLOSURE_HASH = "ff7fc0679a6de91f776e2def53e43005a138e531304c4b60f06774fb3184c388"
FINAL_VERTEX_UNIVERSE_HASH = "11dcf1039c7fc54248a7096eb74455fe9e3d1a030c884c74d5fa5c73e7306663"
VERTEX_DISCOVERY_MANIFEST_HASH = "a664f091f2e651758ff3e4ef771239b40b88cf8190fd2d522e19532467737ba5"

AUDIT_PATH = "conformance/AIFC-LINEAGE-VERTEX-UNIVERSE-CLOSURE-AUDIT-v1.json"
AUDIT_ID = "AIFC-SAL-V1.12-LINEAGE-VERTEX-UNIVERSE-CLOSURE-AUDIT-V1"
AUDIT_HASH = "63cc6733fce589ac380fb40858b60c9b529bd167436641aacc98bdbee438ddc3"

CLOSURE_IMPL_PATH = "reference/verifier/lineage_vertex_reference_closure_v1.py"
CLOSURE_IMPL_BLOB = "025e734deefc52bfca3ab385e75700c9fbc22235"
CLOSURE_IMPL_RAW_SHA256 = "e50206991042c59d0f740e1641bc430f1a5cbef06624252df618b77ea773e4bb"

class ScientificAssuranceLineageV112Error(ValueError):
    pass

@dataclass(frozen=True)
class LineageVertexUniverseClosureReport:
    question_id: str
    exact_tree_binding: str
    repository_object_index_derivation: str
    repository_object_index_completeness: str
    recognized_repository_object_count: int
    repository_object_index_hash: str
    seed_vertex_count: int
    final_vertex_count: int
    vertex_discovery_occurrence_count: int
    closure_monotonicity: str
    fixed_point: str
    reference_closure: str
    manifest_replay: str
    discovery_order_independence: str
    ambiguous_required_references: int
    unresolved_required_references: int
    final_vertex_universe_hash: str
    discovery_manifest_hash: str
    global_lineage_seed_completeness: str
    object_index_profile_global_adequacy: str
    global_repository_object_universe_completeness: str
    semantic_relation_universe_completeness: str
    derived_semantic_authority: str
    solver_invocation_count: int
    result: str
    blocked_subtype: str | None

def _load(path: str) -> Mapping[str, Any]:
    obj = loads_strict((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(obj, Mapping):
        raise ScientificAssuranceLineageV112Error("SAL_V112_OBJECT_NOT_MAPPING:" + path)
    return obj

def _verify_audit(audit: Mapping[str, Any], receipt: Mapping[str, Any],
                  profile: Mapping[str, Any], question_id: str) -> None:
    if (audit.get("schema") != "AIFC/lineage-vertex-universe-closure-audit/v1"
        or audit.get("audit_id") != AUDIT_ID):
        raise ScientificAssuranceLineageV112Error("SAL_V112_AUDIT_ID_REBINDING")
    material = dict(audit)
    claimed = material.pop("audit_content_hash", None)
    actual = domain_hash("AIFC:LINEAGE-VERTEX-UNIVERSE-CLOSURE-AUDIT:v1", material)
    if claimed != AUDIT_HASH or actual != AUDIT_HASH:
        raise ScientificAssuranceLineageV112Error("SAL_V112_AUDIT_CONTENT_REBINDING")
    if audit.get("entailment_question_id") != question_id:
        raise ScientificAssuranceLineageV112Error(
            "LINEAGE_VERTEX_UNIVERSE_AUDIT_QUESTION_CONTEXT_REBINDING"
        )
    if (audit.get("closure_id") != receipt.get("closure_id")
        or audit.get("closure_content_hash") != receipt.get("closure_content_hash")):
        raise ScientificAssuranceLineageV112Error("SAL_V112_AUDIT_CLOSURE_REFERENCE_REBINDING")
    if (audit.get("object_index_profile_id") != profile.get("object_index_profile_id")
        or audit.get("object_index_profile_content_hash") != profile.get("profile_content_hash")):
        raise ScientificAssuranceLineageV112Error("SAL_V112_AUDIT_PROFILE_REFERENCE_REBINDING")
    expected = {
        "exact_tree_binding": "CONFIRMED",
        "repository_object_index_derivation": "MACHINE_DERIVED_FROM_EXACT_TREE",
        "repository_object_index_completeness":
            "ESTABLISHED_ONLY_RELATIVE_TO_EXACT_TREE_AND_RECOGNIZED_OBJECT_PROFILE",
        "lineage_vertex_closure_monotonicity": "CONFIRMED",
        "lineage_vertex_fixed_point": "MACHINE_VERIFIED_BY_FINAL_REPLAY",
        "lineage_vertex_reference_closure": "ESTABLISHED_IN_TESTED_SCOPE_FROM_INHERITED_SEED",
        "vertex_discovery_manifest_replay": "CONFIRMED",
        "lineage_vertex_discovery_order_independence": "CONFIRMED_IN_TESTED_SCOPE",
        "lineage_required_vertex_universe_omission":
            "REJECTED_IN_TESTED_REFERENCE_CLOSURE_SCOPE",
        "global_lineage_seed_completeness": "NOT_ESTABLISHED",
        "object_index_profile_global_adequacy": "NOT_ESTABLISHED",
        "global_repository_object_universe_completeness": "NOT_ESTABLISHED",
        "lineage_semantic_relation_universe_completeness": "NOT_ESTABLISHED",
        "derived_semantic_authority": "BLOCKED",
        "status": "ESTABLISHED_IN_TESTED_SCOPE_FROM_INHERITED_SEED",
    }
    for field, value in expected.items():
        if audit.get(field) != value:
            raise ScientificAssuranceLineageV112Error("SAL_V112_AUDIT_FALSE_PROMOTION:" + field)
    if (audit.get("ambiguous_required_lineage_references") != 0
        or audit.get("unresolved_required_lineage_references") != 0
        or audit.get("solver_invocation_count") != 0):
        raise ScientificAssuranceLineageV112Error("SAL_V112_AUDIT_BLOCKER_OR_SOLVER_REBINDING")

def audit_lineage_vertex_universe_closure(
    predecessor_identity: str,
    target_profile_identity: str,
    entailment_question_identity: str,
) -> LineageVertexUniverseClosureReport:
    if (predecessor_identity, target_profile_identity, entailment_question_identity) != (
        v17.PREDECESSOR_ID, v17.TARGET_PROFILE_ID, v17.QUESTION_ID
    ):
        raise ScientificAssuranceLineageV112Error("ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION")

    inherited = v111u.audit_derived_semantic_lineage_edge_universe(
        predecessor_identity, target_profile_identity, entailment_question_identity
    )
    if (inherited.derived_semantic_authority != "BLOCKED"
        or inherited.solver_invocation_count != 0
        or inherited.vertex_universe_completeness != "NOT_ESTABLISHED"
        or inherited.semantic_relation_universe_completeness != "NOT_ESTABLISHED"):
        raise ScientificAssuranceLineageV112Error("SAL_V112_INHERITED_V111U_CEILING_REGRESSION")

    implementation_raw = (ROOT / CLOSURE_IMPL_PATH).read_bytes()
    if (git_blob_sha1_bytes(implementation_raw) != CLOSURE_IMPL_BLOB
        or hashlib.sha256(implementation_raw).hexdigest() != CLOSURE_IMPL_RAW_SHA256):
        raise ScientificAssuranceLineageV112Error("SAL_V112_CLOSURE_IMPLEMENTATION_REBINDING")

    profile = _load(PROFILE_PATH)
    closure.verify_profile(profile)
    if (profile.get("object_index_profile_id") != PROFILE_ID
        or profile.get("profile_content_hash") != PROFILE_HASH
        or profile.get("source_commit") != SOURCE_MAIN_COMMIT
        or profile.get("source_tree_sha") != SOURCE_TREE_SHA
        or profile.get("implementation_git_blob_sha1") != CLOSURE_IMPL_BLOB
        or profile.get("implementation_raw_sha256") != CLOSURE_IMPL_RAW_SHA256):
        raise ScientificAssuranceLineageV112Error("REPOSITORY_OBJECT_INDEX_PROFILE_REBINDING")

    receipt = _load(CLOSURE_PATH)
    if (receipt.get("closure_id") != CLOSURE_ID
        or receipt.get("closure_content_hash") != CLOSURE_HASH
        or receipt.get("entailment_question_id") != entailment_question_identity
        or receipt.get("object_index_profile_id") != PROFILE_ID
        or receipt.get("object_index_profile_content_hash") != PROFILE_HASH
        or receipt.get("source_lineage_edge_universe_id") != v111u.UNIVERSE_ID
        or receipt.get("source_lineage_edge_universe_content_hash") != v111u.UNIVERSE_HASH
        or receipt.get("source_lineage_edge_binding_id") != v111h.BINDING_ID
        or receipt.get("source_lineage_edge_binding_content_hash") != v111h.BINDING_HASH):
        raise ScientificAssuranceLineageV112Error("SAL_V112_CLOSURE_RECEIPT_REBINDING")

    source_binding = v111h._load(v111h.BINDING_PATH)
    index, result = closure.verify_closure_receipt(
        receipt, profile, source_binding,
        source_commit=SOURCE_MAIN_COMMIT,
        expected_tree_sha=SOURCE_TREE_SHA,
    )
    if (result.question_id != entailment_question_identity
        or result.final_vertex_universe_hash != FINAL_VERTEX_UNIVERSE_HASH
        or result.discovery_manifest_hash != VERTEX_DISCOVERY_MANIFEST_HASH
        or len(result.final_vertex_paths) != 11
        or len(result.discovery_manifest) != 31):
        raise ScientificAssuranceLineageV112Error("SAL_V112_CURRENT_INSTANCE_REBINDING")

    _verify_audit(_load(AUDIT_PATH), receipt, profile, entailment_question_identity)

    return LineageVertexUniverseClosureReport(
        question_id=entailment_question_identity,
        exact_tree_binding="CONFIRMED",
        repository_object_index_derivation="MACHINE_DERIVED_FROM_EXACT_TREE",
        repository_object_index_completeness=
            "ESTABLISHED_ONLY_RELATIVE_TO_EXACT_TREE_AND_RECOGNIZED_OBJECT_PROFILE",
        recognized_repository_object_count=len(index.vertices_by_path),
        repository_object_index_hash=index.index_hash,
        seed_vertex_count=receipt["seed_vertex_count"],
        final_vertex_count=len(result.final_vertex_paths),
        vertex_discovery_occurrence_count=len(result.discovery_manifest),
        closure_monotonicity="CONFIRMED",
        fixed_point="MACHINE_VERIFIED_BY_FINAL_REPLAY",
        reference_closure="ESTABLISHED_IN_TESTED_SCOPE_FROM_INHERITED_SEED",
        manifest_replay="CONFIRMED",
        discovery_order_independence="CONFIRMED_IN_TESTED_SCOPE",
        ambiguous_required_references=0,
        unresolved_required_references=0,
        final_vertex_universe_hash=result.final_vertex_universe_hash,
        discovery_manifest_hash=result.discovery_manifest_hash,
        global_lineage_seed_completeness="NOT_ESTABLISHED",
        object_index_profile_global_adequacy="NOT_ESTABLISHED",
        global_repository_object_universe_completeness="NOT_ESTABLISHED",
        semantic_relation_universe_completeness="NOT_ESTABLISHED",
        derived_semantic_authority="BLOCKED",
        solver_invocation_count=0,
        result=inherited.result,
        blocked_subtype=inherited.blocked_subtype,
    )
