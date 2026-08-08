#!/usr/bin/env python3
"""SAL v1.11u machine-derived lineage edge universe.

The required cross-vertex identity-reference edge universe is recomputed from
the exact v1.11h vertex contents. No declared required-edge list is accepted as
an input. The result is scoped to the inherited six-vertex set and makes no
claim that the vertex universe or every semantic relation outside identity
references is complete.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from canonical import domain_hash
import semantic_lineage_edge_binding_v1 as v111h_edge

EDGE_UNIVERSE_DOMAIN = "AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE:v1"
LINEAGE_GRAPH_DOMAIN_V2 = "AIFC:DERIVED-SEMANTIC-LINEAGE-GRAPH:v2"
UNIVERSE_RECEIPT_DOMAIN = "AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE-RECEIPT:v1"
VERTEX_SCOPE = "INHERITED_EXACT_V1_11H_SIX_VERTEX_SET"
DERIVATION_STATUS = "MACHINE_DERIVED_NO_DECLARED_REQUIRED_EDGE_LIST"

class SemanticLineageEdgeUniverseV1Error(ValueError):
    pass

def universe_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj)
    material.pop("universe_content_hash", None)
    return domain_hash(UNIVERSE_RECEIPT_DOMAIN, material)

def edge_universe_hash(edges: Sequence[Mapping[str, Any]]) -> str:
    return domain_hash(EDGE_UNIVERSE_DOMAIN, list(edges))

def lineage_graph_identity_v2(
    vertices: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
) -> str:
    return domain_hash(
        LINEAGE_GRAPH_DOMAIN_V2,
        {"vertices": list(vertices), "edges": list(edges)},
    )

def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")

def _walk_strings(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield from _walk_strings(item, path + "/" + _pointer_escape(str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, path + "/" + str(index))
    elif isinstance(value, str):
        yield path, value

def _target_identity_channels(
    objects: Mapping[str, Mapping[str, Any]],
    vertices: Sequence[Mapping[str, Any]],
) -> Mapping[str, Mapping[str, tuple[str, ...]]]:
    """Derive target aliases from exact vertex identity material.

    The v1.11h Exact(X) channels are always included. A top-level
    ``semantic_identity`` is additionally treated as a semantic alias of the
    vertex that owns it; in the current six-vertex scope this exposes the
    already-v1.11-proved derived output identity without a source->target edge
    list.
    """
    aliases: dict[str, dict[str, tuple[str, ...]]] = {}
    for vertex in vertices:
        key = str(vertex["vertex_key"])
        obj = objects[key]
        by_value: dict[str, set[str]] = defaultdict(set)

        def add(channel: str, candidate: Any) -> None:
            if isinstance(candidate, str) and candidate:
                by_value[candidate].add(channel)

        add("OBJECT_ID", vertex.get("object_id"))
        add("WHOLE_OBJECT_CONTENT_HASH", vertex.get("whole_object_content_hash"))
        add("SEMANTIC_PROJECTION_HASH", vertex.get("semantic_projection_hash"))
        add("TOP_LEVEL_SEMANTIC_IDENTITY", obj.get("semantic_identity"))
        aliases[key] = {
            value: tuple(sorted(channels))
            for value, channels in by_value.items()
        }
    return aliases

def derive_edge_universe(
    objects: Mapping[str, Mapping[str, Any]],
    vertices: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    """Derive every cross-vertex exact-identity reference in the bound scope."""
    vmap = {str(v["vertex_key"]): v for v in vertices}
    if set(vmap) != set(objects):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_VERTEX_SCOPE_OBJECT_MISMATCH"
        )
    aliases = _target_identity_channels(objects, vertices)
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)

    for source_key in vmap:
        for source_path, value in _walk_strings(objects[source_key]):
            for target_key, target_aliases in aliases.items():
                if target_key == source_key:
                    continue
                channels = target_aliases.get(value)
                if channels is None:
                    continue
                grouped[(source_key, target_key)].append(
                    {
                        "source_json_pointer": source_path,
                        "matched_identity": value,
                        "target_identity_channels": list(channels),
                    }
                )

    edges: list[Mapping[str, Any]] = []
    for (source_key, target_key), occurrences in grouped.items():
        target = vmap[target_key]
        ordered_occurrences = sorted(
            occurrences,
            key=lambda item: (
                str(item["source_json_pointer"]),
                str(item["matched_identity"]),
                tuple(item["target_identity_channels"]),
            ),
        )
        edges.append(
            {
                "edge_id": f"{source_key}_TO_{target_key}",
                "source_vertex_key": source_key,
                "target_vertex_key": target_key,
                "evidence_occurrences": ordered_occurrences,
                "resolved_target_schema_id": target["schema_id"],
                "resolved_target_object_id": target["object_id"],
                "resolved_target_git_blob_sha1": target["git_blob_sha1"],
                "resolved_target_raw_sha256": target["raw_sha256"],
                "resolved_target_whole_content_hash": target[
                    "whole_object_content_hash"
                ],
                "resolved_target_semantic_projection_hash": target[
                    "semantic_projection_hash"
                ],
            }
        )
    return tuple(sorted(edges, key=lambda item: str(item["edge_id"])))

def _pair_id(edge: Mapping[str, Any]) -> str:
    return f'{edge["source_vertex_key"]}_TO_{edge["target_vertex_key"]}'

def verify_source_question_context(
    source_binding: Mapping[str, Any],
    source_audit: Mapping[str, Any],
    question_id: str,
) -> None:
    if source_binding.get("entailment_question_id") != question_id:
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_BINDING_QUESTION_CONTEXT_REBINDING"
        )
    if source_audit.get("entailment_question_id") != question_id:
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_AUDIT_QUESTION_CONTEXT_REBINDING"
        )

def verify_universe_receipt(
    receipt: Mapping[str, Any],
    source_binding: Mapping[str, Any],
    source_audit: Mapping[str, Any],
    objects: Mapping[str, Mapping[str, Any]],
    raws: Mapping[str, bytes],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    str,
]:
    if receipt.get("schema") != "AIFC/derived-semantic-lineage-edge-universe/v1":
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_SCHEMA_REBINDING"
        )

    vertices, old_edges, old_graph = v111h_edge.verify_binding_receipt(
        source_binding, objects, raws
    )
    question = next(
        (v for v in vertices if v.get("vertex_key") == "QUESTION"),
        None,
    )
    if question is None:
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_QUESTION_VERTEX_MISSING"
        )
    question_id = str(question["object_id"])
    verify_source_question_context(source_binding, source_audit, question_id)

    if receipt.get("entailment_question_id") != question_id:
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_UNIVERSE_QUESTION_CONTEXT_REBINDING"
        )
    if receipt.get("vertex_scope") != VERTEX_SCOPE:
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_SCOPE_REBINDING"
        )
    if receipt.get("vertex_scope_count") != len(vertices):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_SCOPE_COUNT_REBINDING"
        )
    if (
        receipt.get("source_lineage_edge_binding_id")
        != source_binding.get("lineage_edge_binding_id")
        or receipt.get("source_lineage_edge_binding_content_hash")
        != source_binding.get("binding_content_hash")
        or receipt.get("source_lineage_graph_identity") != old_graph
    ):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_SOURCE_BINDING_REBINDING"
        )

    derived_edges = derive_edge_universe(objects, vertices)
    old_pairs = tuple(sorted(_pair_id(item) for item in old_edges))
    derived_pairs = tuple(_pair_id(item) for item in derived_edges)
    if not set(old_pairs).issubset(set(derived_pairs)):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_DECLARED_EDGE_NOT_IN_DERIVED_UNIVERSE"
        )
    newly_derived = tuple(sorted(set(derived_pairs) - set(old_pairs)))

    if receipt.get("inherited_declared_edge_pairs") != list(old_pairs):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_INHERITED_EDGE_PAIR_REBINDING"
        )
    if receipt.get("newly_derived_edge_pairs") != list(newly_derived):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_NEWLY_DERIVED_EDGE_PAIR_REBINDING"
        )
    if receipt.get("derived_edge_count") != len(derived_edges):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_COUNT_REBINDING"
        )
    if receipt.get("derived_edge_pairs") != list(derived_pairs):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_REQUIRED_EDGE_UNIVERSE_OMISSION_OR_INJECTION"
        )

    universe_hash = edge_universe_hash(derived_edges)
    graph_id = lineage_graph_identity_v2(vertices, derived_edges)
    if receipt.get("lineage_edge_universe_hash") != universe_hash:
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_HASH_REBINDING"
        )
    if receipt.get("lineage_graph_identity_v2") != graph_id:
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_GRAPH_IDENTITY_REBINDING"
        )
    if receipt.get("universe_derivation_status") != DERIVATION_STATUS:
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_DERIVATION_STATUS_REBINDING"
        )
    if receipt.get("vertex_universe_completeness") != "NOT_ESTABLISHED":
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_VERTEX_UNIVERSE_FALSE_PROMOTION"
        )
    if receipt.get("semantic_relation_universe_completeness") != "NOT_ESTABLISHED":
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_SEMANTIC_RELATION_UNIVERSE_FALSE_PROMOTION"
        )
    if receipt.get("universe_content_hash") != universe_content_hash(receipt):
        raise SemanticLineageEdgeUniverseV1Error(
            "LINEAGE_EDGE_UNIVERSE_CONTENT_REBINDING"
        )
    return tuple(vertices), derived_edges, graph_id
