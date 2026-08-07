#!/usr/bin/env python3
"""Scientific Assurance Lineage v1.3 root-closure path.

This successor deliberately leaves the v1.2 module unchanged. The v1.3 path
closes the next trust boundary:

    caller -> resolver -> registry -> normative object

The caller no longer supplies a resolver, repository root, registry Mapping or
registry path. The resolver loads one fixed repository registry whose own exact
Git blob identity is pinned by this implementation. Record authority_status is
executed as an admission condition. Unattested successor candidates fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping

from canonical import CanonicalizationError, loads_strict
from inherited_gate_hash_v1 import (
    INHERITED_GATE_HASH_PROFILE_ID,
    inherited_gate_obligation_hash_v1,
)
from schema_runtime import RuntimeSchemaError, validate_protocol_object

REPO_ROOT = Path(__file__).resolve().parents[2]

NORMATIVE_ROOT_REGISTRY_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V2"
NORMATIVE_ROOT_REGISTRY_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json"
NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1 = "3efcc12c293578bcbe8d4026f458463f956a2e14"

PREDECESSOR_NORMATIVE_ROOT_REGISTRY_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V1"
PREDECESSOR_NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1 = "0aec9d6ad0d54ce10d312d28a8cb0def1729f835"
PREDECESSOR_EXACT_MAIN_COMMIT = "7e58b47398fe585b24db6304ee6122871095d668"

AUTHORITY_RECEIPT_ID = "AIFC-SAL-V1.2-EXACT-MAIN-RECEIPT-7e58b47"
AUTHORITY_RECEIPT_PATH = "conformance/AIFC-NORMATIVE-AUTHORITY-RECEIPT-7e58b47-v1.json"
AUTHORITY_RECEIPT_GIT_BLOB_SHA1 = "49b54886f065ac42ee4ff22935112c60f44d4a6c"

ADMISSION_ORDER_ARTIFACT_ID = "AIFC-ADMISSION-AUTHORITY-PARTIAL-ORDER-V1"

_RUNTIME_SCHEMA_BY_KIND = {
    "ASSURANCE_HASH_PROFILE": "AIFC/assurance-hash-profile-manifest/v1",
    "INHERITED_GATE_HASH_PROFILE": "AIFC/inherited-gate-hash-profile/v1",
    "SCHEMA_IDENTITY_REGISTRY": "AIFC/schema-identity-registry/v3",
    "HASH_IMPLEMENTATION_BINDING": "AIFC/inherited-gate-hash-implementation-binding/v1",
}


class ScientificAssuranceLineageV13Error(ValueError):
    pass


class NormativeRootClosureError(ScientificAssuranceLineageV13Error):
    pass


@dataclass(frozen=True)
class ResolvedNormativeObjectV13:
    artifact_id: str
    kind: str
    expected_schema: str
    relative_path: str
    git_blob_sha1: str
    authority_status: str
    authority_commit: str
    authority_receipt_id: str | None
    parsed_json: Mapping[str, Any]


@dataclass(frozen=True)
class RootClosedMonotonicityComparison:
    status: str
    failure_codes: tuple[str, ...]
    inherited_gate_set_hash: str
    inherited_gate_hash_profile_id: str
    normative_root_registry_id: str
    normative_root_registry_git_blob_sha1: str
    predecessor_normative_root_registry_id: str
    predecessor_normative_root_registry_git_blob_sha1: str
    predecessor_exact_main_commit: str
    predecessor_release_gate_git_blob_sha1: str
    successor_release_gate_git_blob_sha1: str
    admission_order_git_blob_sha1: str


def git_blob_sha1_bytes(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + raw).hexdigest()


def _strict_json_object(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
        parsed = loads_strict(text)
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise NormativeRootClosureError(f"NORMATIVE_JSON_REJECTED:{label}:{exc}") from exc
    if not isinstance(parsed, Mapping):
        raise NormativeRootClosureError(f"NORMATIVE_JSON_NOT_OBJECT:{label}")
    return parsed


def _runtime_validate(value: Mapping[str, Any], expected_schema: str, label: str) -> None:
    try:
        validate_protocol_object(value, expected_schema)
    except RuntimeSchemaError as exc:
        raise NormativeRootClosureError(
            f"NORMATIVE_RUNTIME_SCHEMA_REJECTED:{label}:{exc}"
        ) from exc


def _read_content_identified_json(relative_path: str, expected_blob: str, label: str) -> Mapping[str, Any]:
    path = (REPO_ROOT / relative_path).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise NormativeRootClosureError(f"NORMATIVE_PATH_ESCAPE:{relative_path}") from exc
    raw = path.read_bytes()
    actual_blob = git_blob_sha1_bytes(raw)
    if actual_blob != expected_blob:
        raise NormativeRootClosureError(
            f"NORMATIVE_CONTENT_IDENTITY_MISMATCH:{label}:expected={expected_blob}:actual={actual_blob}"
        )
    return _strict_json_object(raw, label)


def _load_authority_receipt(receipt_id: str, authority_commit: str) -> Mapping[str, Any]:
    if receipt_id != AUTHORITY_RECEIPT_ID:
        raise NormativeRootClosureError(f"UNKNOWN_NORMATIVE_AUTHORITY_RECEIPT:{receipt_id}")
    receipt = _read_content_identified_json(
        AUTHORITY_RECEIPT_PATH,
        AUTHORITY_RECEIPT_GIT_BLOB_SHA1,
        receipt_id,
    )
    _runtime_validate(receipt, "AIFC/normative-authority-receipt/v1", receipt_id)
    if receipt.get("receipt_id") != receipt_id:
        raise NormativeRootClosureError(f"NORMATIVE_AUTHORITY_RECEIPT_ID_REBINDING:{receipt_id}")
    if receipt.get("tested_source_commit") != authority_commit:
        raise NormativeRootClosureError(
            f"NORMATIVE_AUTHORITY_RECEIPT_COMMIT_REBINDING:{receipt_id}:{authority_commit}"
        )
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise NormativeRootClosureError(f"NORMATIVE_AUTHORITY_RECEIPT_ARTIFACTS_INVALID:{receipt_id}")
    for artifact in artifacts:
        if not isinstance(artifact, Mapping) or artifact.get("head_sha") != authority_commit:
            raise NormativeRootClosureError(
                f"NORMATIVE_AUTHORITY_RECEIPT_HEAD_REBINDING:{receipt_id}"
            )
    return receipt


class RootClosedNormativeRepositoryResolver:
    """Repository-authoritative resolver with no caller-supplied root surface."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("CALLER_SUPPLIED_ROOT_REGISTRY_FORBIDDEN")

    @classmethod
    def from_repository_authority(cls) -> "RootClosedNormativeRepositoryResolver":
        registry = _read_content_identified_json(
            NORMATIVE_ROOT_REGISTRY_PATH,
            NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
            NORMATIVE_ROOT_REGISTRY_ID,
        )
        _runtime_validate(
            registry,
            "AIFC/normative-assurance-root-registry/v2",
            NORMATIVE_ROOT_REGISTRY_ID,
        )
        if registry.get("registry_id") != NORMATIVE_ROOT_REGISTRY_ID:
            raise NormativeRootClosureError("NORMATIVE_ROOT_REGISTRY_ID_REBINDING")
        if registry.get("predecessor_registry_id") != PREDECESSOR_NORMATIVE_ROOT_REGISTRY_ID:
            raise NormativeRootClosureError("PREDECESSOR_NORMATIVE_ROOT_REGISTRY_ID_REBINDING")
        if (
            registry.get("predecessor_registry_git_blob_sha1")
            != PREDECESSOR_NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1
        ):
            raise NormativeRootClosureError("PREDECESSOR_NORMATIVE_ROOT_REGISTRY_CONTENT_REBINDING")
        if registry.get("predecessor_exact_main_commit") != PREDECESSOR_EXACT_MAIN_COMMIT:
            raise NormativeRootClosureError("PREDECESSOR_EXACT_MAIN_COMMIT_REBINDING")

        records = registry.get("records")
        if not isinstance(records, list) or not records:
            raise NormativeRootClosureError("NORMATIVE_ROOT_REGISTRY_RECORDS_INVALID")
        index: dict[str, Mapping[str, Any]] = {}
        for record in records:
            if not isinstance(record, Mapping):
                raise NormativeRootClosureError("NORMATIVE_ROOT_REGISTRY_RECORD_INVALID")
            artifact_id = record.get("artifact_id")
            if not isinstance(artifact_id, str) or not artifact_id:
                raise NormativeRootClosureError("NORMATIVE_ROOT_ARTIFACT_ID_INVALID")
            if artifact_id in index:
                raise NormativeRootClosureError(f"NORMATIVE_ROOT_DUPLICATE_ARTIFACT_ID:{artifact_id}")
            index[artifact_id] = record

        self = object.__new__(cls)
        self.registry = registry
        self.records = index
        return self

    def _enforce_authority_status(self, artifact_id: str, record: Mapping[str, Any]) -> tuple[str, str | None]:
        status = record.get("authority_status")
        authority_commit = record.get("authority_commit")
        receipt_id = record.get("authority_receipt_id")

        if status == "HISTORICAL_ROOT_AT_PREDECESSOR_COMMIT":
            if authority_commit != PREDECESSOR_EXACT_MAIN_COMMIT or receipt_id is not None:
                raise NormativeRootClosureError(
                    f"HISTORICAL_ROOT_AUTHORITY_BINDING_INVALID:{artifact_id}"
                )
            return str(authority_commit), None

        if status == "ATTESTED_SUCCESSOR_AT_COMMIT":
            if not isinstance(authority_commit, str) or not isinstance(receipt_id, str):
                raise NormativeRootClosureError(
                    f"ATTESTED_SUCCESSOR_AUTHORITY_BINDING_INCOMPLETE:{artifact_id}"
                )
            _load_authority_receipt(receipt_id, authority_commit)
            return authority_commit, receipt_id

        if status == "SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION":
            raise NormativeRootClosureError(
                f"UNATTESTED_SUCCESSOR_NORMATIVE_PROMOTION:{artifact_id}"
            )

        raise NormativeRootClosureError(f"UNKNOWN_NORMATIVE_AUTHORITY_STATUS:{artifact_id}:{status}")

    def resolve(self, artifact_id: str, expected_kind: str | None = None) -> ResolvedNormativeObjectV13:
        record = self.records.get(artifact_id)
        if record is None:
            raise NormativeRootClosureError(f"NORMATIVE_OBJECT_ID_NOT_REGISTERED:{artifact_id}")
        kind = record.get("kind")
        expected_schema = record.get("expected_schema")
        relative_path = record.get("relative_path")
        expected_blob = record.get("git_blob_sha1")
        if not all(isinstance(x, str) and x for x in (kind, expected_schema, relative_path, expected_blob)):
            raise NormativeRootClosureError(f"NORMATIVE_ROOT_RECORD_FIELDS_INVALID:{artifact_id}")
        if expected_kind is not None and kind != expected_kind:
            raise NormativeRootClosureError(
                f"NORMATIVE_OBJECT_KIND_REBINDING:{artifact_id}:{expected_kind}:{kind}"
            )

        authority_commit, receipt_id = self._enforce_authority_status(artifact_id, record)
        parsed = _read_content_identified_json(str(relative_path), str(expected_blob), artifact_id)
        if parsed.get("schema") != expected_schema:
            raise NormativeRootClosureError(
                f"NORMATIVE_OBJECT_SCHEMA_REBINDING:{artifact_id}:{expected_schema}:{parsed.get('schema')}"
            )
        runtime_schema = _RUNTIME_SCHEMA_BY_KIND.get(str(kind))
        if runtime_schema is not None:
            _runtime_validate(parsed, runtime_schema, artifact_id)

        return ResolvedNormativeObjectV13(
            artifact_id=artifact_id,
            kind=str(kind),
            expected_schema=str(expected_schema),
            relative_path=str(relative_path),
            git_blob_sha1=str(expected_blob),
            authority_status=str(record.get("authority_status")),
            authority_commit=authority_commit,
            authority_receipt_id=receipt_id,
            parsed_json=parsed,
        )


def _required_gate_ids(gate_doc: Mapping[str, Any]) -> set[str]:
    rows = gate_doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageV13Error("REQUIRED_CHECKS_NOT_ARRAY")
    ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or row.get("required") is not True:
            continue
        gate_id = row.get("id")
        if not isinstance(gate_id, str) or not gate_id:
            raise ScientificAssuranceLineageV13Error("REQUIRED_GATE_ID_INVALID")
        ids.append(gate_id)
    if len(ids) != len(set(ids)):
        raise ScientificAssuranceLineageV13Error("DUPLICATE_REQUIRED_GATE_ID")
    return set(ids)


def _admission_order(order: Mapping[str, Any]) -> dict[str, frozenset[str]]:
    if order.get("order_id") != ADMISSION_ORDER_ARTIFACT_ID:
        raise NormativeRootClosureError("ADMISSION_ORDER_ID_REBINDING")
    raw = order.get("allowed_successor_outcomes")
    if not isinstance(raw, Mapping) or not raw:
        raise NormativeRootClosureError("ADMISSION_ORDER_TABLE_INVALID")
    parsed: dict[str, frozenset[str]] = {}
    for predecessor, successors in raw.items():
        if not isinstance(predecessor, str) or not isinstance(successors, list):
            raise NormativeRootClosureError("ADMISSION_ORDER_ROW_INVALID")
        if not all(isinstance(item, str) and item for item in successors):
            raise NormativeRootClosureError(f"ADMISSION_ORDER_SUCCESSOR_INVALID:{predecessor}")
        parsed[predecessor] = frozenset(successors)
    return parsed


def compare_verifier_results_root_closed(
    predecessor: Mapping[str, Any],
    successor: Mapping[str, Any],
    *,
    predecessor_release_gate_id: str,
    successor_release_gate_id: str,
) -> RootClosedMonotonicityComparison:
    """Compare using the repository-authoritative, content-identified resolver.

    There is intentionally no normative_resolver, registry, registry_path or
    repository_root parameter.
    """
    resolver = RootClosedNormativeRepositoryResolver.from_repository_authority()
    pred_gate = resolver.resolve(predecessor_release_gate_id, "RELEASE_GATE")
    succ_gate = resolver.resolve(successor_release_gate_id, "RELEASE_GATE")
    order_obj = resolver.resolve(ADMISSION_ORDER_ARTIFACT_ID, "ADMISSION_ORDER")
    allowed = _admission_order(order_obj.parsed_json)

    pred_grade = predecessor.get("terminal_grade")
    succ_grade = successor.get("terminal_grade")
    if pred_grade not in allowed:
        raise ScientificAssuranceLineageV13Error(f"UNKNOWN_PREDECESSOR_TERMINAL_GRADE:{pred_grade}")
    if succ_grade not in allowed:
        raise ScientificAssuranceLineageV13Error(f"UNKNOWN_SUCCESSOR_TERMINAL_GRADE:{succ_grade}")

    failures: list[str] = []
    if succ_grade not in allowed[pred_grade]:
        if pred_grade == "FORWARD_NULL_CONSISTENT_MISS" and succ_grade == "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE":
            failures.append(f"SAME_RANK_AUTHORITY_ESCALATION:{pred_grade}:{succ_grade}")
        elif frozenset({str(pred_grade), str(succ_grade)}) == frozenset({
            "FORWARD_NULL_CONSISTENT_MISS",
            "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE",
        }):
            failures.append(f"INCOMPARABLE_ADMISSION_OUTCOME_REWRITE:{pred_grade}:{succ_grade}")
        else:
            failures.append(f"SUCCESSOR_OUTCOME_STRONGER_THAN_PREDECESSOR:{pred_grade}:{succ_grade}")

    pred_ids = _required_gate_ids(pred_gate.parsed_json)
    succ_ids = _required_gate_ids(succ_gate.parsed_json)
    removed = sorted(pred_ids - succ_ids)
    for gate_id in removed:
        failures.append(f"GATE_DEFINITION_HISTORICAL_ANCHOR_NOT_ESTABLISHED:{gate_id}")
        failures.append(f"GATE_ATOM_SEMANTIC_IDENTITY_NOT_ESTABLISHED:{gate_id}")

    obligations = [
        {
            "predecessor_gate_id": gate_id,
            "successor_gate_ids": [gate_id],
            "transition_hash": None,
        }
        for gate_id in sorted(pred_ids & succ_ids)
    ]
    material = {
        "schema": "AIFC/inherited-gate-obligation-set/v1",
        "hash_profile_id": INHERITED_GATE_HASH_PROFILE_ID,
        "predecessor_release_gate_id": predecessor_release_gate_id,
        "predecessor_release_gate_git_blob_sha1": pred_gate.git_blob_sha1,
        "successor_release_gate_id": successor_release_gate_id,
        "successor_release_gate_git_blob_sha1": succ_gate.git_blob_sha1,
        "obligations": obligations,
    }
    inherited_hash = inherited_gate_obligation_hash_v1(material)

    pred_gates = predecessor.get("gate_results", {})
    succ_gates = successor.get("gate_results", {})
    if not isinstance(pred_gates, Mapping) or not isinstance(succ_gates, Mapping):
        raise ScientificAssuranceLineageV13Error("GATE_RESULTS_NOT_OBJECT")
    for obligation in obligations:
        gate_id = obligation["predecessor_gate_id"]
        if pred_gates.get(gate_id) == "FAIL" and succ_gates.get(gate_id) != "FAIL":
            failures.append(
                f"INHERITED_HARDENING_LAYER_OMISSION:{gate_id}:FAIL:{gate_id}={succ_gates.get(gate_id)}"
            )

    return RootClosedMonotonicityComparison(
        status="PASS" if not failures else "FAIL",
        failure_codes=tuple(failures),
        inherited_gate_set_hash=inherited_hash,
        inherited_gate_hash_profile_id=INHERITED_GATE_HASH_PROFILE_ID,
        normative_root_registry_id=NORMATIVE_ROOT_REGISTRY_ID,
        normative_root_registry_git_blob_sha1=NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
        predecessor_normative_root_registry_id=PREDECESSOR_NORMATIVE_ROOT_REGISTRY_ID,
        predecessor_normative_root_registry_git_blob_sha1=PREDECESSOR_NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
        predecessor_exact_main_commit=PREDECESSOR_EXACT_MAIN_COMMIT,
        predecessor_release_gate_git_blob_sha1=pred_gate.git_blob_sha1,
        successor_release_gate_git_blob_sha1=succ_gate.git_blob_sha1,
        admission_order_git_blob_sha1=order_obj.git_blob_sha1,
    )


def build_assurance_monotonicity_record_v4(
    comparison: RootClosedMonotonicityComparison,
    *,
    predecessor_verifier: str,
    successor_verifier: str,
    predecessor_release_gate_id: str,
    successor_release_gate_id: str,
) -> Mapping[str, Any]:
    value = {
        "schema": "AIFC/assurance-monotonicity-record/v4",
        "predecessor_verifier": predecessor_verifier,
        "successor_verifier": successor_verifier,
        "normative_root_registry_id": comparison.normative_root_registry_id,
        "normative_root_registry_git_blob_sha1": comparison.normative_root_registry_git_blob_sha1,
        "predecessor_normative_root_registry_id": comparison.predecessor_normative_root_registry_id,
        "predecessor_normative_root_registry_git_blob_sha1": comparison.predecessor_normative_root_registry_git_blob_sha1,
        "predecessor_exact_main_commit": comparison.predecessor_exact_main_commit,
        "predecessor_release_gate_id": predecessor_release_gate_id,
        "predecessor_release_gate_git_blob_sha1": comparison.predecessor_release_gate_git_blob_sha1,
        "successor_release_gate_id": successor_release_gate_id,
        "successor_release_gate_git_blob_sha1": comparison.successor_release_gate_git_blob_sha1,
        "admission_order_id": ADMISSION_ORDER_ARTIFACT_ID,
        "admission_order_git_blob_sha1": comparison.admission_order_git_blob_sha1,
        "inherited_gate_hash_profile_id": comparison.inherited_gate_hash_profile_id,
        "inherited_gate_set_hash": comparison.inherited_gate_set_hash,
        "authority_status_enforced": True,
        "resolver_provenance_closed": True,
        "monotonicity_result": comparison.status,
        "failure_codes": list(comparison.failure_codes),
    }
    _runtime_validate(value, "AIFC/assurance-monotonicity-record/v4", "ASSURANCE_MONOTONICITY_RECORD_V4")
    return value
