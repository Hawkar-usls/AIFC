#!/usr/bin/env python3
"""AIFC assurance-convergence utilities.

This module checks verifier/protocol evolution invariants. It does not decide
scientific truth and does not allow a successor to define its own inherited
assurance obligations.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


ADMISSION_ALLOWED_SUCCESSORS: dict[str, frozenset[str]] = {
    "INVALIDATED_EVIDENCE": frozenset({
        "INVALIDATED_EVIDENCE",
    }),
    "NOT_ADMITTED": frozenset({
        "INVALIDATED_EVIDENCE",
        "NOT_ADMITTED",
    }),
    "STRUCTURAL_MATCH_ONLY": frozenset({
        "INVALIDATED_EVIDENCE",
        "NOT_ADMITTED",
        "STRUCTURAL_MATCH_ONLY",
    }),
    "FORWARD_NULL_CONSISTENT_MISS": frozenset({
        "INVALIDATED_EVIDENCE",
        "NOT_ADMITTED",
        "STRUCTURAL_MATCH_ONLY",
        "FORWARD_NULL_CONSISTENT_MISS",
    }),
    "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE": frozenset({
        "INVALIDATED_EVIDENCE",
        "NOT_ADMITTED",
        "STRUCTURAL_MATCH_ONLY",
        "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE",
    }),
}

FORWARD_NULL_INCOMPARABLE_PAIR = frozenset({
    "FORWARD_NULL_CONSISTENT_MISS",
    "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE",
})
REJECTION_STATUSES = {"FAIL"}


class AssuranceMonotonicityError(ValueError):
    pass


@dataclass(frozen=True)
class MonotonicityComparison:
    status: str
    failure_codes: tuple[str, ...]
    inherited_gate_set_hash: str | None = None


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def document_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _grade(result: Mapping[str, Any]) -> str:
    grade = result.get("terminal_grade")
    if grade not in ADMISSION_ALLOWED_SUCCESSORS:
        raise AssuranceMonotonicityError(f"UNKNOWN_TERMINAL_GRADE:{grade}")
    return str(grade)


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


def _verified_transition_index(
    verified_transitions: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Mapping[str, Any]], list[str]]:
    index: dict[str, Mapping[str, Any]] = {}
    failures: list[str] = []
    for transition in verified_transitions:
        removed_gate = transition.get("removed_gate_id")
        if not isinstance(removed_gate, str) or not removed_gate:
            raise AssuranceMonotonicityError("GATE_LINEAGE_REMOVED_ID_INVALID")
        if transition.get("verification_status") != "STRENGTHENING_CONFIRMED":
            failures.append(f"FAKE_GATE_STRENGTHENING_RECEIPT:{removed_gate}")
            continue
        successors = transition.get("successor_gate_ids")
        transition_hash = transition.get("transition_hash")
        if not isinstance(successors, list) or not successors or not all(isinstance(x, str) and x for x in successors):
            raise AssuranceMonotonicityError("GATE_LINEAGE_SUCCESSORS_INVALID")
        if not isinstance(transition_hash, str) or len(transition_hash) != 64:
            raise AssuranceMonotonicityError("GATE_LINEAGE_VERIFIED_TRANSITION_HASH_INVALID")
        if removed_gate in index:
            raise AssuranceMonotonicityError(f"DUPLICATE_VERIFIED_GATE_TRANSITION:{removed_gate}")
        index[removed_gate] = transition
    return index, failures


def compare_release_gate_sets(
    predecessor_gate: Mapping[str, Any],
    successor_gate: Mapping[str, Any],
    verified_transitions: Iterable[Mapping[str, Any]] = (),
) -> MonotonicityComparison:
    """Require G_n subseteq G_n+1 unless a proof-replayed transition covers removal."""
    pred = required_gate_ids(predecessor_gate)
    succ = required_gate_ids(successor_gate)
    transition_index, failures = _verified_transition_index(verified_transitions)

    for removed_gate in sorted(pred - succ):
        transition = transition_index.get(removed_gate)
        if transition is None:
            failures.append(f"RELEASE_GATE_REGRESSION:{removed_gate}")
            continue
        successors = transition["successor_gate_ids"]
        if not all(gate_id in succ for gate_id in successors):
            failures.append(f"GATE_LINEAGE_SUCCESSOR_NOT_MANDATORY:{removed_gate}")

    return MonotonicityComparison(
        "PASS" if not failures else "FAIL",
        tuple(failures),
    )


def derive_inherited_gate_obligations(
    predecessor_gate: Mapping[str, Any],
    successor_gate: Mapping[str, Any],
    verified_transitions: Iterable[Mapping[str, Any]] = (),
) -> tuple[tuple[dict[str, Any], ...], str]:
    """Derive inherited obligations from release gates; callers cannot supply the set.

    For an unchanged gate, its successor obligation is the same gate ID. For a
    removed gate, only a proof-replayed strengthening transition may map the
    predecessor obligation onto one or more mandatory successor gates.
    """
    gate_comparison = compare_release_gate_sets(predecessor_gate, successor_gate, verified_transitions)
    if gate_comparison.status != "PASS":
        raise AssuranceMonotonicityError(
            "INHERITED_GATE_SET_DERIVATION_FAILED:" + ",".join(gate_comparison.failure_codes)
        )

    pred = required_gate_ids(predecessor_gate)
    succ = required_gate_ids(successor_gate)
    transition_index, failures = _verified_transition_index(verified_transitions)
    if failures:
        raise AssuranceMonotonicityError("INHERITED_GATE_SET_DERIVATION_FAILED:" + ",".join(failures))

    obligations: list[dict[str, Any]] = []
    for gate_id in sorted(pred):
        if gate_id in succ:
            successors = [gate_id]
            transition_hash = None
        else:
            transition = transition_index[gate_id]
            successors = sorted(set(transition["successor_gate_ids"]))
            transition_hash = transition["transition_hash"]
        obligations.append({
            "predecessor_gate_id": gate_id,
            "successor_gate_ids": successors,
            "transition_hash": transition_hash,
        })

    material = {
        "schema": "AIFC/inherited-gate-obligation-set/v1",
        "predecessor_release_gate_sha256": document_sha256(predecessor_gate),
        "successor_release_gate_sha256": document_sha256(successor_gate),
        "obligations": obligations,
    }
    inherited_hash = hashlib.sha256(_canonical_json_bytes(material)).hexdigest()
    return tuple(obligations), inherited_hash


def compare_verifier_results(
    predecessor: Mapping[str, Any],
    successor: Mapping[str, Any],
    predecessor_release_gate: Mapping[str, Any],
    successor_release_gate: Mapping[str, Any],
    verified_transitions: Iterable[Mapping[str, Any]] = (),
) -> MonotonicityComparison:
    """Check exact admission partial order and derived inherited FAIL preservation.

    The inherited gate domain is derived from the predecessor release gate and
    proof-replayed lineage transitions. There is intentionally no caller-supplied
    inherited_gate_ids argument.
    """
    pred_grade = _grade(predecessor)
    succ_grade = _grade(successor)
    failures: list[str] = []

    if succ_grade not in ADMISSION_ALLOWED_SUCCESSORS[pred_grade]:
        if pred_grade == "FORWARD_NULL_CONSISTENT_MISS" and succ_grade == "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE":
            failures.append(f"SAME_RANK_AUTHORITY_ESCALATION:{pred_grade}:{succ_grade}")
        elif frozenset({pred_grade, succ_grade}) == FORWARD_NULL_INCOMPARABLE_PAIR:
            failures.append(f"INCOMPARABLE_ADMISSION_OUTCOME_REWRITE:{pred_grade}:{succ_grade}")
        else:
            failures.append(f"SUCCESSOR_OUTCOME_STRONGER_THAN_PREDECESSOR:{pred_grade}:{succ_grade}")

    obligations, inherited_hash = derive_inherited_gate_obligations(
        predecessor_release_gate,
        successor_release_gate,
        verified_transitions,
    )

    pred_gates = predecessor.get("gate_results", {})
    succ_gates = successor.get("gate_results", {})
    if not isinstance(pred_gates, Mapping) or not isinstance(succ_gates, Mapping):
        raise AssuranceMonotonicityError("GATE_RESULTS_NOT_OBJECT")

    for obligation in obligations:
        gate_id = obligation["predecessor_gate_id"]
        pred_status = pred_gates.get(gate_id)
        if pred_status not in REJECTION_STATUSES:
            continue
        successor_ids = obligation["successor_gate_ids"]
        successor_statuses = {sid: succ_gates.get(sid) for sid in successor_ids}
        if not any(status in REJECTION_STATUSES for status in successor_statuses.values()):
            rendered = ";".join(f"{sid}={successor_statuses[sid]}" for sid in successor_ids)
            failures.append(
                f"INHERITED_HARDENING_LAYER_OMISSION:{gate_id}:{pred_status}:{rendered}"
            )

    return MonotonicityComparison(
        status="PASS" if not failures else "FAIL",
        failure_codes=tuple(failures),
        inherited_gate_set_hash=inherited_hash,
    )


def compare_schema_identity(
    issued_record: Mapping[str, Any],
    *,
    current_schema_id: str,
    current_dialect: str,
    current_git_blob_sha1: str | None = None,
    current_raw_schema_sha256: str | None = None,
    current_admission_semantics_id: str | None = None,
    current_admission_semantics_content_hash: str | None = None,
    # v1 compatibility inputs retained only for historical checker replay.
    current_source_content_id: str | None = None,
    current_admission_semantics_version: str | None = None,
) -> MonotonicityComparison:
    """Detect same-ID acceptance-language or validator-semantics mutation."""
    failures: list[str] = []
    if issued_record.get("schema_id") != current_schema_id:
        failures.append("SCHEMA_ID_REBINDING")
    if issued_record.get("dialect") != current_dialect:
        failures.append("SCHEMA_DIALECT_REBINDING")

    if issued_record.get("schema") == "AIFC/schema-identity-record/v2":
        if issued_record.get("git_blob_sha1") != current_git_blob_sha1:
            failures.append("SAME_SCHEMA_ID_LANGUAGE_MUTATION:GIT_BLOB_CHANGED")
        if issued_record.get("raw_schema_sha256") != current_raw_schema_sha256:
            failures.append("SAME_SCHEMA_ID_LANGUAGE_MUTATION:RAW_SHA256_CHANGED")
        if issued_record.get("admission_semantics_id") != current_admission_semantics_id:
            failures.append("SAME_SCHEMA_ID_LANGUAGE_MUTATION:VALIDATOR_SEMANTICS_ID_CHANGED")
        if issued_record.get("admission_semantics_content_hash") != current_admission_semantics_content_hash:
            failures.append("VALIDATOR_IMPLEMENTATION_CHANGED_WITH_SAME_SEMANTICS_ID")
    else:
        if issued_record.get("source_content_id") != current_source_content_id:
            failures.append("SAME_SCHEMA_ID_LANGUAGE_MUTATION:SOURCE_CHANGED")
        if issued_record.get("admission_semantics_version") != current_admission_semantics_version:
            failures.append("SAME_SCHEMA_ID_LANGUAGE_MUTATION:VALIDATOR_SEMANTICS_CHANGED")

    return MonotonicityComparison(
        "PASS" if not failures else "FAIL",
        tuple(failures),
    )
