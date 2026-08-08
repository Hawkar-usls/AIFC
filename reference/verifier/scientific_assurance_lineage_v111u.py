#!/usr/bin/env python3
"""SAL v1.11u Lineage Edge Universe Derivation Closure.

Derives the complete cross-vertex identity-reference edge universe inside the exact
inherited v1.11h six-vertex scope. It closes receipt/audit question-context binding,
but does not claim completeness of the vertex universe, general semantic-relation
completeness, derivation-profile authority, or derived semantic authority.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping
from canonical import domain_hash, loads_strict
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v111 as v111
import scientific_assurance_lineage_v111h as v111h
import semantic_lineage_edge_binding_v1 as parent_edge
import semantic_lineage_edge_universe_v1 as universe

ROOT = Path(__file__).resolve().parents[2]

PROFILE_PATH = "conformance/AIFC-LINEAGE-EDGE-UNIVERSE-DERIVATION-PROFILE-v1.json"
PROFILE_ID = "AIFC-SAL-V1.11U-LINEAGE-EDGE-UNIVERSE-DERIVATION-PROFILE-V1"
PROFILE_HASH = "4a1591a945d5bad4bed0c8fbd6fdf7c90ad45df2240d7c59639e5edca271f20f"
UNIVERSE_PATH = "conformance/AIFC-DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-v1.json"
UNIVERSE_ID = "AIFC-SAL-V1.11U-DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-V1"
UNIVERSE_CONTENT_HASH = "fed9f7134eeb714ccdabefeada3d744a8ec2c478cd1cf4acf8fd43068a94522d"
EDGE_UNIVERSE_HASH = "eca830e62f0e13fdd49b9630bc56c5d40796ec9c3d3af6b4975503260788e87a"
AUDIT_PATH = "conformance/AIFC-DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-AUDIT-v1.json"
AUDIT_ID = "AIFC-SAL-V1.11U-DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-AUDIT-V1"
AUDIT_HASH = "09d47efb47d17c2e2912629685471a6876d2a1822cdea6c93dac91cde5da19d2"
SOURCE_MAIN_COMMIT = "367dc30f53365225157dfb77e45fe6ef9ba027c8"

PARENT_BINDING_BLOB = "c5ccf513f826aae2e1115b65475f489f40232486"
PARENT_BINDING_HASH = "42489c49e177f600317bc579fb0d875995216920cbb80327abe2091d2190bbd7"
PARENT_AUDIT_BLOB = "30ec3fa8d0060cac107dfc668b86710ab5ed2b17"
PARENT_AUDIT_HASH = "041b187a106c03c47b6f614e3eadfff525472fd495dda026ae228babccc94d91"

UNIVERSE_IMPL_PATH = "reference/verifier/semantic_lineage_edge_universe_v1.py"
UNIVERSE_IMPL_BLOB = "b3688aaa0e268321f3c8288253532db8c3eb6161"
UNIVERSE_IMPL_RAW_SHA256 = "ed8437241d1077a273a1530e04b4ed238bb93162ebb36d81c88cf2f865632937"

class ScientificAssuranceLineageV111UError(ValueError):
    pass

@dataclass(frozen=True)
class LineageEdgeUniverseReport:
    question_id: str
    inherited_declared_edge_count: int
    machine_derived_edge_count: int
    additional_derived_edge_count: int
    edge_universe_independent_derivation: str
    edge_universe_completeness: str
    binding_question_context: str
    audit_question_context: str
    edge_universe_derivation_profile_authority: str
    lineage_vertex_universe_completeness: str
    lineage_semantic_relation_universe_general: str
    derived_semantic_authority: str
    solver_invocation_count: int
    result: str
    blocked_subtype: str | None

def _load(path: str) -> Mapping[str, Any]:
    obj = loads_strict((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(obj, Mapping):
        raise ScientificAssuranceLineageV111UError(f"SAL_V111U_OBJECT_NOT_MAPPING:{path}")
    return obj

def _content_hash(obj: Mapping[str, Any], field: str, domain: str) -> str:
    material = dict(obj)
    material.pop(field, None)
    return domain_hash(domain, material)


def assert_question_context_objects(
    parent_binding: Mapping[str, Any],
    parent_audit: Mapping[str, Any],
    universe_receipt: Mapping[str, Any],
    universe_audit: Mapping[str, Any],
    question_id: str,
) -> None:
    checks = (
        ("LINEAGE_BINDING_QUESTION_CONTEXT_REBINDING", parent_binding.get("entailment_question_id")),
        ("LINEAGE_AUDIT_QUESTION_CONTEXT_REBINDING", parent_audit.get("entailment_question_id")),
        ("LINEAGE_UNIVERSE_QUESTION_CONTEXT_REBINDING", universe_receipt.get("entailment_question_id")),
        ("LINEAGE_UNIVERSE_AUDIT_QUESTION_CONTEXT_REBINDING", universe_audit.get("entailment_question_id")),
    )
    for error, value in checks:
        if value != question_id:
            raise ScientificAssuranceLineageV111UError(error)

def _verify_impl() -> None:
    raw = (ROOT / UNIVERSE_IMPL_PATH).read_bytes()
    if git_blob_sha1_bytes(raw) != UNIVERSE_IMPL_BLOB:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_UNIVERSE_IMPLEMENTATION_GIT_REBINDING")
    if hashlib.sha256(raw).hexdigest() != UNIVERSE_IMPL_RAW_SHA256:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_UNIVERSE_IMPLEMENTATION_RAW_REBINDING")

def _verify_parent_question_context(question_id: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    binding_raw = (ROOT / v111h.BINDING_PATH).read_bytes()
    audit_raw = (ROOT / v111h.AUDIT_PATH).read_bytes()
    if git_blob_sha1_bytes(binding_raw) != PARENT_BINDING_BLOB:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_PARENT_BINDING_GIT_REBINDING")
    if git_blob_sha1_bytes(audit_raw) != PARENT_AUDIT_BLOB:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_PARENT_AUDIT_GIT_REBINDING")
    binding = _load(v111h.BINDING_PATH)
    audit = _load(v111h.AUDIT_PATH)
    if binding.get("binding_content_hash") != PARENT_BINDING_HASH or parent_edge.binding_content_hash(binding) != PARENT_BINDING_HASH:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_PARENT_BINDING_CONTENT_REBINDING")
    if audit.get("audit_content_hash") != PARENT_AUDIT_HASH or _content_hash(audit,"audit_content_hash","AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-AUDIT:v1") != PARENT_AUDIT_HASH:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_PARENT_AUDIT_CONTENT_REBINDING")
    if binding.get("entailment_question_id") != question_id:
        raise ScientificAssuranceLineageV111UError("LINEAGE_BINDING_QUESTION_CONTEXT_REBINDING")
    if audit.get("entailment_question_id") != question_id:
        raise ScientificAssuranceLineageV111UError("LINEAGE_AUDIT_QUESTION_CONTEXT_REBINDING")
    return binding, audit

def _verify_profile() -> Mapping[str, Any]:
    profile = _load(PROFILE_PATH)
    if profile.get("profile_id") != PROFILE_ID or profile.get("profile_content_hash") != PROFILE_HASH:
        raise ScientificAssuranceLineageV111UError("EDGE_UNIVERSE_DERIVATION_PROFILE_REBINDING")
    if universe.profile_content_hash(profile) != PROFILE_HASH:
        raise ScientificAssuranceLineageV111UError("EDGE_UNIVERSE_DERIVATION_PROFILE_CONTENT_REBINDING")
    if profile.get("execution_implementation_git_blob_sha1") != UNIVERSE_IMPL_BLOB or profile.get("execution_implementation_raw_sha256") != UNIVERSE_IMPL_RAW_SHA256:
        raise ScientificAssuranceLineageV111UError("EDGE_UNIVERSE_DERIVATION_PROFILE_EXECUTION_REBINDING")
    return profile

def _verify_audit(audit: Mapping[str, Any], receipt: Mapping[str, Any], question_id: str) -> None:
    if audit.get("schema") != "AIFC/derived-semantic-lineage-edge-universe-audit/v1" or audit.get("audit_id") != AUDIT_ID:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_AUDIT_ID_REBINDING")
    if audit.get("audit_content_hash") != AUDIT_HASH or _content_hash(audit,"audit_content_hash","AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-AUDIT:v1") != AUDIT_HASH:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_AUDIT_CONTENT_REBINDING")
    if audit.get("entailment_question_id") != question_id:
        raise ScientificAssuranceLineageV111UError("LINEAGE_UNIVERSE_AUDIT_QUESTION_CONTEXT_REBINDING")
    if audit.get("edge_universe_id") != receipt.get("universe_id") or audit.get("edge_universe_content_hash") != receipt.get("universe_content_hash"):
        raise ScientificAssuranceLineageV111UError("LINEAGE_UNIVERSE_AUDIT_RECEIPT_REBINDING")
    if audit.get("edge_universe_hash") != receipt.get("edge_universe_hash"):
        raise ScientificAssuranceLineageV111UError("LINEAGE_UNIVERSE_AUDIT_HASH_REBINDING")
    if audit.get("derived_semantic_authority") != "BLOCKED" or audit.get("solver_invocation_count") != 0:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_AUTHORITY_OR_SOLVER_FALSE_PROMOTION")

def audit_lineage_edge_universe_derivation(
    predecessor_identity: str,
    target_profile_identity: str,
    entailment_question_identity: str,
) -> LineageEdgeUniverseReport:
    if (predecessor_identity,target_profile_identity,entailment_question_identity) != (v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID):
        raise ScientificAssuranceLineageV111UError("ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION")

    inherited = v111h.audit_derived_semantic_lineage_edge_binding(
        predecessor_identity,target_profile_identity,entailment_question_identity
    )
    if inherited.derived_semantic_authority != "BLOCKED" or inherited.solver_invocation_count != 0:
        raise ScientificAssuranceLineageV111UError("SAL_V111U_INHERITED_AUTHORITY_CEILING_REGRESSION")

    _verify_impl()
    parent_binding, _ = _verify_parent_question_context(entailment_question_identity)
    profile = _verify_profile()
    objects, _raws = v111h._objects_and_raws()

    receipt = _load(UNIVERSE_PATH)
    if receipt.get("universe_id") != UNIVERSE_ID or receipt.get("universe_content_hash") != UNIVERSE_CONTENT_HASH:
        raise ScientificAssuranceLineageV111UError("LINEAGE_EDGE_UNIVERSE_RECEIPT_IDENTITY_REBINDING")
    if receipt.get("source_main_commit") != SOURCE_MAIN_COMMIT:
        raise ScientificAssuranceLineageV111UError("LINEAGE_EDGE_UNIVERSE_SOURCE_MAIN_REBINDING")
    if receipt.get("entailment_question_id") != entailment_question_identity:
        raise ScientificAssuranceLineageV111UError("LINEAGE_UNIVERSE_QUESTION_CONTEXT_REBINDING")
    if receipt.get("parent_edge_binding_id") != v111h.BINDING_ID or receipt.get("parent_edge_binding_content_hash") != PARENT_BINDING_HASH or receipt.get("parent_edge_binding_git_blob_sha1") != PARENT_BINDING_BLOB:
        raise ScientificAssuranceLineageV111UError("LINEAGE_EDGE_UNIVERSE_PARENT_BINDING_REBINDING")

    derived, uh = universe.verify_universe_receipt(receipt, objects, profile)
    if uh != EDGE_UNIVERSE_HASH:
        raise ScientificAssuranceLineageV111UError("LINEAGE_EDGE_UNIVERSE_IDENTITY_REBINDING")

    parent_pairs = {(str(e.get("source_vertex_key")),str(e.get("target_vertex_key"))) for e in parent_binding.get("edges",[])}
    derived_pairs = {(str(e["source_vertex_key"]),str(e["target_vertex_key"])) for e in derived}
    if not parent_pairs.issubset(derived_pairs):
        raise ScientificAssuranceLineageV111UError("INHERITED_EDGE_NOT_PRESENT_IN_MACHINE_DERIVED_UNIVERSE")
    additional = derived_pairs - parent_pairs
    if len(parent_pairs) != 9 or len(derived) != 15 or len(additional) != 6:
        raise ScientificAssuranceLineageV111UError("LINEAGE_EDGE_UNIVERSE_EXPECTED_CURRENT_INSTANCE_CARDINALITY_REBINDING")

    audit = _load(AUDIT_PATH)
    _verify_audit(audit,receipt,entailment_question_identity)
    assert_question_context_objects(parent_binding,_load(v111h.AUDIT_PATH),receipt,audit,entailment_question_identity)

    return LineageEdgeUniverseReport(
        question_id=entailment_question_identity,
        inherited_declared_edge_count=len(parent_pairs),
        machine_derived_edge_count=len(derived),
        additional_derived_edge_count=len(additional),
        edge_universe_independent_derivation="CONFIRMED_IN_TESTED_CANDIDATE_SCOPE",
        edge_universe_completeness="CONFIRMED_WITHIN_INHERITED_SIX_VERTEX_IDENTITY_REFERENCE_SCOPE",
        binding_question_context="CONFIRMED",
        audit_question_context="CONFIRMED",
        edge_universe_derivation_profile_authority="NOT_ESTABLISHED_SUCCESSOR_CANDIDATE",
        lineage_vertex_universe_completeness="NOT_ESTABLISHED",
        lineage_semantic_relation_universe_general="NOT_ESTABLISHED",
        derived_semantic_authority="BLOCKED",
        solver_invocation_count=0,
        result=inherited.result,
        blocked_subtype=inherited.blocked_subtype,
    )
