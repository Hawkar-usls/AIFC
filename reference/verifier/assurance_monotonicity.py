#!/usr/bin/env python3
"""AIFC assurance-monotonicity utilities.

This module does not decide scientific truth. It checks evolution invariants between
already-versioned verifier/release-gate layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


ADMISSION_RANK = {
    "INVALIDATED_EVIDENCE": 0,
    "NOT_ADMITTED": 1,
    "STRUCTURAL_MATCH_ONLY": 2,
    "FORWARD_NULL_CONSISTENT_MISS": 3,
    "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE": 3,
}

REJECTION_STATUSES = {"FAIL"}


class AssuranceMonotonicityError(ValueError):
    pass


@dataclass(frozen=True)
class MonotonicityComparison:
    status: str
    failure_codes: tuple[str, ...]


def _grade(result: Mapping[str, Any]) -> str:
    grade = result.get("terminal_grade")
    if grade not in ADMISSION_RANK:
        raise AssuranceMonotonicityError(f"UNKNOWN_TERMINAL_GRADE:{grade}")
    return str(grade)


def compare_verifier_results(
    predecessor: Mapping[str, Any],
    successor: Mapping[str, Any],
    inherited_gate_ids: Iterable[str],
) -> MonotonicityComparison:
    """Check no admission strengthening and no inherited FAIL-gate omission.

    BLOCKED -> PASS is allowed because a successor may implement a previously missing
    assurance gate. FAIL -> non-FAIL is not allowed for an inherited mandatory gate
    unless a separate normative transition explicitly supersedes that gate.
    """
    pred_grade = _grade(predecessor)
    succ_grade = _grade(successor)
    failures: list[str] = []

    if ADMISSION_RANK[succ_grade] > ADMISSION_RANK[pred_grade]:
        failures.append(
            f"SUCCESSOR_OUTCOME_STRONGER_THAN_PREDECESSOR:{pred_grade}:{succ_grade}"
        )

    pred_gates = predecessor.get("gate_results", {})
    succ_gates = successor.get("gate_results", {})
    if not isinstance(pred_gates, Mapping) or not isinstance(succ_gates, Mapping):
        raise AssuranceMonotonicityError("GATE_RESULTS_NOT_OBJECT")

    for gate_id in sorted(set(inherited_gate_ids)):
        pred_status = pred_gates.get(gate_id)
        succ_status = succ_gates.get(gate_id)
        if pred_status in REJECTION_STATUSES and succ_status != pred_status:
            failures.append(
                f"INHERITED_HARDENING_LAYER_OMISSION:{gate_id}:{pred_status}:{succ_status}"
            )

    return MonotonicityComparison(
        status="PASS" if not failures else "FAIL",
        failure_codes=tuple(failures),
    )


def required_gate_ids(gate_doc: Mapping[str, Any]) -> set[str]:
    rows = gate_doc.get("required_checks")
    if not isinstance(rows, list):
        raise AssuranceMonotonicityError("REQUIRED_CHECKS_NOT_ARRAY")
    ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or row.get("required") is not True:
            continue
        gate_id = row.get("id")
        if not isinstance(gate_id, str) or not gate_id:
            raise AssuranceMonotonicityError("REQUIRED_GATE_ID_INVALID")
        ids.append(gate_id)
    if len(ids) != len(set(ids)):
        raise AssuranceMonotonicityError("DUPLICATE_REQUIRED_GATE_ID")
    return set(ids)


def compare_release_gate_sets(
    predecessor_gate: Mapping[str, Any],
    successor_gate: Mapping[str, Any],
    lineage_transitions: Iterable[Mapping[str, Any]] = (),
) -> MonotonicityComparison:
    """Require G_n subseteq G_n+1 unless explicit transitions cover removals."""
    pred = required_gate_ids(predecessor_gate)
    succ = required_gate_ids(successor_gate)
    removed = set(pred - succ)
    if not removed:
        return MonotonicityComparison("PASS", ())

    covered: set[str] = set()
    for transition in lineage_transitions:
        if transition.get("schema") != "AIFC/gate-lineage-transition/v1":
            raise AssuranceMonotonicityError("GATE_LINEAGE_TRANSITION_SCHEMA_INVALID")
        removed_gate = transition.get("removed_gate_id")
        successors = transition.get("successor_gate_ids")
        evidence_hash = transition.get("equivalence_or_strengthening_evidence_hash")
        if not isinstance(removed_gate, str):
            raise AssuranceMonotonicityError("GATE_LINEAGE_REMOVED_ID_INVALID")
        if not isinstance(successors, list) or not successors:
            raise AssuranceMonotonicityError("GATE_LINEAGE_SUCCESSORS_INVALID")
        if not all(isinstance(x, str) and x in succ for x in successors):
            raise AssuranceMonotonicityError("GATE_LINEAGE_SUCCESSOR_NOT_MANDATORY")
        if not isinstance(evidence_hash, str) or len(evidence_hash) != 64:
            raise AssuranceMonotonicityError("GATE_LINEAGE_EVIDENCE_HASH_INVALID")
        covered.add(removed_gate)

    uncovered = sorted(removed - covered)
    if uncovered:
        return MonotonicityComparison(
            "FAIL",
            tuple(f"RELEASE_GATE_REGRESSION:{gate}" for gate in uncovered),
        )
    return MonotonicityComparison("PASS", ())


def compare_schema_identity(
    issued_record: Mapping[str, Any],
    *,
    current_schema_id: str,
    current_dialect: str,
    current_source_content_id: str,
    current_admission_semantics_version: str,
) -> MonotonicityComparison:
    """Detect same-ID schema acceptance-language mutation.

    Exact source bytes and validation-semantics identity are both inherited identity
    components. Any change under the same issued schema_id fails closed and requires
    a new schema identifier.
    """
    failures: list[str] = []
    if issued_record.get("schema_id") != current_schema_id:
        failures.append("SCHEMA_ID_REBINDING")
    if issued_record.get("dialect") != current_dialect:
        failures.append("SCHEMA_DIALECT_REBINDING")
    if issued_record.get("source_content_id") != current_source_content_id:
        failures.append("SAME_SCHEMA_ID_LANGUAGE_MUTATION:SOURCE_CHANGED")
    if issued_record.get("admission_semantics_version") != current_admission_semantics_version:
        failures.append("SAME_SCHEMA_ID_LANGUAGE_MUTATION:VALIDATOR_SEMANTICS_CHANGED")
    return MonotonicityComparison(
        "PASS" if not failures else "FAIL",
        tuple(failures),
    )
