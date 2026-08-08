#!/usr/bin/env python3
"""SAL semantic bridge endpoint identity semantics v1.

Executable bridge atoms are not identified by their names alone. Every endpoint
atom must resolve to the exact canonical semantic binding of the predecessor or
target formula. Bridge-derived atoms must be disjoint from both endpoint
namespaces and resolve a separate content-identified derivation object.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from canonical import domain_hash
from scientific_assurance_lineage_v16 import (
    EntailmentResult,
    ScientificAssuranceLineageV16Error,
    finite_propositional_entailment,
)
import semantic_bridge_execution_v1 as v1

AXIOM_V2_DOMAIN = "AIFC:SEMANTIC-BRIDGE-AXIOM:v2"
DERIVED_OBJECT_DOMAIN = "AIFC:BRIDGE-DERIVED-SEMANTIC-OBJECT:v1"
COMPOSED_PREMISE_DOMAIN = "AIFC:BRIDGE-ENDPOINT-CLOSED-COMPOSED-PREMISE:v1"
ENDPOINT_PROFILE_ID = "AIFC-SAL-V1.10-SEMANTIC-BRIDGE-ENDPOINT-IDENTITY-PROFILE-V1"


class SemanticBridgeEndpointIdentityV1Error(ValueError):
    pass


@dataclass(frozen=True)
class EndpointClosedBridgeComposition:
    composed_premise: Mapping[str, Any]
    composed_premise_hash: str
    bridge_axiom_ids: tuple[str, ...]
    bridge_atom_ids: tuple[str, ...]
    predecessor_endpoint_atoms: tuple[str, ...]
    target_endpoint_atoms: tuple[str, ...]
    derived_atoms: tuple[str, ...]


def bridge_axiom_v2_content_hash(axiom: Mapping[str, Any]) -> str:
    material = dict(axiom)
    material.pop("axiom_content_hash", None)
    return domain_hash(AXIOM_V2_DOMAIN, material)


def derived_semantic_object_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj)
    material.pop("derivation_content_hash", None)
    return domain_hash(DERIVED_OBJECT_DOMAIN, material)


def verify_derived_semantic_object(
    obj: Mapping[str, Any],
    *,
    expected_question_id: str,
    expected_atom_id: str,
    expected_semantic_identity: str,
    require_authority: bool,
) -> None:
    if obj.get("schema") != "AIFC/bridge-derived-semantic-object/v1":
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_SCHEMA_REBINDING")
    if obj.get("entailment_question_id") != expected_question_id:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_QUESTION_REBINDING")
    if obj.get("atom_id") != expected_atom_id:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_ATOM_REBINDING")
    if obj.get("semantic_identity") != expected_semantic_identity:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_SEMANTIC_IDENTITY_REBINDING")
    if obj.get("derivation_kind") != "BRIDGE_DERIVED_SEMANTIC_OBJECT_V1":
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_KIND_REBINDING")
    sources = obj.get("source_semantic_identities")
    if not isinstance(sources, list) or not sources or any(not isinstance(x, str) or not x for x in sources):
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_SOURCE_SEMANTICS_INVALID")
    if len(set(sources)) != len(sources):
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_SOURCE_SEMANTICS_DUPLICATE")
    claimed = obj.get("derivation_content_hash")
    if claimed != derived_semantic_object_content_hash(obj):
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_CONTENT_IDENTITY_REBINDING")
    status = obj.get("derivation_authority_status")
    lineage = obj.get("authority_lineage_ref")
    if status not in {
        "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
        "AUTHORITY_ADMISSIBLE",
    }:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_AUTHORITY_STATUS_INVALID")
    if status == "AUTHORITY_ADMISSIBLE":
        if not isinstance(lineage, Mapping):
            raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_AUTHORITY_LINEAGE_MISSING")
    elif lineage is not None:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_CANDIDATE_LINEAGE_SELF_ASSERTION")
    if require_authority and status != "AUTHORITY_ADMISSIBLE":
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_DERIVED_OBJECT_AUTHORITY_NOT_ADMISSIBLE")


def _require_disjoint_endpoint_namespaces(
    predecessor_bindings: Mapping[str, str],
    target_bindings: Mapping[str, str],
) -> None:
    overlap = set(predecessor_bindings) & set(target_bindings)
    if overlap:
        raise SemanticBridgeEndpointIdentityV1Error(
            "BRIDGE_ENDPOINT_NAMESPACE_COLLISION:" + ",".join(sorted(overlap))
        )


def verify_bridge_axiom_endpoint_identity(
    axiom: Mapping[str, Any],
    *,
    expected_question_id: str,
    predecessor_bindings: Mapping[str, str],
    target_bindings: Mapping[str, str],
    derived_object_resolver: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    require_authority: bool,
) -> set[str]:
    _require_disjoint_endpoint_namespaces(predecessor_bindings, target_bindings)
    if axiom.get("schema") != "AIFC/semantic-bridge-axiom/v2":
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_V2_SCHEMA_IDENTITY_REBINDING")
    if axiom.get("entailment_question_id") != expected_question_id:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_QUESTION_REBINDING")
    if axiom.get("logical_fragment") != "FINITE_CLASSICAL_PROPOSITIONAL_V1":
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_LOGICAL_FRAGMENT_REBINDING")
    if axiom.get("endpoint_identity_profile_id") != ENDPOINT_PROFILE_ID:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_ENDPOINT_IDENTITY_PROFILE_REBINDING")
    ast = axiom.get("normalized_formula_ast")
    if not isinstance(ast, Mapping):
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_AST_INVALID")
    try:
        atoms = v1.formula_atoms(ast)
    except v1.SemanticBridgeExecutionV1Error as exc:
        raise SemanticBridgeEndpointIdentityV1Error(str(exc)) from exc
    bindings = axiom.get("atom_bindings")
    if not isinstance(bindings, Mapping) or set(bindings) != atoms:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_ATOM_NAMESPACE_BINDING_MISMATCH")

    for atom, binding in bindings.items():
        if not isinstance(binding, Mapping):
            raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_AXIOM_ATOM_BINDING_INVALID:{atom}")
        role = binding.get("semantic_role")
        identity = binding.get("semantic_identity")
        if not isinstance(identity, str) or not identity:
            raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_AXIOM_ATOM_IDENTITY_INVALID:{atom}")

        if role == "PREDECESSOR_ATOM":
            if atom not in predecessor_bindings:
                if atom in target_bindings:
                    raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_ATOM_ROLE_REBINDING:{atom}:TARGET_AS_PREDECESSOR")
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_PREDECESSOR_ENDPOINT_UNKNOWN:{atom}")
            if identity != predecessor_bindings[atom]:
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_ATOM_SEMANTIC_IDENTITY_REBINDING:{atom}")
            if "derived_semantic_object_ref" in binding:
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_ENDPOINT_DERIVED_REF_FORBIDDEN:{atom}")
        elif role == "TARGET_ATOM":
            if atom not in target_bindings:
                if atom in predecessor_bindings:
                    raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_ATOM_ROLE_REBINDING:{atom}:PREDECESSOR_AS_TARGET")
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_TARGET_ENDPOINT_UNKNOWN:{atom}")
            if identity != target_bindings[atom]:
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_ATOM_SEMANTIC_IDENTITY_REBINDING:{atom}")
            if "derived_semantic_object_ref" in binding:
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_ENDPOINT_DERIVED_REF_FORBIDDEN:{atom}")
        elif role == "BRIDGE_DERIVED_ATOM":
            if atom in predecessor_bindings or atom in target_bindings:
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_DERIVED_ATOM_COLLISION:{atom}")
            ref = binding.get("derived_semantic_object_ref")
            if not isinstance(ref, Mapping):
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_DERIVED_ATOM_PROVENANCE_MISSING:{atom}")
            obj = derived_object_resolver(ref)
            if obj.get("derived_semantic_object_id") != ref.get("derived_semantic_object_id"):
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_DERIVED_OBJECT_REFERENCE_REBINDING:{atom}")
            if obj.get("derivation_content_hash") != ref.get("derivation_content_hash"):
                raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_DERIVED_OBJECT_REFERENCE_REBINDING:{atom}")
            verify_derived_semantic_object(
                obj,
                expected_question_id=expected_question_id,
                expected_atom_id=atom,
                expected_semantic_identity=identity,
                require_authority=require_authority,
            )
        else:
            raise SemanticBridgeEndpointIdentityV1Error(f"BRIDGE_AXIOM_ATOM_ROLE_INVALID:{atom}")

    claimed = axiom.get("axiom_content_hash")
    if claimed != bridge_axiom_v2_content_hash(axiom):
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_CONTENT_IDENTITY_REBINDING")
    status = axiom.get("axiom_authority_status")
    lineage = axiom.get("authority_lineage_ref")
    if status not in {
        "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
        "AUTHORITY_ADMISSIBLE",
    }:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_AUTHORITY_STATUS_INVALID")
    if status == "AUTHORITY_ADMISSIBLE":
        if not isinstance(lineage, Mapping):
            raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_AUTHORITY_LINEAGE_MISSING")
    elif lineage is not None:
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_CANDIDATE_LINEAGE_SELF_ASSERTION")
    if require_authority and status != "AUTHORITY_ADMISSIBLE":
        raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_AUTHORITY_NOT_ADMISSIBLE")
    return atoms


def compose_endpoint_closed_bridge_premise(
    premise: Mapping[str, Any],
    bridge_axioms: Sequence[Mapping[str, Any]],
    *,
    expected_question_id: str,
    predecessor_bindings: Mapping[str, str],
    target_bindings: Mapping[str, str],
    derived_object_resolver: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    require_authority: bool,
) -> EndpointClosedBridgeComposition:
    try:
        v1.formula_atoms(premise)
    except v1.SemanticBridgeExecutionV1Error as exc:
        raise SemanticBridgeEndpointIdentityV1Error(str(exc)) from exc
    _require_disjoint_endpoint_namespaces(predecessor_bindings, target_bindings)
    seen: set[str] = set()
    ids: list[str] = []
    asts: list[Mapping[str, Any]] = []
    bridge_atoms: set[str] = set()
    pred_atoms: set[str] = set()
    target_atoms: set[str] = set()
    derived_atoms: set[str] = set()

    for axiom in bridge_axioms:
        axiom_id = axiom.get("axiom_id")
        if not isinstance(axiom_id, str) or not axiom_id or axiom_id in seen:
            raise SemanticBridgeEndpointIdentityV1Error("BRIDGE_AXIOM_ID_INVALID_OR_DUPLICATE")
        seen.add(axiom_id)
        ids.append(axiom_id)
        atoms = verify_bridge_axiom_endpoint_identity(
            axiom,
            expected_question_id=expected_question_id,
            predecessor_bindings=predecessor_bindings,
            target_bindings=target_bindings,
            derived_object_resolver=derived_object_resolver,
            require_authority=require_authority,
        )
        bridge_atoms |= atoms
        bindings = axiom["atom_bindings"]
        pred_atoms |= {a for a in atoms if bindings[a]["semantic_role"] == "PREDECESSOR_ATOM"}
        target_atoms |= {a for a in atoms if bindings[a]["semantic_role"] == "TARGET_ATOM"}
        derived_atoms |= {a for a in atoms if bindings[a]["semantic_role"] == "BRIDGE_DERIVED_ATOM"}
        ast = axiom.get("normalized_formula_ast")
        assert isinstance(ast, Mapping)
        asts.append(ast)

    composed: Mapping[str, Any]
    if not asts:
        composed = premise
    else:
        composed = {"op":"AND","args":[premise,*asts]}
    material = {
        "composition_rule":"PREMISE_AND_ORDERED_ENDPOINT_CLOSED_BRIDGE_AXIOMS_V1",
        "entailment_question_id":expected_question_id,
        "bridge_axiom_ids":ids,
        "composed_premise":composed,
    }
    return EndpointClosedBridgeComposition(
        composed_premise=composed,
        composed_premise_hash=domain_hash(COMPOSED_PREMISE_DOMAIN, material),
        bridge_axiom_ids=tuple(ids),
        bridge_atom_ids=tuple(sorted(bridge_atoms)),
        predecessor_endpoint_atoms=tuple(sorted(pred_atoms)),
        target_endpoint_atoms=tuple(sorted(target_atoms)),
        derived_atoms=tuple(sorted(derived_atoms)),
    )


def bridge_aware_atom_count_v2(
    premise: Mapping[str, Any],
    bridge_axioms: Sequence[Mapping[str, Any]],
    target: Mapping[str, Any],
    *,
    expected_question_id: str,
    predecessor_bindings: Mapping[str, str],
    target_bindings: Mapping[str, str],
    derived_object_resolver: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> int:
    composition = compose_endpoint_closed_bridge_premise(
        premise,
        bridge_axioms,
        expected_question_id=expected_question_id,
        predecessor_bindings=predecessor_bindings,
        target_bindings=target_bindings,
        derived_object_resolver=derived_object_resolver,
        require_authority=False,
    )
    try:
        return len(v1.formula_atoms(composition.composed_premise) | v1.formula_atoms(target))
    except v1.SemanticBridgeExecutionV1Error as exc:
        raise SemanticBridgeEndpointIdentityV1Error(str(exc)) from exc


def bridge_bound_entailment_v2(
    premise: Mapping[str, Any],
    bridge_axioms: Sequence[Mapping[str, Any]],
    target: Mapping[str, Any],
    *,
    expected_question_id: str,
    predecessor_bindings: Mapping[str, str],
    target_bindings: Mapping[str, str],
    derived_object_resolver: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    max_atoms: int,
) -> tuple[EntailmentResult, EndpointClosedBridgeComposition]:
    composition = compose_endpoint_closed_bridge_premise(
        premise,
        bridge_axioms,
        expected_question_id=expected_question_id,
        predecessor_bindings=predecessor_bindings,
        target_bindings=target_bindings,
        derived_object_resolver=derived_object_resolver,
        require_authority=True,
    )
    try:
        result = finite_propositional_entailment(
            composition.composed_premise,
            target,
            max_atoms=max_atoms,
        )
    except ScientificAssuranceLineageV16Error:
        raise
    return result, composition
