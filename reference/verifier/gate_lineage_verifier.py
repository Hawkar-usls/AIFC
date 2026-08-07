#!/usr/bin/env python3
"""Resolver-backed proof replay for AIFC mandatory gate lineage transitions."""
from __future__ import annotations

from itertools import product
from typing import Any, Mapping


class GateLineageVerificationError(ValueError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise GateLineageVerificationError(code)


def _resolved_obj(resolver, content_hash: str, expected_schema: str) -> Mapping[str, Any]:
    try:
        resolved = resolver.resolve(content_hash, expected_schema=expected_schema)
    except Exception as exc:
        raise GateLineageVerificationError(
            f"GATE_LINEAGE_EVIDENCE_RESOLUTION_FAILED:{expected_schema}:{content_hash}:{exc}"
        ) from exc
    obj = resolved.parsed_json
    if not isinstance(obj, Mapping):
        raise GateLineageVerificationError(f"GATE_LINEAGE_RESOLVED_OBJECT_INVALID:{expected_schema}")
    return obj


def _atoms(expr: Mapping[str, Any]) -> set[str]:
    op = expr.get("op")
    if op == "ATOM":
        atom = expr.get("id")
        _require(isinstance(atom, str) and atom, "GATE_DEFINITION_ATOM_INVALID")
        return {atom}
    if op == "CONST":
        _require(isinstance(expr.get("value"), bool), "GATE_DEFINITION_CONST_INVALID")
        return set()
    if op in {"AND", "OR"}:
        args = expr.get("args")
        _require(isinstance(args, list) and args, "GATE_DEFINITION_ARGS_INVALID")
        out: set[str] = set()
        for arg in args:
            _require(isinstance(arg, Mapping), "GATE_DEFINITION_ARG_NOT_OBJECT")
            out.update(_atoms(arg))
        return out
    if op == "NOT":
        arg = expr.get("arg")
        _require(isinstance(arg, Mapping), "GATE_DEFINITION_NOT_ARG_INVALID")
        return _atoms(arg)
    raise GateLineageVerificationError(f"GATE_DEFINITION_OPERATOR_INVALID:{op}")


def _evaluate(expr: Mapping[str, Any], assignment: Mapping[str, bool]) -> bool:
    op = expr.get("op")
    if op == "ATOM":
        atom = str(expr.get("id"))
        _require(atom in assignment, f"GATE_DEFINITION_ATOM_UNBOUND:{atom}")
        return bool(assignment[atom])
    if op == "CONST":
        value = expr.get("value")
        _require(isinstance(value, bool), "GATE_DEFINITION_CONST_INVALID")
        return value
    if op == "AND":
        args = expr.get("args")
        _require(isinstance(args, list) and args, "GATE_DEFINITION_ARGS_INVALID")
        return all(_evaluate(arg, assignment) for arg in args)
    if op == "OR":
        args = expr.get("args")
        _require(isinstance(args, list) and args, "GATE_DEFINITION_ARGS_INVALID")
        return any(_evaluate(arg, assignment) for arg in args)
    if op == "NOT":
        arg = expr.get("arg")
        _require(isinstance(arg, Mapping), "GATE_DEFINITION_NOT_ARG_INVALID")
        return not _evaluate(arg, assignment)
    raise GateLineageVerificationError(f"GATE_DEFINITION_OPERATOR_INVALID:{op}")


def verify_gate_lineage_transition(
    transition_hash: str,
    successor_required_gate_ids: set[str],
    resolver,
) -> dict[str, Any]:
    """Resolve and execute one gate replacement proof.

    v1 supports a deliberately restricted proof method: Boolean truth-table
    implication. Passing all successor predicates must imply passing the removed
    predecessor predicate. The verifier enumerates the full atom space itself.
    """
    transition = _resolved_obj(resolver, transition_hash, "AIFC/gate-lineage-transition/v1")
    removed_gate_id = transition.get("removed_gate_id")
    successor_gate_ids = transition.get("successor_gate_ids")
    _require(isinstance(removed_gate_id, str), "GATE_LINEAGE_REMOVED_ID_INVALID")
    _require(isinstance(successor_gate_ids, list) and successor_gate_ids, "GATE_LINEAGE_SUCCESSORS_INVALID")
    _require(removed_gate_id not in successor_required_gate_ids, "GATE_LINEAGE_REMOVED_GATE_STILL_MANDATORY")
    _require(
        all(isinstance(g, str) and g in successor_required_gate_ids for g in successor_gate_ids),
        "GATE_LINEAGE_SUCCESSOR_NOT_MANDATORY",
    )

    previous_hash = transition.get("previous_gate_definition_hash")
    successor_hashes = transition.get("successor_definition_hashes")
    evidence_hash = transition.get("equivalence_or_strengthening_evidence_hash")
    _require(isinstance(previous_hash, str), "GATE_LINEAGE_PREVIOUS_DEFINITION_HASH_INVALID")
    _require(isinstance(successor_hashes, list) and successor_hashes, "GATE_LINEAGE_SUCCESSOR_DEFINITION_HASHES_INVALID")
    _require(len(successor_hashes) == len(successor_gate_ids), "GATE_LINEAGE_SUCCESSOR_DEFINITION_COUNT_MISMATCH")
    _require(isinstance(evidence_hash, str), "GATE_LINEAGE_EVIDENCE_HASH_INVALID")

    previous = _resolved_obj(resolver, previous_hash, "AIFC/gate-definition/v1")
    _require(previous.get("gate_id") == removed_gate_id, "GATE_LINEAGE_PREDECESSOR_DEFINITION_REBINDING")

    successor_definitions: list[Mapping[str, Any]] = []
    for gate_id, definition_hash in zip(successor_gate_ids, successor_hashes):
        _require(isinstance(definition_hash, str), "GATE_LINEAGE_SUCCESSOR_DEFINITION_HASH_INVALID")
        definition = _resolved_obj(resolver, definition_hash, "AIFC/gate-definition/v1")
        _require(definition.get("gate_id") == gate_id, "GATE_LINEAGE_SUCCESSOR_DEFINITION_REBINDING")
        successor_definitions.append(definition)

    evidence = _resolved_obj(resolver, evidence_hash, "AIFC/gate-strengthening-evidence/v1")
    _require(evidence.get("proof_method") == "BOOLEAN_TRUTH_TABLE_IMPLICATION_V1", "GATE_LINEAGE_PROOF_METHOD_UNSUPPORTED")
    _require(evidence.get("removed_gate_id") == removed_gate_id, "GATE_LINEAGE_EVIDENCE_REMOVED_ID_REBINDING")
    _require(evidence.get("previous_gate_definition_hash") == previous_hash, "GATE_LINEAGE_EVIDENCE_PREDECESSOR_HASH_REBINDING")
    _require(evidence.get("successor_gate_ids") == successor_gate_ids, "GATE_LINEAGE_EVIDENCE_SUCCESSOR_ID_REBINDING")
    _require(evidence.get("successor_definition_hashes") == successor_hashes, "GATE_LINEAGE_EVIDENCE_SUCCESSOR_HASH_REBINDING")
    _require(evidence.get("claim") == "SUCCESSOR_CONJUNCTION_IMPLIES_PREDECESSOR", "GATE_LINEAGE_EVIDENCE_CLAIM_INVALID")

    previous_expr = previous.get("pass_condition")
    _require(isinstance(previous_expr, Mapping), "GATE_LINEAGE_PREDECESSOR_EXPRESSION_INVALID")
    successor_exprs: list[Mapping[str, Any]] = []
    atoms = _atoms(previous_expr)
    for definition in successor_definitions:
        expr = definition.get("pass_condition")
        _require(isinstance(expr, Mapping), "GATE_LINEAGE_SUCCESSOR_EXPRESSION_INVALID")
        successor_exprs.append(expr)
        atoms.update(_atoms(expr))

    declared_max = evidence.get("maximum_truth_table_atoms")
    _require(isinstance(declared_max, int), "GATE_LINEAGE_MAX_ATOMS_INVALID")
    _require(len(atoms) <= declared_max <= 16, "GATE_LINEAGE_TRUTH_TABLE_BOUND_EXCEEDED")

    atom_order = sorted(atoms)
    assignments_checked = 0
    for values in product((False, True), repeat=len(atom_order)):
        assignment = dict(zip(atom_order, values))
        assignments_checked += 1
        successors_pass = all(_evaluate(expr, assignment) for expr in successor_exprs)
        predecessor_pass = _evaluate(previous_expr, assignment)
        if successors_pass and not predecessor_pass:
            compact = ",".join(f"{k}={int(assignment[k])}" for k in atom_order)
            raise GateLineageVerificationError(
                f"GATE_STRENGTHENING_COUNTEREXAMPLE:{removed_gate_id}:{compact}"
            )

    return {
        "transition_hash": transition_hash,
        "removed_gate_id": removed_gate_id,
        "successor_gate_ids": list(successor_gate_ids),
        "previous_gate_definition_hash": previous_hash,
        "successor_definition_hashes": list(successor_hashes),
        "equivalence_or_strengthening_evidence_hash": evidence_hash,
        "proof_method": "BOOLEAN_TRUTH_TABLE_IMPLICATION_V1",
        "verification_status": "STRENGTHENING_CONFIRMED",
        "atom_count": len(atom_order),
        "assignments_checked": assignments_checked,
    }
