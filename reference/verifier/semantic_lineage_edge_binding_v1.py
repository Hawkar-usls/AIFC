#!/usr/bin/env python3
"""SAL v1.11h lineage-edge binding.

This module proves identity of the traversed lineage edges between the already
content-identified v1.11 vertices. It deliberately makes no semantic-authority
decision.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from canonical import domain_hash, loads_strict
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import semantic_derivation_replay_v1 as replay

EDGE_SET_DOMAIN = "AIFC:DERIVED-SEMANTIC-LINEAGE-EDGES:v1"
LINEAGE_GRAPH_DOMAIN = "AIFC:DERIVED-SEMANTIC-LINEAGE-GRAPH:v1"
BINDING_DOMAIN = "AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-BINDING:v1"

VERTEX_KEYS = ("PROFILE","PROOF","MANIFEST","GRAPH","DERIVED","QUESTION")

@dataclass(frozen=True)
class EdgeSpec:
    edge_id: str
    source_key: str
    target_key: str
    source_id_field: str
    source_whole_hash_field: str | None = None
    source_projection_hash_field: str | None = None

EDGE_SPECS = (
    EdgeSpec("PROOF_TO_PROFILE","PROOF","PROFILE","derivation_profile_id","derivation_profile_content_hash"),
    EdgeSpec("PROOF_TO_MANIFEST","PROOF","MANIFEST","declared_leaf_manifest_id",None,"declared_leaf_manifest_hash"),
    EdgeSpec("PROOF_TO_DEPENDENCY_GRAPH","PROOF","GRAPH","declared_dependency_graph_id",None,"declared_dependency_graph_hash"),
    EdgeSpec("MANIFEST_TO_PROFILE","MANIFEST","PROFILE","derivation_profile_id"),
    EdgeSpec("GRAPH_TO_QUESTION","GRAPH","QUESTION","entailment_question_id"),
    EdgeSpec("DERIVED_TO_PROFILE","DERIVED","PROFILE","derivation_profile_id","derivation_profile_content_hash"),
    EdgeSpec("DERIVED_TO_PROOF","DERIVED","PROOF","derivation_proof_id","derivation_proof_content_hash"),
    EdgeSpec("DERIVED_TO_MANIFEST","DERIVED","MANIFEST","canonical_leaf_manifest_id",None,"canonical_leaf_manifest_hash"),
    EdgeSpec("DERIVED_TO_DEPENDENCY_GRAPH","DERIVED","GRAPH","canonical_dependency_graph_id",None,"canonical_dependency_graph_hash"),
)
REQUIRED_EDGE_IDS = tuple(x.edge_id for x in EDGE_SPECS)

class SemanticLineageEdgeBindingV1Error(ValueError):
    pass

def binding_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj)
    material.pop("binding_content_hash", None)
    return domain_hash(BINDING_DOMAIN, material)

def _raw_identity(raw: bytes) -> tuple[str,str]:
    return git_blob_sha1_bytes(raw), hashlib.sha256(raw).hexdigest()

def _vertex(
    key: str,
    obj: Mapping[str, Any],
    raw: bytes,
    *,
    source_path: str,
    schema_id: str,
    id_field: str,
    whole_hash_field: str | None,
    projection_hash_field: str | None,
) -> Mapping[str, Any]:
    if obj.get("schema") != schema_id:
        raise SemanticLineageEdgeBindingV1Error(f"LINEAGE_VERTEX_SCHEMA_REBINDING:{key}")
    oid = obj.get(id_field)
    if not isinstance(oid, str) or not oid:
        raise SemanticLineageEdgeBindingV1Error(f"LINEAGE_VERTEX_OBJECT_ID_INVALID:{key}")
    whole = obj.get(whole_hash_field) if whole_hash_field else None
    projection = obj.get(projection_hash_field) if projection_hash_field else None
    if whole is not None and (not isinstance(whole,str) or len(whole) != 64):
        raise SemanticLineageEdgeBindingV1Error(f"LINEAGE_VERTEX_WHOLE_CONTENT_HASH_INVALID:{key}")
    if projection is not None and (not isinstance(projection,str) or len(projection) != 64):
        raise SemanticLineageEdgeBindingV1Error(f"LINEAGE_VERTEX_SEMANTIC_PROJECTION_HASH_INVALID:{key}")
    blob, raw_sha = _raw_identity(raw)
    return {
        "vertex_key":key,
        "schema_id":schema_id,
        "object_id":oid,
        "source_path":source_path,
        "git_blob_sha1":blob,
        "raw_sha256":raw_sha,
        "whole_object_content_hash":whole,
        "semantic_projection_hash":projection,
    }

def build_vertices(objects: Mapping[str, Mapping[str, Any]], raws: Mapping[str, bytes]) -> tuple[Mapping[str,Any], ...]:
    p = objects["PROFILE"]; proof = objects["PROOF"]; manifest = objects["MANIFEST"]
    graph = objects["GRAPH"]; derived = objects["DERIVED"]; question = objects["QUESTION"]

    # Bind the logical object used by edge replay to the exact bytes whose
    # Git/raw identities become the vertex identity.
    for key in VERTEX_KEYS:
        try:
            parsed = loads_strict(raws[key].decode("utf-8"))
        except Exception as exc:
            raise SemanticLineageEdgeBindingV1Error(f"LINEAGE_VERTEX_RAW_BYTES_INVALID:{key}") from exc
        if parsed != objects[key]:
            raise SemanticLineageEdgeBindingV1Error(f"LINEAGE_VERTEX_BYTES_TO_OBJECT_REBINDING:{key}")

    # Verify internal content identities before they can become lineage vertices.
    if p.get("profile_content_hash") != replay.profile_content_hash(p):
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_VERTEX_PROFILE_CONTENT_REBINDING")
    if proof.get("proof_content_hash") != replay.proof_content_hash(proof):
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_VERTEX_PROOF_CONTENT_REBINDING")
    if manifest.get("manifest_content_hash") != replay.manifest_content_hash(manifest):
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_VERTEX_MANIFEST_CONTENT_REBINDING")
    if graph.get("graph_content_hash") != replay.graph_content_hash(graph):
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_VERTEX_GRAPH_CONTENT_REBINDING")
    if derived.get("derivation_content_hash") != replay.derived_content_hash(derived):
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_VERTEX_DERIVED_CONTENT_REBINDING")
    qid = question.get("question_id")
    if not isinstance(qid,str) or len(qid) != 64:
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_VERTEX_QUESTION_ID_INVALID")

    vertices = (
        _vertex("PROFILE",p,raws["PROFILE"],source_path="conformance/AIFC-SEMANTIC-DERIVATION-PROFILE-v1.json",
                schema_id="AIFC/semantic-derivation-profile/v1",id_field="derivation_profile_id",
                whole_hash_field="profile_content_hash",projection_hash_field=None),
        _vertex("PROOF",proof,raws["PROOF"],source_path="conformance/AIFC-SEMANTIC-DERIVATION-PROOF-v1.json",
                schema_id="AIFC/semantic-derivation-proof/v1",id_field="derivation_proof_id",
                whole_hash_field="proof_content_hash",projection_hash_field=None),
        _vertex("MANIFEST",manifest,raws["MANIFEST"],source_path="conformance/AIFC-DERIVATION-LEAF-MANIFEST-v1.json",
                schema_id="AIFC/derivation-leaf-manifest/v1",id_field="manifest_id",
                whole_hash_field="manifest_content_hash",projection_hash_field="leaf_manifest_hash"),
        _vertex("GRAPH",graph,raws["GRAPH"],source_path="conformance/AIFC-CANONICAL-SEMANTIC-DEPENDENCY-GRAPH-v1.json",
                schema_id="AIFC/canonical-semantic-dependency-graph/v1",id_field="graph_id",
                whole_hash_field="graph_content_hash",projection_hash_field="dependency_graph_hash"),
        _vertex("DERIVED",derived,raws["DERIVED"],source_path="conformance/AIFC-BRIDGE-DERIVED-SEMANTIC-OBJECT-v2.json",
                schema_id="AIFC/bridge-derived-semantic-object/v2",id_field="derived_semantic_object_id",
                whole_hash_field="derivation_content_hash",projection_hash_field=None),
        _vertex("QUESTION",question,raws["QUESTION"],source_path="conformance/AIFC-ENTAILMENT-QUESTION-v1.json",
                schema_id="AIFC/entailment-question/v1",id_field="question_id",
                whole_hash_field=None,projection_hash_field="question_id"),
    )
    return vertices

def build_edges(objects: Mapping[str, Mapping[str, Any]], vertices: Sequence[Mapping[str,Any]]) -> tuple[Mapping[str,Any], ...]:
    vmap = {v["vertex_key"]:v for v in vertices}
    if set(vmap) != set(VERTEX_KEYS):
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_VERTEX_SET_REBINDING")
    out=[]
    for spec in EDGE_SPECS:
        source = objects[spec.source_key]
        target = vmap[spec.target_key]
        did = source.get(spec.source_id_field)
        dwhole = source.get(spec.source_whole_hash_field) if spec.source_whole_hash_field else None
        dproj = source.get(spec.source_projection_hash_field) if spec.source_projection_hash_field else None

        if did != target["object_id"]:
            raise SemanticLineageEdgeBindingV1Error(
                f"DERIVED_SEMANTIC_LINEAGE_EDGE_REBINDING:{spec.edge_id}:OBJECT_ID"
            )
        if spec.source_whole_hash_field and dwhole != target["whole_object_content_hash"]:
            raise SemanticLineageEdgeBindingV1Error(
                f"LINEAGE_EDGE_WHOLE_OBJECT_IDENTITY_REBINDING:{spec.edge_id}"
            )
        if spec.source_projection_hash_field and dproj != target["semantic_projection_hash"]:
            raise SemanticLineageEdgeBindingV1Error(
                f"LINEAGE_EDGE_SEMANTIC_PROJECTION_REBINDING:{spec.edge_id}"
            )
        out.append({
            "edge_id":spec.edge_id,
            "source_vertex_key":spec.source_key,
            "target_vertex_key":spec.target_key,
            "source_declared_target_id":did,
            "source_declared_target_whole_content_hash":dwhole,
            "source_declared_target_semantic_projection_hash":dproj,
            "resolved_target_schema_id":target["schema_id"],
            "resolved_target_object_id":target["object_id"],
            "resolved_target_git_blob_sha1":target["git_blob_sha1"],
            "resolved_target_raw_sha256":target["raw_sha256"],
            "resolved_target_whole_content_hash":target["whole_object_content_hash"],
            "resolved_target_semantic_projection_hash":target["semantic_projection_hash"],
        })
    return tuple(out)

def edge_set_hash(edges: Sequence[Mapping[str,Any]]) -> str:
    return domain_hash(EDGE_SET_DOMAIN, list(edges))

def lineage_graph_identity(vertices: Sequence[Mapping[str,Any]], edges: Sequence[Mapping[str,Any]]) -> str:
    return domain_hash(LINEAGE_GRAPH_DOMAIN, {"vertices":list(vertices),"edges":list(edges)})

def verify_binding_receipt(
    receipt: Mapping[str, Any],
    objects: Mapping[str, Mapping[str, Any]],
    raws: Mapping[str, bytes],
) -> tuple[tuple[Mapping[str,Any],...], tuple[Mapping[str,Any],...], str]:
    if receipt.get("schema") != "AIFC/derived-semantic-lineage-edge-binding/v1":
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_EDGE_BINDING_SCHEMA_REBINDING")
    vertices = build_vertices(objects, raws)
    edges = build_edges(objects, vertices)

    ids = tuple(e["edge_id"] for e in edges)
    if ids != REQUIRED_EDGE_IDS:
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_REQUIRED_EDGE_SET_INTERNAL_ERROR")
    declared_edges = receipt.get("edges")
    if not isinstance(declared_edges,list) or tuple(x.get("edge_id") for x in declared_edges) != REQUIRED_EDGE_IDS:
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_EDGE_SET_OMISSION_OR_INJECTION")
    if receipt.get("vertices") != list(vertices):
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_VERTEX_WHOLE_OBJECT_IDENTITY_REBINDING")
    if declared_edges != list(edges):
        raise SemanticLineageEdgeBindingV1Error("DERIVED_SEMANTIC_LINEAGE_EDGE_REBINDING")

    eh = edge_set_hash(edges)
    gh = lineage_graph_identity(vertices, edges)
    if receipt.get("lineage_edge_set_hash") != eh:
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_EDGE_SET_HASH_REBINDING")
    if receipt.get("lineage_graph_identity") != gh:
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_GRAPH_IDENTITY_REBINDING")
    if receipt.get("binding_content_hash") != binding_content_hash(receipt):
        raise SemanticLineageEdgeBindingV1Error("LINEAGE_EDGE_BINDING_CONTENT_REBINDING")
    return vertices, edges, gh
