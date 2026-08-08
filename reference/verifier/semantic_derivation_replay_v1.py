#!/usr/bin/env python3
"""SAL v1.11 derivation replay candidate.

The replay engine can return VALID, INVALID, or BLOCKED. It has no authority
decision type and cannot promote a semantic object to normative authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from canonical import domain_hash
from canonical_semantic_resolver_v1 import CanonicalResolution

PROFILE_DOMAIN = "AIFC:SEMANTIC-DERIVATION-PROFILE:v1"
PROOF_DOMAIN = "AIFC:SEMANTIC-DERIVATION-PROOF:v1"
MANIFEST_DOMAIN = "AIFC:DERIVATION-LEAF-MANIFEST:v1"
GRAPH_DOMAIN = "AIFC:CANONICAL-SEMANTIC-DEPENDENCY-GRAPH:v1"
DERIVED_DOMAIN = "AIFC:BRIDGE-DERIVED-SEMANTIC-OBJECT:v2"
OUTPUT_DOMAIN = "AIFC:DERIVED-SEMANTIC-OUTPUT:v1"

class SemanticDerivationReplayV1Error(ValueError):
    pass

@dataclass(frozen=True)
class DerivationReplayResult:
    state: str
    normalized_derivation_ast: Mapping[str, Any] | None
    recomputed_manifest: tuple[Mapping[str, Any], ...]
    recomputed_manifest_hash: str | None
    canonical_dependencies: tuple[str, ...]
    recomputed_dependency_graph_hash: str | None
    recomputed_output_semantic_identity: str | None

def profile_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj); material.pop("profile_content_hash", None)
    return domain_hash(PROFILE_DOMAIN, material)

def proof_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj); material.pop("proof_content_hash", None)
    return domain_hash(PROOF_DOMAIN, material)

def manifest_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj); material.pop("manifest_content_hash", None)
    return domain_hash(MANIFEST_DOMAIN, material)

def graph_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj); material.pop("graph_content_hash", None)
    return domain_hash(GRAPH_DOMAIN, material)

def derived_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj); material.pop("derivation_content_hash", None)
    return domain_hash(DERIVED_DOMAIN, material)

def normalize_derivation_ast(ast: Mapping[str, Any], profile: Mapping[str, Any]) -> Mapping[str, Any]:
    if profile.get("normalization_semantics") != "SORT_SOURCE_REFERENCE_IDS_LEXICOGRAPHIC_STABLE_DUPLICATES_V1":
        raise SemanticDerivationReplayV1Error("DERIVATION_NORMALIZATION_REBINDING")
    if ast.get("op") != "DERIVE" or ast.get("rule") != "CANONICAL_MULTI_SOURCE_COMPOSITION_V1":
        raise SemanticDerivationReplayV1Error("DERIVATION_AST_UNSUPPORTED")
    sources = ast.get("sources")
    conclusion = ast.get("conclusion")
    if not isinstance(sources, list) or not sources or not isinstance(conclusion, Mapping):
        raise SemanticDerivationReplayV1Error("DERIVATION_AST_INVALID")
    clean = []
    for source in sources:
        if not isinstance(source, Mapping) or set(source) != {"op","semantic_reference_id"} or source.get("op") != "SOURCE":
            raise SemanticDerivationReplayV1Error("DERIVATION_SOURCE_NODE_INVALID")
        rid = source.get("semantic_reference_id")
        if not isinstance(rid, str) or not rid:
            raise SemanticDerivationReplayV1Error("DERIVATION_SOURCE_REFERENCE_INVALID")
        clean.append({"op":"SOURCE","semantic_reference_id":rid})
    clean.sort(key=lambda x: x["semantic_reference_id"])
    return {
        "op":"DERIVE",
        "rule":"CANONICAL_MULTI_SOURCE_COMPOSITION_V1",
        "sources":clean,
        "conclusion":{
            "entailment_question_id": conclusion.get("entailment_question_id"),
            "atom_id": conclusion.get("atom_id"),
            "semantic_identity": conclusion.get("semantic_identity"),
            "semantic_role": conclusion.get("semantic_role"),
        },
    }

def canonical_leaf_manifest(
    normalized_ast: Mapping[str, Any],
    resolution_by_ref: Mapping[str, CanonicalResolution],
) -> tuple[Mapping[str, Any], ...]:
    sources = normalized_ast["sources"]
    occurrence: dict[str,int] = {}
    out = []
    for idx, node in enumerate(sources):
        rid = node["semantic_reference_id"]
        resolved = resolution_by_ref.get(rid)
        if resolved is None or resolved.state != "RESOLVED":
            raise SemanticDerivationReplayV1Error("DERIVATION_SOURCE_RESOLUTION_BLOCKED")
        occurrence_key = str(resolved.canonical_source_identity)
        n = occurrence.get(occurrence_key, 0)
        occurrence[occurrence_key] = n + 1
        out.append({
            "canonical_semantic_identity": resolved.canonical_semantic_identity,
            "resolved_semantic_role": resolved.resolved_semantic_role,
            "canonical_source_identity": resolved.canonical_source_identity,
            "normalized_proof_node_path": f"/sources/{idx}",
            "occurrence_index": n,
            "semantic_context": "DERIVATION_PREMISE",
            "polarity": "POSITIVE",
        })
    return tuple(out)

def leaf_manifest_hash(entries: Sequence[Mapping[str, Any]], question_id: str) -> str:
    return domain_hash(MANIFEST_DOMAIN, {"entailment_question_id":question_id,"entries":list(entries)})

def canonical_dependencies(entries: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(sorted({str(x["canonical_semantic_identity"]) for x in entries}))

def dependency_graph_hash(derived_identity: str, deps: Sequence[str], question_id: str) -> str:
    return domain_hash(
        GRAPH_DOMAIN,
        {
            "entailment_question_id":question_id,
            "derived_semantic_identity":derived_identity,
            "dependencies":list(sorted(set(deps))),
        },
    )

def assert_acyclic(graph: Mapping[str, Sequence[str]]) -> None:
    visiting:set[str]=set(); visited:set[str]=set()
    def visit(node:str):
        if node in visiting:
            raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_DEPENDENCY_CYCLE")
        if node in visited:
            return
        visiting.add(node)
        for nxt in graph.get(node, ()):
            visit(str(nxt))
        visiting.remove(node); visited.add(node)
    for node in list(graph):
        visit(str(node))

def expected_output_identity(question_id: str, atom_id: str, manifest_hash: str, profile_hash: str) -> str:
    return "DERIVED_SEMANTIC:" + domain_hash(
        OUTPUT_DOMAIN,
        {
            "entailment_question_id":question_id,
            "atom_id":atom_id,
            "leaf_manifest_hash":manifest_hash,
            "derivation_profile_content_hash":profile_hash,
        },
    )

def replay_derivation(
    proof: Mapping[str, Any],
    profile: Mapping[str, Any],
    manifest_obj: Mapping[str, Any],
    graph_obj: Mapping[str, Any],
    derived_obj: Mapping[str, Any],
    resolve_ref: Callable[[str], CanonicalResolution],
) -> DerivationReplayResult:
    if profile.get("schema") != "AIFC/semantic-derivation-profile/v1":
        raise SemanticDerivationReplayV1Error("DERIVATION_PROFILE_SCHEMA_REBINDING")
    if proof.get("schema") != "AIFC/semantic-derivation-proof/v1":
        raise SemanticDerivationReplayV1Error("DERIVATION_PROOF_SCHEMA_REBINDING")
    if proof.get("derivation_profile_id") != profile.get("derivation_profile_id"):
        raise SemanticDerivationReplayV1Error("DERIVATION_PROOF_PROFILE_REBINDING")
    if proof.get("derivation_profile_content_hash") != profile.get("profile_content_hash"):
        raise SemanticDerivationReplayV1Error("DERIVATION_PROOF_PROFILE_REBINDING")
    if profile.get("profile_content_hash") != profile_content_hash(profile):
        raise SemanticDerivationReplayV1Error("DERIVATION_PROFILE_CONTENT_IDENTITY_REBINDING")
    if proof.get("proof_content_hash") != proof_content_hash(proof):
        raise SemanticDerivationReplayV1Error("DERIVATION_PROOF_CONTENT_IDENTITY_REBINDING")
    normalized = normalize_derivation_ast(proof["raw_derivation_ast"], profile)
    refs = [x["semantic_reference_id"] for x in normalized["sources"]]
    declared_refs = proof.get("source_semantic_reference_ids")
    if not isinstance(declared_refs, list) or sorted(declared_refs) != sorted(set(refs)):
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_SOURCE_REFERENCE_SET_REBINDING")
    resolutions = {rid: resolve_ref(rid) for rid in sorted(set(refs))}
    if any(r.state != "RESOLVED" for r in resolutions.values()):
        return DerivationReplayResult("BLOCKED", normalized, (), None, (), None, None)
    manifest = canonical_leaf_manifest(normalized, resolutions)
    qid = str(proof.get("entailment_question_id"))
    mh = leaf_manifest_hash(manifest, qid)
    if manifest_obj.get("manifest_content_hash") != manifest_content_hash(manifest_obj):
        raise SemanticDerivationReplayV1Error("DERIVATION_LEAF_MANIFEST_CONTENT_REBINDING")
    if manifest_obj.get("entailment_question_id") != qid or manifest_obj.get("entries") != list(manifest):
        raise SemanticDerivationReplayV1Error("DERIVATION_CANONICAL_LEAF_MANIFEST_REBINDING")
    if proof.get("declared_leaf_manifest_hash") != mh or manifest_obj.get("leaf_manifest_hash") != mh:
        raise SemanticDerivationReplayV1Error("DERIVATION_CANONICAL_LEAF_MANIFEST_HASH_REBINDING")
    deps = canonical_dependencies(manifest)
    conclusion = normalized["conclusion"]
    expected_identity = expected_output_identity(
        qid, str(conclusion.get("atom_id")), mh, str(profile.get("profile_content_hash"))
    )
    if conclusion.get("entailment_question_id") != qid:
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_OUTPUT_QUESTION_REBINDING")
    if conclusion.get("semantic_role") != "BRIDGE_DERIVED_ATOM":
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_OUTPUT_ROLE_REBINDING")
    if conclusion.get("semantic_identity") != expected_identity:
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_OUTPUT_IDENTITY_REBINDING")
    if derived_obj.get("source_semantic_reference_ids") != sorted(set(refs)):
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_SOURCE_REFERENCE_SET_REBINDING")
    if derived_obj.get("entailment_question_id") != qid:
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_OUTPUT_QUESTION_REBINDING")
    if derived_obj.get("atom_id") != conclusion.get("atom_id"):
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_OUTPUT_ATOM_REBINDING")
    if derived_obj.get("semantic_identity") != expected_identity:
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_OUTPUT_IDENTITY_REBINDING")
    if derived_obj.get("semantic_role") != "BRIDGE_DERIVED_ATOM":
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_OUTPUT_ROLE_REBINDING")
    if derived_obj.get("derivation_content_hash") != derived_content_hash(derived_obj):
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_OBJECT_CONTENT_IDENTITY_REBINDING")
    gh = dependency_graph_hash(expected_identity, deps, qid)
    if graph_obj.get("graph_content_hash") != graph_content_hash(graph_obj):
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_DEPENDENCY_GRAPH_CONTENT_REBINDING")
    if graph_obj.get("dependencies") != list(deps) or graph_obj.get("derived_semantic_identity") != expected_identity:
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_DEPENDENCY_GRAPH_REBINDING")
    if graph_obj.get("dependency_graph_hash") != gh:
        raise SemanticDerivationReplayV1Error("DERIVED_SEMANTIC_DEPENDENCY_GRAPH_HASH_REBINDING")
    assert_acyclic({expected_identity: deps})
    return DerivationReplayResult("VALID", normalized, manifest, mh, deps, gh, expected_identity)
