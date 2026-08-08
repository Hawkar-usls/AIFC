#!/usr/bin/env python3
"""SAL v1.11h Derived Semantic Lineage Edge Binding.

This hardening layer preserves the v1.11 execution/authority separation and
adds exact edge identity over the already content-identified lineage vertices.
It does not authorize derived semantics and does not invoke the entailment
solver.
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
import semantic_lineage_edge_binding_v1 as edge

ROOT = Path(__file__).resolve().parents[2]

BINDING_PATH = "conformance/AIFC-DERIVED-SEMANTIC-LINEAGE-EDGE-BINDING-v1.json"
BINDING_ID = "AIFC-SAL-V1.11H-DERIVED-SEMANTIC-LINEAGE-EDGE-BINDING-V1"
BINDING_HASH = "42489c49e177f600317bc579fb0d875995216920cbb80327abe2091d2190bbd7"
LINEAGE_EDGE_SET_HASH = "80631fd7969f89f624bd5fa5dfdb94c7d3f5b2f80d399e7220e36c4e1dcb646a"
LINEAGE_GRAPH_IDENTITY = "33bb5817a88313926e0c4afc111b25414b31de8bbbfeb2e21aeb790b01402ff9"

AUDIT_PATH = "conformance/AIFC-DERIVED-SEMANTIC-LINEAGE-EDGE-AUDIT-v1.json"
AUDIT_ID = "AIFC-SAL-V1.11H-DERIVED-SEMANTIC-LINEAGE-EDGE-AUDIT-V1"
AUDIT_HASH = "041b187a106c03c47b6f614e3eadfff525472fd495dda026ae228babccc94d91"

SOURCE_MAIN_COMMIT = "847bc6487351ebd45f2ecd6bd5189f532eb99d8d"

EDGE_IMPL_PATH = "reference/verifier/semantic_lineage_edge_binding_v1.py"
EDGE_IMPL_BLOB = "62f08081aea5b13d54bd4170d1ece809e4fc3db4"
EDGE_IMPL_RAW_SHA256 = "4fe85150fe856159a21f9ebf4f516e51795dcc26b858dec66289d7dee23858c8"

class ScientificAssuranceLineageV111HError(ValueError):
    pass

@dataclass(frozen=True)
class DerivedSemanticLineageEdgeReport:
    question_id: str
    vertex_identity: str
    edge_identity: str
    semantic_projection_edge_binding: str
    whole_object_edge_binding: str
    required_edge_set_exactness: str
    lineage_graph_identity: str
    derived_semantic_authority: str
    solver_invocation_count: int
    result: str
    blocked_subtype: str | None

def _load(path: str) -> Mapping[str, Any]:
    obj = loads_strict((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(obj, Mapping):
        raise ScientificAssuranceLineageV111HError(f"SAL_V111H_OBJECT_NOT_MAPPING:{path}")
    return obj

def _objects_and_raws():
    paths = {
        "PROFILE": v111.DERIVATION_PROFILE_PATH,
        "PROOF": v111.PROOF_PATH,
        "MANIFEST": v111.MANIFEST_PATH,
        "GRAPH": v111.GRAPH_PATH,
        "DERIVED": v111.DERIVED_PATH,
        "QUESTION": "conformance/AIFC-ENTAILMENT-QUESTION-v1.json",
    }
    objects = {k:_load(p) for k,p in paths.items()}
    raws = {k:(ROOT/p).read_bytes() for k,p in paths.items()}
    return objects, raws

def _verify_audit_object(audit: Mapping[str, Any], binding: Mapping[str, Any]) -> None:
    if audit.get("schema") != "AIFC/derived-semantic-lineage-edge-audit/v1" or audit.get("audit_id") != AUDIT_ID:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_AUDIT_ID_REBINDING")
    material = dict(audit)
    claimed = material.pop("audit_content_hash", None)
    actual = domain_hash("AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-AUDIT:v1", material)
    if claimed != AUDIT_HASH or actual != AUDIT_HASH:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_AUDIT_CONTENT_REBINDING")
    if audit.get("lineage_edge_binding_id") != BINDING_ID or audit.get("lineage_edge_binding_content_hash") != binding.get("binding_content_hash"):
        raise ScientificAssuranceLineageV111HError("SAL_V111H_AUDIT_BINDING_REFERENCE_REBINDING")
    if audit.get("lineage_graph_identity") != binding.get("lineage_graph_identity"):
        raise ScientificAssuranceLineageV111HError("SAL_V111H_AUDIT_GRAPH_IDENTITY_REBINDING")
    if audit.get("derived_semantic_authority") != "BLOCKED" or audit.get("solver_invocation_count") != 0:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_AUTHORITY_OR_SOLVER_FALSE_PROMOTION")

def audit_derived_semantic_lineage_edge_binding(
    predecessor_identity: str,
    target_profile_identity: str,
    entailment_question_identity: str,
) -> DerivedSemanticLineageEdgeReport:
    if (predecessor_identity,target_profile_identity,entailment_question_identity) != (
        v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID
    ):
        raise ScientificAssuranceLineageV111HError("ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION")

    inherited = v111.audit_derived_semantic_lineage(
        predecessor_identity,target_profile_identity,entailment_question_identity
    )
    if inherited.solver_invocation_count != 0 or inherited.derived_semantic_authority != "BLOCKED":
        raise ScientificAssuranceLineageV111HError("SAL_V111H_INHERITED_AUTHORITY_CEILING_REGRESSION")

    edge_raw = (ROOT / EDGE_IMPL_PATH).read_bytes()
    if git_blob_sha1_bytes(edge_raw) != EDGE_IMPL_BLOB or hashlib.sha256(edge_raw).hexdigest() != EDGE_IMPL_RAW_SHA256:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_EDGE_EXECUTION_IMPLEMENTATION_REBINDING")

    binding = _load(BINDING_PATH)
    if binding.get("lineage_edge_binding_id") != BINDING_ID:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_BINDING_ID_REBINDING")
    if binding.get("source_main_commit") != SOURCE_MAIN_COMMIT:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_SOURCE_MAIN_REBINDING")
    if binding.get("binding_content_hash") != BINDING_HASH:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_BINDING_CONTENT_IDENTITY_REBINDING")
    objects, raws = _objects_and_raws()
    vertices, edges, graph_id = edge.verify_binding_receipt(binding, objects, raws)
    if len(vertices) != 6 or len(edges) != 9:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_VERTEX_OR_EDGE_COUNT_REBINDING")
    if binding.get("lineage_edge_set_hash") != LINEAGE_EDGE_SET_HASH or graph_id != LINEAGE_GRAPH_IDENTITY:
        raise ScientificAssuranceLineageV111HError("SAL_V111H_LINEAGE_GRAPH_IDENTITY_REBINDING")

    audit = _load(AUDIT_PATH)
    _verify_audit_object(audit,binding)

    return DerivedSemanticLineageEdgeReport(
        question_id=entailment_question_identity,
        vertex_identity="ESTABLISHED_IN_V1_11_TESTED_SCOPE",
        edge_identity="ESTABLISHED_IN_TESTED_SCOPE",
        semantic_projection_edge_binding="CONFIRMED_IN_TESTED_SCOPE",
        whole_object_edge_binding="CONFIRMED_IN_TESTED_SCOPE",
        required_edge_set_exactness="CONFIRMED_9_OF_9",
        lineage_graph_identity=graph_id,
        derived_semantic_authority="BLOCKED",
        solver_invocation_count=0,
        result=inherited.result,
        blocked_subtype=inherited.blocked_subtype,
    )
