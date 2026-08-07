#!/usr/bin/env python3
"""Scientific Assurance Lineage v1.3 root-closure path.

v1.2 remains historical. v1.3 closes caller -> resolver -> registry injection:
callers supply only artifact IDs. One fixed repository registry is loaded, its
own exact content identity is pinned here, and authority_status is executed.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping

from canonical import CanonicalizationError, loads_strict
from inherited_gate_hash_v1 import INHERITED_GATE_HASH_PROFILE_ID, inherited_gate_obligation_hash_v1
from schema_runtime import RuntimeSchemaError, validate_protocol_object

REPO_ROOT = Path(__file__).resolve().parents[2]
NORMATIVE_ROOT_REGISTRY_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V2"
NORMATIVE_ROOT_REGISTRY_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json"
NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1 = "d2bb7f3917f8761836825a4e80f03c1e282fc37d"
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
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()


def _strict_object(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        value = loads_strict(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise NormativeRootClosureError(f"NORMATIVE_JSON_REJECTED:{label}:{exc}") from exc
    if not isinstance(value, Mapping):
        raise NormativeRootClosureError(f"NORMATIVE_JSON_NOT_OBJECT:{label}")
    return value


def _validate(value: Mapping[str, Any], schema: str, label: str) -> None:
    try:
        validate_protocol_object(value, schema)
    except RuntimeSchemaError as exc:
        raise NormativeRootClosureError(f"NORMATIVE_RUNTIME_SCHEMA_REJECTED:{label}:{exc}") from exc


def _read_bound_json(path_text: str, expected_blob: str, label: str) -> Mapping[str, Any]:
    path = (REPO_ROOT / path_text).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise NormativeRootClosureError(f"NORMATIVE_PATH_ESCAPE:{path_text}") from exc
    raw = path.read_bytes()
    actual = git_blob_sha1_bytes(raw)
    if actual != expected_blob:
        raise NormativeRootClosureError(
            f"NORMATIVE_CONTENT_IDENTITY_MISMATCH:{label}:expected={expected_blob}:actual={actual}"
        )
    return _strict_object(raw, label)


def _load_authority_receipt(receipt_id: str, commit: str) -> Mapping[str, Any]:
    if receipt_id != AUTHORITY_RECEIPT_ID:
        raise NormativeRootClosureError(f"UNKNOWN_NORMATIVE_AUTHORITY_RECEIPT:{receipt_id}")
    receipt = _read_bound_json(AUTHORITY_RECEIPT_PATH, AUTHORITY_RECEIPT_GIT_BLOB_SHA1, receipt_id)
    _validate(receipt, "AIFC/normative-authority-receipt/v1", receipt_id)
    if receipt.get("receipt_id") != receipt_id or receipt.get("tested_source_commit") != commit:
        raise NormativeRootClosureError(f"NORMATIVE_AUTHORITY_RECEIPT_REBINDING:{receipt_id}")
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise NormativeRootClosureError(f"NORMATIVE_AUTHORITY_RECEIPT_ARTIFACTS_INVALID:{receipt_id}")
    if any(not isinstance(a, Mapping) or a.get("head_sha") != commit for a in artifacts):
        raise NormativeRootClosureError(f"NORMATIVE_AUTHORITY_RECEIPT_HEAD_REBINDING:{receipt_id}")
    return receipt


class RootClosedNormativeRepositoryResolver:
    """No public constructor accepts a root, path, registry or Mapping."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("CALLER_SUPPLIED_ROOT_REGISTRY_FORBIDDEN")

    @classmethod
    def from_repository_authority(cls) -> "RootClosedNormativeRepositoryResolver":
        registry = _read_bound_json(
            NORMATIVE_ROOT_REGISTRY_PATH,
            NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
            NORMATIVE_ROOT_REGISTRY_ID,
        )
        _validate(registry, "AIFC/normative-assurance-root-registry/v2", NORMATIVE_ROOT_REGISTRY_ID)
        checks = {
            "registry_id": NORMATIVE_ROOT_REGISTRY_ID,
            "predecessor_registry_id": PREDECESSOR_NORMATIVE_ROOT_REGISTRY_ID,
            "predecessor_registry_git_blob_sha1": PREDECESSOR_NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
            "predecessor_exact_main_commit": PREDECESSOR_EXACT_MAIN_COMMIT,
        }
        for key, expected in checks.items():
            if registry.get(key) != expected:
                raise NormativeRootClosureError(f"NORMATIVE_ROOT_REGISTRY_REBINDING:{key}")
        rows = registry.get("records")
        if not isinstance(rows, list) or not rows:
            raise NormativeRootClosureError("NORMATIVE_ROOT_REGISTRY_RECORDS_INVALID")
        index: dict[str, Mapping[str, Any]] = {}
        for row in rows:
            if not isinstance(row, Mapping):
                raise NormativeRootClosureError("NORMATIVE_ROOT_REGISTRY_RECORD_INVALID")
            artifact_id = row.get("artifact_id")
            if not isinstance(artifact_id, str) or not artifact_id or artifact_id in index:
                raise NormativeRootClosureError(f"NORMATIVE_ROOT_ARTIFACT_ID_INVALID:{artifact_id}")
            index[artifact_id] = row
        self = object.__new__(cls)
        self.registry = registry
        self.records = index
        return self

    def _authority(self, artifact_id: str, row: Mapping[str, Any]) -> tuple[str, str | None]:
        status, commit, receipt = (
            row.get("authority_status"),
            row.get("authority_commit"),
            row.get("authority_receipt_id"),
        )
        if status == "HISTORICAL_ROOT_AT_PREDECESSOR_COMMIT":
            if commit != PREDECESSOR_EXACT_MAIN_COMMIT or receipt is not None:
                raise NormativeRootClosureError(f"HISTORICAL_ROOT_AUTHORITY_BINDING_INVALID:{artifact_id}")
            return str(commit), None
        if status == "ATTESTED_SUCCESSOR_AT_COMMIT":
            if not isinstance(commit, str) or not isinstance(receipt, str):
                raise NormativeRootClosureError(f"ATTESTED_SUCCESSOR_AUTHORITY_BINDING_INCOMPLETE:{artifact_id}")
            _load_authority_receipt(receipt, commit)
            return commit, receipt
        if status == "SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION":
            raise NormativeRootClosureError(f"UNATTESTED_SUCCESSOR_NORMATIVE_PROMOTION:{artifact_id}")
        raise NormativeRootClosureError(f"UNKNOWN_NORMATIVE_AUTHORITY_STATUS:{artifact_id}:{status}")

    def resolve(self, artifact_id: str, expected_kind: str | None = None) -> ResolvedNormativeObjectV13:
        row = self.records.get(artifact_id)
        if row is None:
            raise NormativeRootClosureError(f"NORMATIVE_OBJECT_ID_NOT_REGISTERED:{artifact_id}")
        kind, schema, path, blob = (
            row.get("kind"), row.get("expected_schema"), row.get("relative_path"), row.get("git_blob_sha1")
        )
        if not all(isinstance(x, str) and x for x in (kind, schema, path, blob)):
            raise NormativeRootClosureError(f"NORMATIVE_ROOT_RECORD_FIELDS_INVALID:{artifact_id}")
        if expected_kind is not None and kind != expected_kind:
            raise NormativeRootClosureError(f"NORMATIVE_OBJECT_KIND_REBINDING:{artifact_id}:{expected_kind}:{kind}")
        commit, receipt = self._authority(artifact_id, row)
        parsed = _read_bound_json(str(path), str(blob), artifact_id)
        if parsed.get("schema") != schema:
            raise NormativeRootClosureError(f"NORMATIVE_OBJECT_SCHEMA_REBINDING:{artifact_id}:{schema}")
        runtime_schema = _RUNTIME_SCHEMA_BY_KIND.get(str(kind))
        if runtime_schema:
            _validate(parsed, runtime_schema, artifact_id)
        return ResolvedNormativeObjectV13(
            artifact_id, str(kind), str(schema), str(path), str(blob), str(row.get("authority_status")),
            commit, receipt, parsed
        )


def _required_gate_ids(doc: Mapping[str, Any]) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageV13Error("REQUIRED_CHECKS_NOT_ARRAY")
    ids = [r.get("id") for r in rows if isinstance(r, Mapping) and r.get("required") is True]
    if not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids)):
        raise ScientificAssuranceLineageV13Error("REQUIRED_GATE_IDS_INVALID")
    return set(ids)


def _admission_order(doc: Mapping[str, Any]) -> dict[str, frozenset[str]]:
    if doc.get("order_id") != ADMISSION_ORDER_ARTIFACT_ID:
        raise NormativeRootClosureError("ADMISSION_ORDER_ID_REBINDING")
    raw = doc.get("allowed_successor_outcomes")
    if not isinstance(raw, Mapping) or not raw:
        raise NormativeRootClosureError("ADMISSION_ORDER_TABLE_INVALID")
    out: dict[str, frozenset[str]] = {}
    for pred, succs in raw.items():
        if not isinstance(pred, str) or not isinstance(succs, list) or not all(isinstance(x, str) for x in succs):
            raise NormativeRootClosureError("ADMISSION_ORDER_ROW_INVALID")
        out[pred] = frozenset(succs)
    return out


def compare_verifier_results_root_closed(
    predecessor: Mapping[str, Any],
    successor: Mapping[str, Any],
    *,
    predecessor_release_gate_id: str,
    successor_release_gate_id: str,
) -> RootClosedMonotonicityComparison:
    resolver = RootClosedNormativeRepositoryResolver.from_repository_authority()
    pred_gate = resolver.resolve(predecessor_release_gate_id, "RELEASE_GATE")
    succ_gate = resolver.resolve(successor_release_gate_id, "RELEASE_GATE")
    order_obj = resolver.resolve(ADMISSION_ORDER_ARTIFACT_ID, "ADMISSION_ORDER")
    order = _admission_order(order_obj.parsed_json)
    pred_grade, succ_grade = predecessor.get("terminal_grade"), successor.get("terminal_grade")
    if pred_grade not in order or succ_grade not in order:
        raise ScientificAssuranceLineageV13Error("UNKNOWN_TERMINAL_GRADE")
    failures: list[str] = []
    if succ_grade not in order[pred_grade]:
        if pred_grade == "FORWARD_NULL_CONSISTENT_MISS" and succ_grade == "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE":
            failures.append(f"SAME_RANK_AUTHORITY_ESCALATION:{pred_grade}:{succ_grade}")
        elif frozenset({str(pred_grade), str(succ_grade)}) == frozenset({"FORWARD_NULL_CONSISTENT_MISS", "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE"}):
            failures.append(f"INCOMPARABLE_ADMISSION_OUTCOME_REWRITE:{pred_grade}:{succ_grade}")
        else:
            failures.append(f"SUCCESSOR_OUTCOME_STRONGER_THAN_PREDECESSOR:{pred_grade}:{succ_grade}")
    pred_ids, succ_ids = _required_gate_ids(pred_gate.parsed_json), _required_gate_ids(succ_gate.parsed_json)
    for gate_id in sorted(pred_ids - succ_ids):
        failures += [
            f"GATE_DEFINITION_HISTORICAL_ANCHOR_NOT_ESTABLISHED:{gate_id}",
            f"GATE_ATOM_SEMANTIC_IDENTITY_NOT_ESTABLISHED:{gate_id}",
        ]
    obligations = [{
        "predecessor_gate_id": gate_id,
        "successor_gate_ids": [gate_id],
        "transition_hash": None,
    } for gate_id in sorted(pred_ids & succ_ids)]
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
    pred_gates, succ_gates = predecessor.get("gate_results", {}), successor.get("gate_results", {})
    if not isinstance(pred_gates, Mapping) or not isinstance(succ_gates, Mapping):
        raise ScientificAssuranceLineageV13Error("GATE_RESULTS_NOT_OBJECT")
    for obligation in obligations:
        gate_id = obligation["predecessor_gate_id"]
        if pred_gates.get(gate_id) == "FAIL" and succ_gates.get(gate_id) != "FAIL":
            failures.append(f"INHERITED_HARDENING_LAYER_OMISSION:{gate_id}:FAIL:{gate_id}={succ_gates.get(gate_id)}")
    return RootClosedMonotonicityComparison(
        "PASS" if not failures else "FAIL", tuple(failures), inherited_hash, INHERITED_GATE_HASH_PROFILE_ID,
        NORMATIVE_ROOT_REGISTRY_ID, NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
        PREDECESSOR_NORMATIVE_ROOT_REGISTRY_ID, PREDECESSOR_NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
        PREDECESSOR_EXACT_MAIN_COMMIT, pred_gate.git_blob_sha1, succ_gate.git_blob_sha1,
        order_obj.git_blob_sha1,
    )


def build_assurance_monotonicity_record_v4(
    comparison: RootClosedMonotonicityComparison,
    *, predecessor_verifier: str, successor_verifier: str,
    predecessor_release_gate_id: str, successor_release_gate_id: str,
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
    _validate(value, "AIFC/assurance-monotonicity-record/v4", "ASSURANCE_MONOTONICITY_RECORD_V4")
    return value
