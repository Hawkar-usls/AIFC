#!/usr/bin/env python3
"""SAL v1.11u Derived Semantic Lineage Edge Universe Closure.

This hardening layer preserves the exact v1.11h vertex/edge milestone and
recomputes the required cross-vertex identity-reference universe from the
bound vertex contents instead of accepting a successor-written edge list.
The theorem is explicitly relative to the inherited six-vertex scope.
Derived semantic authority remains blocked and the entailment solver remains
uninvoked.
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
import semantic_lineage_edge_universe_v1 as universe

ROOT = Path(__file__).resolve().parents[2]

UNIVERSE_PATH = "conformance/AIFC-DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-v1.json"
UNIVERSE_ID = "AIFC-SAL-V1.11U-DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-V1"
UNIVERSE_HASH = "0e83cc64745288a60c271c5fcb3088de0ecde622d58ae2b08c8da36de5bc15d6"
LINEAGE_EDGE_UNIVERSE_HASH = "4960bc1c150f4dd14dd9e605449dfa4878d99d6a62ccdf8851fca564c513bb67"
LINEAGE_GRAPH_IDENTITY_V2 = "c8c1e89cbc90792181a2e5a59510a0ae41a0436f8c5844c55e6a90a6e4cfbc8a"

AUDIT_PATH = "conformance/AIFC-DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-AUDIT-v1.json"
AUDIT_ID = "AIFC-SAL-V1.11U-DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-AUDIT-V1"
AUDIT_HASH = "1b1f8f14bbc4b5f369804bc08aad7d44605d461402a444d18e212fba0830ff8c"

SOURCE_MAIN_COMMIT = "367dc30f53365225157dfb77e45fe6ef9ba027c8"

UNIVERSE_IMPL_PATH = "reference/verifier/semantic_lineage_edge_universe_v1.py"
UNIVERSE_IMPL_BLOB = "ae172215eedfb71b7b71fb1e613b3f0e5a6d987a"
UNIVERSE_IMPL_RAW_SHA256 = "8388c1a8d96ec8c90bea76e3aae9aec48e9c040fc599a590aa3f27f022efbfcf"

class ScientificAssuranceLineageV111UError(ValueError):
    pass

@dataclass(frozen=True)
class DerivedSemanticLineageEdgeUniverseReport:
    question_id: str
    vertex_scope: str
    edge_universe_derivation: str
    edge_universe_completeness: str
    derived_edge_count: int
    inherited_declared_edge_count: int
    newly_derived_edge_count: int
    binding_question_context: str
    audit_question_context: str
    lineage_graph_identity_v2: str
    vertex_universe_completeness: str
    semantic_relation_universe_completeness: str
    derived_semantic_authority: str
    solver_invocation_count: int
    result: str
    blocked_subtype: str | None

def _load(path: str) -> Mapping[str, Any]:
    obj = loads_strict((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(obj, Mapping):
        raise ScientificAssuranceLineageV111UError(
            f"SAL_V111U_OBJECT_NOT_MAPPING:{path}"
        )
    return obj

def _verify_audit_object(
    audit: Mapping[str, Any],
    receipt: Mapping[str, Any],
    question_id: str,
) -> None:
    if (
        audit.get("schema")
        != "AIFC/derived-semantic-lineage-edge-universe-audit/v1"
        or audit.get("audit_id") != AUDIT_ID
    ):
        raise ScientificAssuranceLineageV111UError("SAL_V111U_AUDIT_ID_REBINDING")
    material = dict(audit)
    claimed = material.pop("audit_content_hash", None)
    actual = domain_hash(
        "AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-AUDIT:v1",
        material,
    )
    if claimed != AUDIT_HASH or actual != AUDIT_HASH:
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_AUDIT_CONTENT_REBINDING"
        )
    if audit.get("entailment_question_id") != question_id:
        raise ScientificAssuranceLineageV111UError(
            "LINEAGE_UNIVERSE_AUDIT_QUESTION_CONTEXT_REBINDING"
        )
    if (
        audit.get("edge_universe_id") != UNIVERSE_ID
        or audit.get("edge_universe_content_hash")
        != receipt.get("universe_content_hash")
    ):
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_AUDIT_UNIVERSE_REFERENCE_REBINDING"
        )
    if (
        audit.get("source_lineage_edge_binding_id")
        != receipt.get("source_lineage_edge_binding_id")
        or audit.get("source_lineage_edge_binding_content_hash")
        != receipt.get("source_lineage_edge_binding_content_hash")
    ):
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_AUDIT_SOURCE_BINDING_REBINDING"
        )
    if (
        audit.get("vertex_scope") != universe.VERTEX_SCOPE
        or audit.get("vertex_scope_count") != receipt.get("vertex_scope_count")
        or audit.get("derived_edge_count") != receipt.get("derived_edge_count")
        or audit.get("inherited_declared_edge_count")
        != len(receipt.get("inherited_declared_edge_pairs", []))
        or audit.get("newly_derived_edge_count")
        != len(receipt.get("newly_derived_edge_pairs", []))
    ):
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_AUDIT_COUNT_OR_SCOPE_REBINDING"
        )
    if (
        audit.get("lineage_edge_universe_hash")
        != receipt.get("lineage_edge_universe_hash")
        or audit.get("lineage_graph_identity_v2")
        != receipt.get("lineage_graph_identity_v2")
    ):
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_AUDIT_GRAPH_IDENTITY_REBINDING"
        )
    if (
        audit.get("edge_universe_derivation")
        != "ESTABLISHED_IN_TESTED_SCOPE_RELATIVE_TO_BOUND_VERTEX_SET"
        or audit.get("edge_universe_completeness")
        != "ESTABLISHED_IN_TESTED_SCOPE_RELATIVE_TO_BOUND_VERTEX_SET"
        or audit.get("binding_question_context")
        != "EXPLICITLY_CLOSED_IN_TESTED_SCOPE"
        or audit.get("audit_question_context")
        != "EXPLICITLY_CLOSED_IN_TESTED_SCOPE"
        or audit.get("vertex_universe_completeness") != "NOT_ESTABLISHED"
        or audit.get("semantic_relation_universe_completeness")
        != "NOT_ESTABLISHED"
    ):
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_AUDIT_FALSE_CLOSURE_PROMOTION"
        )
    if (
        audit.get("derived_semantic_authority") != "BLOCKED"
        or audit.get("solver_invocation_count") != 0
        or audit.get("status") != "ESTABLISHED_IN_TESTED_SCOPE"
    ):
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_AUTHORITY_OR_SOLVER_FALSE_PROMOTION"
        )

def audit_derived_semantic_lineage_edge_universe(
    predecessor_identity: str,
    target_profile_identity: str,
    entailment_question_identity: str,
) -> DerivedSemanticLineageEdgeUniverseReport:
    if (
        predecessor_identity,
        target_profile_identity,
        entailment_question_identity,
    ) != (v17.PREDECESSOR_ID, v17.TARGET_PROFILE_ID, v17.QUESTION_ID):
        raise ScientificAssuranceLineageV111UError(
            "ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION"
        )

    inherited = v111h.audit_derived_semantic_lineage_edge_binding(
        predecessor_identity,
        target_profile_identity,
        entailment_question_identity,
    )
    if (
        inherited.solver_invocation_count != 0
        or inherited.derived_semantic_authority != "BLOCKED"
        or inherited.edge_identity != "ESTABLISHED_IN_TESTED_SCOPE"
    ):
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_INHERITED_V111H_CEILING_REGRESSION"
        )

    implementation_raw = (ROOT / UNIVERSE_IMPL_PATH).read_bytes()
    if (
        git_blob_sha1_bytes(implementation_raw) != UNIVERSE_IMPL_BLOB
        or hashlib.sha256(implementation_raw).hexdigest()
        != UNIVERSE_IMPL_RAW_SHA256
    ):
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_UNIVERSE_IMPLEMENTATION_REBINDING"
        )

    receipt = _load(UNIVERSE_PATH)
    if receipt.get("edge_universe_id") != UNIVERSE_ID:
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_UNIVERSE_ID_REBINDING"
        )
    if receipt.get("source_main_commit") != SOURCE_MAIN_COMMIT:
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_SOURCE_MAIN_REBINDING"
        )
    if receipt.get("universe_content_hash") != UNIVERSE_HASH:
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_UNIVERSE_CONTENT_IDENTITY_REBINDING"
        )

    objects, raws = v111h._objects_and_raws()
    source_binding = v111h._load(v111h.BINDING_PATH)
    source_audit = v111h._load(v111h.AUDIT_PATH)
    vertices, edges, graph_id = universe.verify_universe_receipt(
        receipt,
        source_binding,
        source_audit,
        objects,
        raws,
    )
    if receipt.get("lineage_edge_universe_hash") != LINEAGE_EDGE_UNIVERSE_HASH:
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_EDGE_UNIVERSE_HASH_REBINDING"
        )
    if graph_id != LINEAGE_GRAPH_IDENTITY_V2:
        raise ScientificAssuranceLineageV111UError(
            "SAL_V111U_LINEAGE_GRAPH_IDENTITY_REBINDING"
        )

    audit = _load(AUDIT_PATH)
    _verify_audit_object(audit, receipt, entailment_question_identity)

    return DerivedSemanticLineageEdgeUniverseReport(
        question_id=entailment_question_identity,
        vertex_scope=universe.VERTEX_SCOPE,
        edge_universe_derivation=(
            "ESTABLISHED_IN_TESTED_SCOPE_RELATIVE_TO_BOUND_VERTEX_SET"
        ),
        edge_universe_completeness=(
            "ESTABLISHED_IN_TESTED_SCOPE_RELATIVE_TO_BOUND_VERTEX_SET"
        ),
        derived_edge_count=len(edges),
        inherited_declared_edge_count=len(
            receipt["inherited_declared_edge_pairs"]
        ),
        newly_derived_edge_count=len(receipt["newly_derived_edge_pairs"]),
        binding_question_context="EXPLICITLY_CLOSED_IN_TESTED_SCOPE",
        audit_question_context="EXPLICITLY_CLOSED_IN_TESTED_SCOPE",
        lineage_graph_identity_v2=graph_id,
        vertex_universe_completeness="NOT_ESTABLISHED",
        semantic_relation_universe_completeness="NOT_ESTABLISHED",
        derived_semantic_authority="BLOCKED",
        solver_invocation_count=0,
        result=inherited.result,
        blocked_subtype=inherited.blocked_subtype,
    )
