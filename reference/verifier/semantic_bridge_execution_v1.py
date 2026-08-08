#!/usr/bin/env python3
"""SAL semantic bridge execution semantics v1.

This module gives an authority-admissible bridge semantic effect only by composing
its exact executable axioms into the prover premise before entailment is evaluated.

The bridge language is the same finite propositional AST fragment already used by
SAL formulas: ATOM, NOT, AND, OR. Every bridge atom must have an explicit semantic
binding in its axiom object. The composition rule is deterministic:
PREMISE_AND_ORDERED_BRIDGE_AXIOMS_V1.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from canonical import domain_hash
from scientific_assurance_lineage_v16 import (
    EntailmentResult,
    ScientificAssuranceLineageV16Error,
    finite_propositional_entailment,
)

AXIOM_DOMAIN = "AIFC:SEMANTIC-BRIDGE-AXIOM:v1"
COMPOSED_PREMISE_DOMAIN = "AIFC:BRIDGE-COMPOSED-PREMISE:v1"


class SemanticBridgeExecutionV1Error(ValueError):
    pass


@dataclass(frozen=True)
class BridgeComposition:
    composed_premise: Mapping[str, Any]
    composed_premise_hash: str
    bridge_axiom_ids: tuple[str, ...]
    bridge_atom_ids: tuple[str, ...]


def formula_atoms(formula: Mapping[str, Any]) -> set[str]:
    """Strictly validate the finite propositional AST and return its atom IDs."""
    op = formula.get("op")
    keys = set(formula)
    if op == "ATOM":
        if keys != {"op", "id"}:
            raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_ATOM_SHAPE_INVALID")
        atom = formula.get("id")
        if not isinstance(atom, str) or not atom:
            raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_ATOM_ID_INVALID")
        return {atom}
    if op == "NOT":
        if keys != {"op", "arg"}:
            raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_NOT_SHAPE_INVALID")
        arg = formula.get("arg")
        if not isinstance(arg, Mapping):
            raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_NOT_ARG_INVALID")
        return formula_atoms(arg)
    if op in {"AND", "OR"}:
        if keys != {"op", "args"}:
            raise SemanticBridgeExecutionV1Error(f"BRIDGE_AXIOM_{op}_SHAPE_INVALID")
        args = formula.get("args")
        if not isinstance(args, list) or not args:
            raise SemanticBridgeExecutionV1Error(f"BRIDGE_AXIOM_{op}_ARGS_INVALID")
        atoms: set[str] = set()
        for arg in args:
            if not isinstance(arg, Mapping):
                raise SemanticBridgeExecutionV1Error(f"BRIDGE_AXIOM_{op}_ARG_INVALID")
            atoms |= formula_atoms(arg)
        return atoms
    raise SemanticBridgeExecutionV1Error(f"BRIDGE_AXIOM_OPERATOR_INVALID:{op}")


def bridge_axiom_content_hash(axiom: Mapping[str, Any]) -> str:
    material = dict(axiom)
    material.pop("axiom_content_hash", None)
    return domain_hash(AXIOM_DOMAIN, material)


def verify_bridge_axiom_semantics(
    axiom: Mapping[str, Any],
    *,
    expected_question_id: str,
    require_authority: bool,
) -> set[str]:
    if axiom.get("schema") != "AIFC/semantic-bridge-axiom/v1":
        raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_SCHEMA_IDENTITY_REBINDING")
    if axiom.get("entailment_question_id") != expected_question_id:
        raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_QUESTION_REBINDING")
    if axiom.get("logical_fragment") != "FINITE_CLASSICAL_PROPOSITIONAL_V1":
        raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_LOGICAL_FRAGMENT_REBINDING")
    ast = axiom.get("normalized_formula_ast")
    if not isinstance(ast, Mapping):
        raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_AST_INVALID")
    atoms = formula_atoms(ast)
    bindings = axiom.get("atom_bindings")
    if not isinstance(bindings, Mapping) or set(bindings) != atoms:
        raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_ATOM_NAMESPACE_BINDING_MISMATCH")
    for atom, binding in bindings.items():
        if not isinstance(binding, Mapping):
            raise SemanticBridgeExecutionV1Error(f"BRIDGE_AXIOM_ATOM_BINDING_INVALID:{atom}")
        if binding.get("semantic_role") not in {
            "PREDECESSOR_ATOM",
            "TARGET_ATOM",
            "BRIDGE_DERIVED_ATOM",
        }:
            raise SemanticBridgeExecutionV1Error(f"BRIDGE_AXIOM_ATOM_ROLE_INVALID:{atom}")
        identity = binding.get("semantic_identity")
        if not isinstance(identity, str) or not identity:
            raise SemanticBridgeExecutionV1Error(f"BRIDGE_AXIOM_ATOM_IDENTITY_INVALID:{atom}")
    claimed = axiom.get("axiom_content_hash")
    actual = bridge_axiom_content_hash(axiom)
    if claimed != actual:
        raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_CONTENT_IDENTITY_REBINDING")
    status = axiom.get("axiom_authority_status")
    if status not in {
        "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
        "AUTHORITY_ADMISSIBLE",
    }:
        raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_AUTHORITY_STATUS_INVALID")
    if require_authority and status != "AUTHORITY_ADMISSIBLE":
        raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_AUTHORITY_NOT_ADMISSIBLE")
    return atoms


def compose_bridge_premise(
    premise: Mapping[str, Any],
    bridge_axioms: Sequence[Mapping[str, Any]],
    *,
    expected_question_id: str,
    require_authority: bool,
) -> BridgeComposition:
    """Compose exact bridge axioms into the prover premise.

    No axiom is accepted only by being present. Each axiom is syntax-checked,
    content-hash checked, namespace-bound, and optionally authority-checked.
    """
    formula_atoms(premise)
    seen: set[str] = set()
    ids: list[str] = []
    asts: list[Mapping[str, Any]] = []
    bridge_atoms: set[str] = set()
    for axiom in bridge_axioms:
        axiom_id = axiom.get("axiom_id")
        if not isinstance(axiom_id, str) or not axiom_id or axiom_id in seen:
            raise SemanticBridgeExecutionV1Error("BRIDGE_AXIOM_ID_INVALID_OR_DUPLICATE")
        seen.add(axiom_id)
        ids.append(axiom_id)
        bridge_atoms |= verify_bridge_axiom_semantics(
            axiom,
            expected_question_id=expected_question_id,
            require_authority=require_authority,
        )
        ast = axiom.get("normalized_formula_ast")
        assert isinstance(ast, Mapping)
        asts.append(ast)

    if not asts:
        composed: Mapping[str, Any] = premise
    else:
        composed = {"op": "AND", "args": [premise, *asts]}
    material = {
        "composition_rule": "PREMISE_AND_ORDERED_BRIDGE_AXIOMS_V1",
        "entailment_question_id": expected_question_id,
        "bridge_axiom_ids": ids,
        "composed_premise": composed,
    }
    return BridgeComposition(
        composed_premise=composed,
        composed_premise_hash=domain_hash(COMPOSED_PREMISE_DOMAIN, material),
        bridge_axiom_ids=tuple(ids),
        bridge_atom_ids=tuple(sorted(bridge_atoms)),
    )


def bridge_aware_atom_count(
    premise: Mapping[str, Any],
    bridge_axioms: Sequence[Mapping[str, Any]],
    target: Mapping[str, Any],
    *,
    expected_question_id: str,
) -> int:
    composition = compose_bridge_premise(
        premise,
        bridge_axioms,
        expected_question_id=expected_question_id,
        require_authority=False,
    )
    return len(formula_atoms(composition.composed_premise) | formula_atoms(target))


def bridge_bound_entailment(
    premise: Mapping[str, Any],
    bridge_axioms: Sequence[Mapping[str, Any]],
    target: Mapping[str, Any],
    *,
    expected_question_id: str,
    max_atoms: int,
) -> tuple[EntailmentResult, BridgeComposition]:
    """The only v1.9 prover entry point.

    The underlying finite solver never receives the unbridged premise when a
    non-empty authority-admissible bridge is supplied.
    """
    composition = compose_bridge_premise(
        premise,
        bridge_axioms,
        expected_question_id=expected_question_id,
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


def bridge_effect_test_vector() -> tuple[str, str, int]:
    """Non-normative regression vector proving that a non-empty bridge changes the theorem.

    A alone does not entail C. A together with (not A or C) does entail C.
    """
    premise = {"op": "ATOM", "id": "TEST_A"}
    target = {"op": "ATOM", "id": "TEST_C"}
    axiom = {
        "schema": "AIFC/semantic-bridge-axiom/v1",
        "axiom_id": "AIFC-SAL-TEST-ONLY-BRIDGE-IMPLICATION-A-TO-C",
        "entailment_question_id": "0" * 64,
        "logical_fragment": "FINITE_CLASSICAL_PROPOSITIONAL_V1",
        "normalized_formula_ast": {
            "op": "OR",
            "args": [
                {"op": "NOT", "arg": {"op": "ATOM", "id": "TEST_A"}},
                {"op": "ATOM", "id": "TEST_C"},
            ],
        },
        "atom_bindings": {
            "TEST_A": {
                "semantic_role": "PREDECESSOR_ATOM",
                "semantic_identity": "TEST_ONLY:PREDECESSOR:A",
            },
            "TEST_C": {
                "semantic_role": "TARGET_ATOM",
                "semantic_identity": "TEST_ONLY:TARGET:C",
            },
        },
        "axiom_authority_status": "AUTHORITY_ADMISSIBLE",
    }
    axiom["axiom_content_hash"] = bridge_axiom_content_hash(axiom)
    direct = finite_propositional_entailment(premise, target, max_atoms=16)
    bridged, composition = bridge_bound_entailment(
        premise,
        [axiom],
        target,
        expected_question_id="0" * 64,
        max_atoms=16,
    )
    if direct.state != "REFUTED_BY_COUNTERMODEL" or bridged.state != "PROVED":
        raise SemanticBridgeExecutionV1Error("BRIDGE_EXECUTION_EFFECT_TEST_VECTOR_FAILED")
    atom_count = len(formula_atoms(composition.composed_premise) | formula_atoms(target))
    return direct.state, bridged.state, atom_count
