#!/usr/bin/env python3
"""Scientific Assurance Lineage bootstrap utilities.

This module adds the first executable proof-anchoring boundary on top of
Assurance Convergence v1.1. Historical v1.1 APIs remain unchanged for replay.

The anchored path deliberately supports additive release-gate evolution first.
Gate removal/replacement remains blocked until historical gate-definition and
atom-semantics anchoring are separately established.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping

from canonical import CanonicalizationError, canonical_json_bytes, loads_strict


SAL_BOOTSTRAP_ROOT_COMMIT = "908de7afddcf9f72c98c2b3fb696a41be1e438e0"
NORMATIVE_ROOT_REGISTRY_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V1"
ADMISSION_ORDER_ARTIFACT_ID = "AIFC-ADMISSION-AUTHORITY-PARTIAL-ORDER-V1"
INHERITED_GATE_HASH_PROFILE_ID = "AIFC-INHERITED-GATE-OBLIGATION-HASH-V1"
INHERITED_GATE_HASH_DOMAIN = b"AIFC:INHERITED-GATE-OBLIGATION-SET:v1\x00"


class ScientificAssuranceLineageError(ValueError):
    pass


class NormativeIdentityError(ScientificAssuranceLineageError):
    pass


@dataclass(frozen=True)
class ResolvedNormativeObject:
    artifact_id: str
    kind: str
    expected_schema: str
    relative_path: str
    git_blob_sha1: str
    parsed_json: Mapping[str, Any]


@dataclass(frozen=True)
class AnchoredMonotonicityComparison:
    status: str
    failure_codes: tuple[str, ...]
    inherited_gate_set_hash: str
    inherited_gate_hash_profile_id: str
    predecessor_release_gate_git_blob_sha1: str
    successor_release_gate_git_blob_sha1: str
    admission_order_git_blob_sha1: str


def git_blob_sha1_bytes(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + raw).hexdigest()


def _safe_repo_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise NormativeIdentityError(f"NORMATIVE_OBJECT_PATH_ESCAPE:{relative_path}") from exc
    return candidate


def _strict_json_object(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
        parsed = loads_strict(text)
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise NormativeIdentityError(f"NORMATIVE_OBJECT_JSON_REJECTED:{label}:{exc}") from exc
    if not isinstance(parsed, Mapping):
        raise NormativeIdentityError(f"NORMATIVE_OBJECT_NOT_OBJECT:{label}")
    return parsed


class NormativeRepositoryResolver:
    """Resolve normative assurance objects from a bootstrap-rooted registry.

    The caller supplies an artifact identity, never a raw normative document.
    Each record binds the artifact identity to an exact repository path and Git
    blob content identity. The registry itself declares the exact historical
    bootstrap commit from which authority is inherited.
    """

    def __init__(self, root: Path, registry: Mapping[str, Any]):
        self.root = Path(root)
        if registry.get("schema") != "AIFC/normative-assurance-root-registry/v1":
            raise NormativeIdentityError("NORMATIVE_ROOT_REGISTRY_SCHEMA_INVALID")
        if registry.get("registry_id") != NORMATIVE_ROOT_REGISTRY_ID:
            raise NormativeIdentityError("NORMATIVE_ROOT_REGISTRY_ID_REBINDING")
        if registry.get("bootstrap_root_commit") != SAL_BOOTSTRAP_ROOT_COMMIT:
            raise NormativeIdentityError("NORMATIVE_ROOT_BOOTSTRAP_COMMIT_REBINDING")
        records = registry.get("records")
        if not isinstance(records, list) or not records:
            raise NormativeIdentityError("NORMATIVE_ROOT_REGISTRY_RECORDS_INVALID")
        index: dict[str, Mapping[str, Any]] = {}
        for record in records:
            if not isinstance(record, Mapping):
                raise NormativeIdentityError("NORMATIVE_ROOT_REGISTRY_RECORD_INVALID")
            artifact_id = record.get("artifact_id")
            if not isinstance(artifact_id, str) or not artifact_id:
                raise NormativeIdentityError("NORMATIVE_ROOT_ARTIFACT_ID_INVALID")
            if artifact_id in index:
                raise NormativeIdentityError(f"NORMATIVE_ROOT_DUPLICATE_ARTIFACT_ID:{artifact_id}")
            index[artifact_id] = record
        self.registry = registry
        self.records = index

    @classmethod
    def from_file(cls, root: Path, path: Path | None = None) -> "NormativeRepositoryResolver":
        root = Path(root)
        registry_path = path or root / "conformance" / "AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json"
        raw = registry_path.read_bytes()
        return cls(root, _strict_json_object(raw, str(registry_path)))

    def resolve(self, artifact_id: str, expected_kind: str | None = None) -> ResolvedNormativeObject:
        record = self.records.get(artifact_id)
        if record is None:
            raise NormativeIdentityError(f"NORMATIVE_OBJECT_ID_NOT_REGISTERED:{artifact_id}")
        kind = record.get("kind")
        expected_schema = record.get("expected_schema")
        relative_path = record.get("relative_path")
        expected_blob = record.get("git_blob_sha1")
        if not all(isinstance(x, str) and x for x in (kind, expected_schema, relative_path, expected_blob)):
            raise NormativeIdentityError(f"NORMATIVE_ROOT_RECORD_FIELDS_INVALID:{artifact_id}")
        if expected_kind is not None and kind != expected_kind:
            raise NormativeIdentityError(
                f"NORMATIVE_OBJECT_KIND_REBINDING:{artifact_id}:{expected_kind}:{kind}"
            )
        path = _safe_repo_path(self.root, relative_path)
        raw = path.read_bytes()
        actual_blob = git_blob_sha1_bytes(raw)
        if actual_blob != expected_blob:
            if kind == "RELEASE_GATE":
                code = "RELEASE_GATE_DOCUMENT_REBINDING"
            elif kind == "ADMISSION_ORDER":
                code = "SAME_ADMISSION_ORDER_ID_MUTATION"
            elif kind == "ASSURANCE_HASH_PROFILE":
                code = "ASSURANCE_HASH_PROFILE_SEMANTICS_MUTATION"
            elif kind == "INHERITED_GATE_HASH_PROFILE":
                code = "INHERITED_GATE_SET_HASH_SEMANTICS_DRIFT"
            else:
                code = "NORMATIVE_OBJECT_CONTENT_REBINDING"
            raise NormativeIdentityError(
                f"{code}:{artifact_id}:expected={expected_blob}:actual={actual_blob}"
            )
        parsed = _strict_json_object(raw, artifact_id)
        if parsed.get("schema") != expected_schema:
            raise NormativeIdentityError(
                f"NORMATIVE_OBJECT_SCHEMA_REBINDING:{artifact_id}:{expected_schema}:{parsed.get('schema')}"
            )
        return ResolvedNormativeObject(
            artifact_id=artifact_id,
            kind=str(kind),
            expected_schema=str(expected_schema),
            relative_path=str(relative_path),
            git_blob_sha1=str(actual_blob),
            parsed_json=parsed,
        )


def _required_gate_ids(gate_doc: Mapping[str, Any]) -> set[str]:
    rows = gate_doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageError("REQUIRED_CHECKS_NOT_ARRAY")
    ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or row.get("required") is not True:
            continue
        gate_id = row.get("id")
        if not isinstance(gate_id, str) or not gate_id:
            raise ScientificAssuranceLineageError("REQUIRED_GATE_ID_INVALID")
        ids.append(gate_id)
    if len(ids) != len(set(ids)):
        raise ScientificAssuranceLineageError("DUPLICATE_REQUIRED_GATE_ID")
    return set(ids)


def _admission_order(order: Mapping[str, Any]) -> dict[str, frozenset[str]]:
    if order.get("order_id") != ADMISSION_ORDER_ARTIFACT_ID:
        raise NormativeIdentityError("ADMISSION_ORDER_ID_REBINDING")
    raw = order.get("allowed_successor_outcomes")
    if not isinstance(raw, Mapping) or not raw:
        raise NormativeIdentityError("ADMISSION_ORDER_TABLE_INVALID")
    parsed: dict[str, frozenset[str]] = {}
    for predecessor, successors in raw.items():
        if not isinstance(predecessor, str) or not isinstance(successors, list):
            raise NormativeIdentityError("ADMISSION_ORDER_ROW_INVALID")
        if not all(isinstance(item, str) and item for item in successors):
            raise NormativeIdentityError(f"ADMISSION_ORDER_SUCCESSOR_INVALID:{predecessor}")
        parsed[predecessor] = frozenset(successors)
    return parsed


def inherited_gate_obligation_hash_v1(material: Mapping[str, Any]) -> str:
    """Domain-separated identity for derived inherited obligations.

    This intentionally does not extend AIFC/assurance-evidence-hash/v1.
    """
    if material.get("schema") != "AIFC/inherited-gate-obligation-set/v1":
        raise ScientificAssuranceLineageError("INHERITED_GATE_OBLIGATION_SCHEMA_INVALID")
    return hashlib.sha256(INHERITED_GATE_HASH_DOMAIN + canonical_json_bytes(material)).hexdigest()


def compare_verifier_results_anchored(
    predecessor: Mapping[str, Any],
    successor: Mapping[str, Any],
    *,
    predecessor_release_gate_id: str,
    successor_release_gate_id: str,
    normative_resolver: NormativeRepositoryResolver,
) -> AnchoredMonotonicityComparison:
    """Compare verifier results using resolver-derived normative documents.

    No release-gate document, inherited gate set, or admission-order table is
    accepted from the caller. v0.1 of the anchored path permits strict additive
    gate evolution. Any removal/replacement fails closed until gate-definition
    historical anchors and executable atom identities are available.
    """
    pred_gate = normative_resolver.resolve(predecessor_release_gate_id, "RELEASE_GATE")
    succ_gate = normative_resolver.resolve(successor_release_gate_id, "RELEASE_GATE")
    order_obj = normative_resolver.resolve(ADMISSION_ORDER_ARTIFACT_ID, "ADMISSION_ORDER")
    allowed = _admission_order(order_obj.parsed_json)

    pred_grade = predecessor.get("terminal_grade")
    succ_grade = successor.get("terminal_grade")
    if pred_grade not in allowed:
        raise ScientificAssuranceLineageError(f"UNKNOWN_PREDECESSOR_TERMINAL_GRADE:{pred_grade}")
    if succ_grade not in allowed:
        raise ScientificAssuranceLineageError(f"UNKNOWN_SUCCESSOR_TERMINAL_GRADE:{succ_grade}")

    failures: list[str] = []
    if succ_grade not in allowed[pred_grade]:
        pair = frozenset({str(pred_grade), str(succ_grade)})
        forward_pair = frozenset({
            "FORWARD_NULL_CONSISTENT_MISS",
            "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE",
        })
        if pred_grade == "FORWARD_NULL_CONSISTENT_MISS" and succ_grade == "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE":
            failures.append(f"SAME_RANK_AUTHORITY_ESCALATION:{pred_grade}:{succ_grade}")
        elif pair == forward_pair:
            failures.append(f"INCOMPARABLE_ADMISSION_OUTCOME_REWRITE:{pred_grade}:{succ_grade}")
        else:
            failures.append(f"SUCCESSOR_OUTCOME_STRONGER_THAN_PREDECESSOR:{pred_grade}:{succ_grade}")

    pred_ids = _required_gate_ids(pred_gate.parsed_json)
    succ_ids = _required_gate_ids(succ_gate.parsed_json)
    removed = sorted(pred_ids - succ_ids)
    for gate_id in removed:
        failures.append(f"GATE_DEFINITION_HISTORICAL_ANCHOR_NOT_ESTABLISHED:{gate_id}")
        failures.append(f"GATE_ATOM_SEMANTIC_IDENTITY_NOT_ESTABLISHED:{gate_id}")

    obligations = tuple({
        "predecessor_gate_id": gate_id,
        "successor_gate_ids": [gate_id],
        "transition_hash": None,
    } for gate_id in sorted(pred_ids & succ_ids))

    material = {
        "schema": "AIFC/inherited-gate-obligation-set/v1",
        "hash_profile_id": INHERITED_GATE_HASH_PROFILE_ID,
        "predecessor_release_gate_id": predecessor_release_gate_id,
        "predecessor_release_gate_git_blob_sha1": pred_gate.git_blob_sha1,
        "successor_release_gate_id": successor_release_gate_id,
        "successor_release_gate_git_blob_sha1": succ_gate.git_blob_sha1,
        "obligations": list(obligations),
    }
    inherited_hash = inherited_gate_obligation_hash_v1(material)

    pred_gates = predecessor.get("gate_results", {})
    succ_gates = successor.get("gate_results", {})
    if not isinstance(pred_gates, Mapping) or not isinstance(succ_gates, Mapping):
        raise ScientificAssuranceLineageError("GATE_RESULTS_NOT_OBJECT")

    for obligation in obligations:
        gate_id = obligation["predecessor_gate_id"]
        if pred_gates.get(gate_id) != "FAIL":
            continue
        if succ_gates.get(gate_id) != "FAIL":
            failures.append(
                f"INHERITED_HARDENING_LAYER_OMISSION:{gate_id}:FAIL:{gate_id}={succ_gates.get(gate_id)}"
            )

    return AnchoredMonotonicityComparison(
        status="PASS" if not failures else "FAIL",
        failure_codes=tuple(failures),
        inherited_gate_set_hash=inherited_hash,
        inherited_gate_hash_profile_id=INHERITED_GATE_HASH_PROFILE_ID,
        predecessor_release_gate_git_blob_sha1=pred_gate.git_blob_sha1,
        successor_release_gate_git_blob_sha1=succ_gate.git_blob_sha1,
        admission_order_git_blob_sha1=order_obj.git_blob_sha1,
    )
