#!/usr/bin/env python3
"""SAL v1.5 Authority-Closure Hardening.

This layer closes concrete v1.4 implementation gaps without rewriting v1.4:
- provenance evidence is bound to the exact content-identified receipt that names it;
- historical workflow runs are bound to workflow id/path and exact definition blob;
- successor registry growth is an exact authorized delta, not an unchecked superset;
- historical artifacts are downloaded and semantically replayed at their attested source.

It also machine-establishes the remaining bootstrap obstruction: the authoritative
predecessor root does not contain an authoritative lineage-transition profile.
Therefore the v1.4 finite transition remains executable and exact-replayed, but
AUTHORITY_CLOSED_FINITE_INDUCTION stays blocked rather than being self-promoted by
successor-created transition semantics.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, Iterator, Mapping
import urllib.error
import urllib.request
import zipfile

from canonical import CanonicalizationError, loads_strict
from schema_runtime import RuntimeSchemaError, validate_protocol_object
from scientific_assurance_lineage_v14 import (
    git_blob_sha1_bytes,
    git_tree_blob,
    git_tree_sha,
    verify_lineage_activation_local,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "Hawkar-usls/AIFC"
API_VERSION = "2022-11-28"

HISTORICAL_COMMIT = "7e58b47398fe585b24db6304ee6122871095d668"
V13_PREDECESSOR_COMMIT = "eeee61c6143cde1bea64c643def6eaec461e7aa2"
V14_MAIN_COMMIT = "56370d60f43feca8b82871d30a0b71acf1409a2f"

ROOT_V2_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V2"
ROOT_V2_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json"
ROOT_V2_BLOB = "d2bb7f3917f8761836825a4e80f03c1e282fc37d"
ROOT_V3_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V3"
ROOT_V3_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v3.json"
ROOT_V3_BLOB = "2092e1a85692dbca2f6c640945ab6b6de224ebd1"

PROVENANCE_V2_ID = "AIFC-SAL-AUTHORITY-RECEIPT-PROVENANCE-V2"
PROVENANCE_V2_PATH = "conformance/AIFC-AUTHORITY-RECEIPT-PROVENANCE-v2.json"
PROVENANCE_V2_BLOB = "74286aa07eee1dafe755621bcfad5cc0e09b1d11"

PROFILE_ID = "AIFC-LINEAGE-TRANSITION-PROFILE-V1"
PROFILE_PATH = "conformance/AIFC-LINEAGE-TRANSITION-PROFILE-v1.json"
PROFILE_BLOB = "f096dbbb6d6382f58b3f2bbd3b7ad170b46d5e1b"
OBSTRUCTION_ID = "AIFC-SAL-V1.5-UNANCHORED-LINEAGE-TRANSITION-SEMANTICS"
OBSTRUCTION_PATH = "conformance/AIFC-AUTHORITY-CLOSURE-OBSTRUCTION-v1.json"
OBSTRUCTION_BLOB = "db8f5189326fdd058daf812e393a94795a7e6755"

SCHEMA_REGISTRY_V5_PATH = "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v5.json"
SCHEMA_REGISTRY_V5_BLOB = "709331f8b59496aac799142ab2311b3abe6353d8"
RELEASE_GATE_V11_PATH = "conformance/AIFC-RELEASE-GATE-v1.0.11-draft.json"
RELEASE_GATE_V11_BLOB = "dc1af9c927358865b3cd6830a8ca2eabb00ff09d"
RELEASE_GATE_V12_PATH = "conformance/AIFC-RELEASE-GATE-v1.0.12-draft.json"
RELEASE_GATE_V12_BLOB = "7206dc82d4fa7bfcb8da883b18bad2192ac08479"

EXPECTED_RECEIPT_IDS = frozenset({
    "AIFC-SAL-V1.2-EXACT-MAIN-RECEIPT-7e58b47",
    "AIFC-SAL-V1.3-EXACT-MAIN-RECEIPT-eeee61c",
    "AIFC-SAL-V1.4-EXACT-MAIN-RECEIPT-56370d6",
})
ACTIVATED_IDS = frozenset({
    "AIFC-SCHEMA-IDENTITY-REGISTRY-V3",
    "AIFC-INHERITED-GATE-OBLIGATION-HASH-V1-IMPLEMENTATION-BINDING-V1",
    "AIFC-RELEASE-GATE-v1.0.10-draft",
})
EXPECTED_NEW_V3_RECORDS: dict[str, dict[str, Any]] = {
    "AIFC-SCHEMA-IDENTITY-REGISTRY-V4": {
        "artifact_id": "AIFC-SCHEMA-IDENTITY-REGISTRY-V4",
        "kind": "SCHEMA_IDENTITY_REGISTRY",
        "expected_schema": "AIFC/schema-identity-registry/v4",
        "relative_path": "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v4.json",
        "git_blob_sha1": "4de28a045f8da0995ca0f7b07c051cce6f632881",
        "authority_status": "SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION",
        "authority_commit": None,
        "authority_receipt_id": None,
    },
    "AIFC-RELEASE-GATE-v1.0.11-draft": {
        "artifact_id": "AIFC-RELEASE-GATE-v1.0.11-draft",
        "kind": "RELEASE_GATE",
        "expected_schema": "AIFC/conformance-release-gate/v1",
        "relative_path": "conformance/AIFC-RELEASE-GATE-v1.0.11-draft.json",
        "git_blob_sha1": "dc1af9c927358865b3cd6830a8ca2eabb00ff09d",
        "authority_status": "SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION",
        "authority_commit": None,
        "authority_receipt_id": None,
    },
}
NEW_FRONTIER_GATES = frozenset({
    "PROVENANCE_RECEIPT_CONTENT_BINDING",
    "HISTORICAL_WORKFLOW_DEFINITION_IDENTITY",
    "SUCCESSOR_REGISTRY_EXACT_DELTA",
    "LINEAGE_TRANSITION_PROFILE_AUTHORITY_ANCHOR",
    "HISTORICAL_ARTIFACT_SEMANTIC_REPLAY",
})


class ScientificAssuranceLineageV15Error(ValueError):
    pass


@dataclass(frozen=True)
class AuthorityClosureReport:
    provenance_receipt_content_binding: bool
    historical_workflow_definition_identity: bool
    successor_registry_exact_delta: bool
    lineage_transition_profile_authority_anchor: bool
    historical_artifact_semantic_replay: bool
    receipt_count: int
    workflow_count: int
    artifact_count: int
    authority_closed_finite_induction: bool


def _strict_object(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        value = loads_strict(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise ScientificAssuranceLineageV15Error(f"SAL_V15_JSON_REJECTED:{label}:{exc}") from exc
    if not isinstance(value, Mapping):
        raise ScientificAssuranceLineageV15Error(f"SAL_V15_JSON_NOT_OBJECT:{label}")
    return value


def _read_bound_json(path_text: str, expected_blob: str, label: str) -> Mapping[str, Any]:
    path = (REPO_ROOT / path_text).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ScientificAssuranceLineageV15Error(f"SAL_V15_PATH_ESCAPE:{path_text}") from exc
    raw = path.read_bytes()
    actual = git_blob_sha1_bytes(raw)
    if actual != expected_blob:
        raise ScientificAssuranceLineageV15Error(
            f"SAL_V15_CONTENT_IDENTITY_MISMATCH:{label}:expected={expected_blob}:actual={actual}"
        )
    return _strict_object(raw, label)


def _validate(value: Mapping[str, Any], schema: str, label: str) -> None:
    try:
        validate_protocol_object(value, schema)
    except RuntimeSchemaError as exc:
        raise ScientificAssuranceLineageV15Error(f"SAL_V15_RUNTIME_SCHEMA_REJECTED:{label}:{exc}") from exc


def _require_git_membership(commit: str, path: str, blob: str, code: str) -> None:
    actual = git_tree_blob(commit, path)
    if actual != blob:
        raise ScientificAssuranceLineageV15Error(
            f"{code}:{commit}:{path}:expected={blob}:actual={actual}"
        )


def _record_index(registry: Mapping[str, Any], label: str) -> dict[str, Mapping[str, Any]]:
    rows = registry.get("records")
    if not isinstance(rows, list) or not rows:
        raise ScientificAssuranceLineageV15Error(f"SAL_V15_ROOT_RECORDS_INVALID:{label}")
    out: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("artifact_id"), str):
            raise ScientificAssuranceLineageV15Error(f"SAL_V15_ROOT_RECORD_INVALID:{label}")
        artifact_id = str(row["artifact_id"])
        if artifact_id in out:
            raise ScientificAssuranceLineageV15Error(f"SAL_V15_ROOT_RECORD_DUPLICATE:{label}:{artifact_id}")
        out[artifact_id] = row
    return out


def _required_gate_ids(doc: Mapping[str, Any]) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageV15Error("SAL_V15_REQUIRED_CHECKS_NOT_ARRAY")
    ids = [row.get("id") for row in rows if isinstance(row, Mapping) and row.get("required") is True]
    if not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids)):
        raise ScientificAssuranceLineageV15Error("SAL_V15_REQUIRED_GATE_IDS_INVALID")
    return set(ids)


def _receipt_workflow_projection(receipt: Mapping[str, Any]) -> tuple[str, set[tuple[Any, ...]]]:
    schema = receipt.get("schema")
    rows = receipt.get("workflow_runs")
    if schema == "AIFC/normative-authority-receipt/v1":
        if not isinstance(rows, Mapping) or not rows:
            raise ScientificAssuranceLineageV15Error("RECEIPT_V1_WORKFLOW_SET_INVALID")
        projection = {(str(role), int(run_id)) for role, run_id in rows.items()}
        return "v1", projection
    if schema == "AIFC/normative-authority-receipt/v2":
        if not isinstance(rows, list) or not rows:
            raise ScientificAssuranceLineageV15Error("RECEIPT_V2_WORKFLOW_SET_INVALID")
        projection: set[tuple[Any, ...]] = set()
        for row in rows:
            if not isinstance(row, Mapping):
                raise ScientificAssuranceLineageV15Error("RECEIPT_V2_WORKFLOW_ROW_INVALID")
            item = (
                str(row.get("role")), int(row.get("run_id")), str(row.get("workflow_name")),
                str(row.get("expected_conclusion")),
            )
            if item in projection:
                raise ScientificAssuranceLineageV15Error("RECEIPT_V2_WORKFLOW_DUPLICATE")
            projection.add(item)
        return "v2", projection
    raise ScientificAssuranceLineageV15Error(f"UNSUPPORTED_AUTHORITY_RECEIPT_SCHEMA:{schema}")


def _provenance_workflow_projection(row: Mapping[str, Any], mode: str) -> set[tuple[Any, ...]]:
    runs = row.get("workflow_runs")
    if not isinstance(runs, list) or not runs:
        raise ScientificAssuranceLineageV15Error("PROVENANCE_V2_WORKFLOW_SET_INVALID")
    if mode == "v1":
        result = {(str(r.get("role")), int(r.get("run_id"))) for r in runs if isinstance(r, Mapping)}
    else:
        result = {
            (str(r.get("role")), int(r.get("run_id")), str(r.get("workflow_name")), str(r.get("expected_conclusion")))
            for r in runs if isinstance(r, Mapping)
        }
    if len(result) != len(runs):
        raise ScientificAssuranceLineageV15Error("PROVENANCE_V2_WORKFLOW_DUPLICATE_OR_INVALID")
    return result


def _artifact_projection(rows: Any, label: str) -> set[tuple[int, str, str, str]]:
    if not isinstance(rows, list) or not rows:
        raise ScientificAssuranceLineageV15Error(f"{label}_ARTIFACT_SET_INVALID")
    result: set[tuple[int, str, str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ScientificAssuranceLineageV15Error(f"{label}_ARTIFACT_ROW_INVALID")
        item = (int(row.get("artifact_id")), str(row.get("name")), str(row.get("digest")), str(row.get("head_sha")))
        if item in result:
            raise ScientificAssuranceLineageV15Error(f"{label}_ARTIFACT_DUPLICATE")
        result.add(item)
    return result


def _verify_receipt_content_binding(provenance: Mapping[str, Any]) -> tuple[int, int, int]:
    rows = provenance.get("receipts")
    if not isinstance(rows, list) or not rows:
        raise ScientificAssuranceLineageV15Error("PROVENANCE_V2_RECEIPTS_INVALID")
    ids = {row.get("receipt_id") for row in rows if isinstance(row, Mapping)}
    if ids != EXPECTED_RECEIPT_IDS or len(ids) != len(rows):
        raise ScientificAssuranceLineageV15Error("PROVENANCE_V2_RECEIPT_SET_REBINDING")

    workflow_count = 0
    artifact_count = 0
    for row in rows:
        if not isinstance(row, Mapping) or row.get("live_replay_required") is not True:
            raise ScientificAssuranceLineageV15Error("RETROACTIVE_AUTHORITY_RECEIPT_SELF_ASSERTION_V2")
        receipt = _read_bound_json(str(row.get("receipt_path")), str(row.get("receipt_git_blob_sha1")), str(row.get("receipt_id")))
        schema = str(receipt.get("schema"))
        _validate(receipt, schema, str(row.get("receipt_id")))
        if receipt.get("receipt_id") != row.get("receipt_id"):
            raise ScientificAssuranceLineageV15Error("PROVENANCE_RECEIPT_ID_CONTENT_REBINDING")
        if receipt.get("tested_source_commit") != row.get("tested_source_commit") or receipt.get("tested_tree_sha") != row.get("tested_tree_sha"):
            raise ScientificAssuranceLineageV15Error(f"PROVENANCE_RECEIPT_SOURCE_CONTENT_REBINDING:{row.get('receipt_id')}")
        commit = str(row.get("tested_source_commit"))
        tree = str(row.get("tested_tree_sha"))
        if git_tree_sha(commit) != tree:
            raise ScientificAssuranceLineageV15Error(f"PROVENANCE_RECEIPT_TREE_REBINDING:{commit}")

        mode, receipt_runs = _receipt_workflow_projection(receipt)
        provenance_runs = _provenance_workflow_projection(row, mode)
        if receipt_runs != provenance_runs:
            raise ScientificAssuranceLineageV15Error(f"PROVENANCE_RECEIPT_WORKFLOW_CONTENT_DISCONNECT:{row.get('receipt_id')}")
        receipt_artifacts = _artifact_projection(receipt.get("artifacts"), "RECEIPT")
        provenance_artifacts = _artifact_projection(row.get("artifacts"), "PROVENANCE")
        if receipt_artifacts != provenance_artifacts:
            raise ScientificAssuranceLineageV15Error(f"PROVENANCE_RECEIPT_ARTIFACT_CONTENT_DISCONNECT:{row.get('receipt_id')}")

        workflow_count += len(provenance_runs)
        artifact_count += len(provenance_artifacts)
    return len(rows), workflow_count, artifact_count


def _verify_workflow_definition_membership(provenance: Mapping[str, Any]) -> int:
    count = 0
    for receipt in provenance.get("receipts", []):
        if not isinstance(receipt, Mapping):
            raise ScientificAssuranceLineageV15Error("WORKFLOW_DEFINITION_RECEIPT_ROW_INVALID")
        commit = str(receipt.get("tested_source_commit"))
        seen_run_ids: set[int] = set()
        for row in receipt.get("workflow_runs", []):
            if not isinstance(row, Mapping):
                raise ScientificAssuranceLineageV15Error("WORKFLOW_DEFINITION_ROW_INVALID")
            run_id = int(row.get("run_id"))
            if run_id in seen_run_ids:
                raise ScientificAssuranceLineageV15Error(f"WORKFLOW_DEFINITION_DUPLICATE_RUN:{run_id}")
            seen_run_ids.add(run_id)
            _require_git_membership(
                commit,
                str(row.get("workflow_path")),
                str(row.get("workflow_git_blob_sha1")),
                "HISTORICAL_WORKFLOW_DEFINITION_REBINDING",
            )
            count += 1
    return count


def _verify_registry_exact_delta() -> None:
    v2 = _read_bound_json(ROOT_V2_PATH, ROOT_V2_BLOB, ROOT_V2_ID)
    _validate(v2, "AIFC/normative-assurance-root-registry/v2", ROOT_V2_ID)
    v3 = _read_bound_json(ROOT_V3_PATH, ROOT_V3_BLOB, ROOT_V3_ID)
    _validate(v3, "AIFC/normative-assurance-root-registry/v3", ROOT_V3_ID)
    old = _record_index(v2, "v2")
    new = _record_index(v3, "v3")
    expected_new_ids = set(EXPECTED_NEW_V3_RECORDS)
    if set(new) != set(old) | expected_new_ids:
        extras = sorted(set(new) - set(old) - expected_new_ids)
        missing = sorted((set(old) | expected_new_ids) - set(new))
        raise ScientificAssuranceLineageV15Error(f"SUCCESSOR_REGISTRY_EXTRA_RECORD_INJECTION:extras={extras}:missing={missing}")

    immutable = ("artifact_id", "kind", "expected_schema", "relative_path", "git_blob_sha1")
    for artifact_id, old_row in old.items():
        new_row = new[artifact_id]
        if any(new_row.get(k) != old_row.get(k) for k in immutable):
            raise ScientificAssuranceLineageV15Error(f"SUCCESSOR_REGISTRY_PREDECESSOR_CONTENT_REBINDING:{artifact_id}")
        if artifact_id in ACTIVATED_IDS:
            if old_row.get("authority_status") != "SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION":
                raise ScientificAssuranceLineageV15Error(f"SUCCESSOR_REGISTRY_ACTIVATION_PRESTATE_INVALID:{artifact_id}")
            if new_row.get("authority_status") != "ATTESTED_SUCCESSOR_AT_COMMIT":
                raise ScientificAssuranceLineageV15Error(f"SUCCESSOR_REGISTRY_ACTIVATION_POSTSTATE_INVALID:{artifact_id}")
            if new_row.get("authority_commit") != V13_PREDECESSOR_COMMIT or new_row.get("authority_receipt_id") != "AIFC-SAL-V1.3-EXACT-MAIN-RECEIPT-eeee61c":
                raise ScientificAssuranceLineageV15Error(f"SUCCESSOR_REGISTRY_ACTIVATION_BINDING_INVALID:{artifact_id}")
        else:
            for key in ("authority_status", "authority_commit", "authority_receipt_id"):
                if new_row.get(key) != old_row.get(key):
                    raise ScientificAssuranceLineageV15Error(f"SUCCESSOR_REGISTRY_UNAUTHORIZED_REWRITE:{artifact_id}:{key}")

    for artifact_id, expected in EXPECTED_NEW_V3_RECORDS.items():
        if dict(new[artifact_id]) != expected:
            raise ScientificAssuranceLineageV15Error(f"SUCCESSOR_REGISTRY_NEW_RECORD_REBINDING:{artifact_id}")


def _verify_transition_profile_authority_anchor() -> bool:
    profile = _read_bound_json(PROFILE_PATH, PROFILE_BLOB, PROFILE_ID)
    _validate(profile, "AIFC/lineage-transition-profile/v1", PROFILE_ID)
    obstruction = _read_bound_json(OBSTRUCTION_PATH, OBSTRUCTION_BLOB, OBSTRUCTION_ID)
    _validate(obstruction, "AIFC/authority-closure-obstruction/v1", OBSTRUCTION_ID)
    if profile.get("authority_status") != "SUCCESSOR_CANDIDATE_REQUIRES_PREDECESSOR_PROFILE_ATTESTATION":
        raise ScientificAssuranceLineageV15Error("SUCCESSOR_DEFINED_ACTIVATION_AUTHORITY")

    v2 = _read_bound_json(ROOT_V2_PATH, ROOT_V2_BLOB, ROOT_V2_ID)
    records = _record_index(v2, "v2-authority-anchor")
    matches = [
        row for row in records.values()
        if row.get("artifact_id") == PROFILE_ID
        or row.get("kind") == "LINEAGE_TRANSITION_PROFILE"
        or row.get("expected_schema") == "AIFC/lineage-transition-profile/v1"
    ]
    authoritative_matches = [
        row for row in matches
        if row.get("authority_status") in {"HISTORICAL_ROOT_AT_PREDECESSOR_COMMIT", "ATTESTED_SUCCESSOR_AT_COMMIT"}
    ]
    if authoritative_matches:
        raise ScientificAssuranceLineageV15Error("AUTHORITY_CLOSURE_OBSTRUCTION_FALSE_NEGATIVE")
    if obstruction.get("observed_authoritative_profile_records") != 0:
        raise ScientificAssuranceLineageV15Error("AUTHORITY_CLOSURE_OBSTRUCTION_COUNT_REBINDING")
    if obstruction.get("predecessor_registry_git_blob_sha1") != ROOT_V2_BLOB or obstruction.get("predecessor_authority_commit") != V13_PREDECESSOR_COMMIT:
        raise ScientificAssuranceLineageV15Error("AUTHORITY_CLOSURE_OBSTRUCTION_PREDECESSOR_REBINDING")
    if obstruction.get("successor_candidate_profile_git_blob_sha1") != PROFILE_BLOB:
        raise ScientificAssuranceLineageV15Error("AUTHORITY_CLOSURE_OBSTRUCTION_PROFILE_REBINDING")
    if obstruction.get("result") != "BLOCKED_NO_PREDECESSOR_TRANSITION_PROFILE_AUTHORITY" or obstruction.get("authority_closed_finite_induction") is not False:
        raise ScientificAssuranceLineageV15Error("AUTHORITY_CLOSURE_OBSTRUCTION_STATUS_REBINDING")
    return False


def _verify_schema_registry_v5() -> None:
    reg = _read_bound_json(SCHEMA_REGISTRY_V5_PATH, SCHEMA_REGISTRY_V5_BLOB, "schema-registry-v5")
    _validate(reg, "AIFC/schema-identity-registry/v5", "schema-registry-v5")
    rows = reg.get("records")
    if not isinstance(rows, list) or len(rows) != 4:
        raise ScientificAssuranceLineageV15Error("SAL_V15_SCHEMA_IDENTITY_COUNT_MISMATCH")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ScientificAssuranceLineageV15Error("SAL_V15_SCHEMA_IDENTITY_ROW_INVALID")
        path = str(row.get("source_path"))
        raw = (REPO_ROOT / path).read_bytes()
        if git_blob_sha1_bytes(raw) != row.get("git_blob_sha1"):
            raise ScientificAssuranceLineageV15Error(f"SAL_V15_SCHEMA_GIT_IDENTITY_MISMATCH:{path}")
        if hashlib.sha256(raw).hexdigest() != row.get("raw_schema_sha256"):
            raise ScientificAssuranceLineageV15Error(f"SAL_V15_SCHEMA_RAW_IDENTITY_MISMATCH:{path}")


def _verify_release_frontier() -> None:
    gate11 = _read_bound_json(RELEASE_GATE_V11_PATH, RELEASE_GATE_V11_BLOB, "release-gate-v1.0.11")
    gate12 = _read_bound_json(RELEASE_GATE_V12_PATH, RELEASE_GATE_V12_BLOB, "release-gate-v1.0.12")
    old_ids, new_ids = _required_gate_ids(gate11), _required_gate_ids(gate12)
    if len(old_ids) != 83 or len(new_ids) != 88 or new_ids - old_ids != NEW_FRONTIER_GATES or not old_ids < new_ids:
        raise ScientificAssuranceLineageV15Error("SAL_RELEASE_GATE_83_TO_88_NOT_STRICT_ADDITIVE")


def verify_authority_closure_local() -> AuthorityClosureReport:
    verify_lineage_activation_local()
    provenance = _read_bound_json(PROVENANCE_V2_PATH, PROVENANCE_V2_BLOB, PROVENANCE_V2_ID)
    _validate(provenance, "AIFC/authority-receipt-provenance/v2", PROVENANCE_V2_ID)
    receipt_count, workflow_count, artifact_count = _verify_receipt_content_binding(provenance)
    observed_workflows = _verify_workflow_definition_membership(provenance)
    if observed_workflows != workflow_count:
        raise ScientificAssuranceLineageV15Error("WORKFLOW_DEFINITION_COUNT_REBINDING")
    _verify_registry_exact_delta()
    anchor = _verify_transition_profile_authority_anchor()
    _verify_schema_registry_v5()
    _verify_release_frontier()
    return AuthorityClosureReport(
        True,
        True,
        True,
        anchor,
        False,
        receipt_count,
        workflow_count,
        artifact_count,
        False,
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _github_json(url: str, token: str) -> Mapping[str, Any]:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "AIFC-SAL-Authority-Closure-v1.5",
    })
    with urllib.request.urlopen(req, timeout=60) as response:
        value = json.loads(response.read().decode("utf-8", errors="strict"))
    if not isinstance(value, Mapping):
        raise ScientificAssuranceLineageV15Error("GITHUB_API_RESPONSE_NOT_OBJECT")
    return value


def _download_artifact_zip(url: str, token: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "AIFC-SAL-Authority-Closure-v1.5",
    })
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=60) as response:
            location = response.headers.get("Location")
    except urllib.error.HTTPError as exc:
        if exc.code != 302:
            raise
        location = exc.headers.get("Location")
    if not isinstance(location, str) or not location.startswith("https://"):
        raise ScientificAssuranceLineageV15Error("GITHUB_ARTIFACT_REDIRECT_MISSING")
    with urllib.request.urlopen(
        urllib.request.Request(location, headers={"User-Agent": "AIFC-SAL-Authority-Closure-v1.5"}), timeout=60
    ) as response:
        return response.read()


def _verify_live_provenance(
    provenance: Mapping[str, Any],
    api_get: Callable[[str], Mapping[str, Any]],
    artifact_bytes: Callable[[int], bytes],
) -> dict[int, bytes]:
    base = f"https://api.github.com/repos/{REPOSITORY}"
    downloaded: dict[int, bytes] = {}
    for receipt in provenance.get("receipts", []):
        if not isinstance(receipt, Mapping):
            raise ScientificAssuranceLineageV15Error("LIVE_PROVENANCE_RECEIPT_ROW_INVALID")
        commit = str(receipt.get("tested_source_commit"))
        for expected in receipt.get("workflow_runs", []):
            if not isinstance(expected, Mapping):
                raise ScientificAssuranceLineageV15Error("LIVE_WORKFLOW_ROW_INVALID")
            run_id = int(expected.get("run_id"))
            run = api_get(f"{base}/actions/runs/{run_id}")
            if run.get("id") != run_id or run.get("name") != expected.get("workflow_name"):
                raise ScientificAssuranceLineageV15Error(f"LIVE_WORKFLOW_RUN_IDENTITY_REBINDING:{run_id}")
            if run.get("workflow_id") != expected.get("workflow_id"):
                raise ScientificAssuranceLineageV15Error(f"HISTORICAL_WORKFLOW_ID_REBINDING:{run_id}")
            if run.get("path") != expected.get("workflow_path"):
                raise ScientificAssuranceLineageV15Error(f"HISTORICAL_WORKFLOW_PATH_REBINDING:{run_id}")
            if run.get("event") != expected.get("event"):
                raise ScientificAssuranceLineageV15Error(f"HISTORICAL_WORKFLOW_EVENT_REBINDING:{run_id}")
            if run.get("head_sha") != commit or run.get("status") != "completed" or run.get("conclusion") != expected.get("expected_conclusion"):
                raise ScientificAssuranceLineageV15Error(f"LIVE_WORKFLOW_PROVENANCE_REJECTED:{run_id}")
            _require_git_membership(
                commit,
                str(expected.get("workflow_path")),
                str(expected.get("workflow_git_blob_sha1")),
                "HISTORICAL_WORKFLOW_DEFINITION_REBINDING",
            )
        for expected in receipt.get("artifacts", []):
            if not isinstance(expected, Mapping):
                raise ScientificAssuranceLineageV15Error("LIVE_ARTIFACT_ROW_INVALID")
            artifact_id = int(expected.get("artifact_id"))
            artifact = api_get(f"{base}/actions/artifacts/{artifact_id}")
            run = artifact.get("workflow_run") or {}
            if artifact.get("id") != artifact_id or artifact.get("name") != expected.get("name"):
                raise ScientificAssuranceLineageV15Error(f"LIVE_ARTIFACT_IDENTITY_REBINDING:{artifact_id}")
            if artifact.get("digest") != expected.get("digest") or artifact.get("expired") is not False or run.get("head_sha") != expected.get("head_sha"):
                raise ScientificAssuranceLineageV15Error(f"LIVE_ARTIFACT_PROVENANCE_REJECTED:{artifact_id}")
            raw = artifact_bytes(artifact_id)
            digest = "sha256:" + hashlib.sha256(raw).hexdigest()
            if digest != expected.get("digest"):
                raise ScientificAssuranceLineageV15Error(f"LIVE_ARTIFACT_BYTES_REBINDING:{artifact_id}")
            downloaded[artifact_id] = raw
    return downloaded


def _safe_extract_zip(raw: bytes, destination: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            candidate = (destination / info.filename).resolve()
            try:
                candidate.relative_to(destination.resolve())
            except ValueError as exc:
                raise ScientificAssuranceLineageV15Error(f"ARTIFACT_ZIP_PATH_ESCAPE:{info.filename}") from exc
        archive.extractall(destination)


def _find_unique(root: Path, name: str) -> Path:
    matches = [p for p in root.rglob(name) if p.is_file()]
    if len(matches) != 1:
        raise ScientificAssuranceLineageV15Error(f"ARTIFACT_SEMANTIC_FILE_COUNT:{name}:{len(matches)}")
    return matches[0]


def _run_semantic(command: list[str], cwd: Path, token: str) -> bytes:
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    env["GITHUB_TOKEN"] = token
    proc = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode != 0:
        text = proc.stdout.decode("utf-8", errors="replace")[-4000:]
        raise ScientificAssuranceLineageV15Error(f"HISTORICAL_ARTIFACT_SEMANTIC_REPLAY_FAILED:{command[-1]}:{text}")
    return proc.stdout


@contextmanager
def _historical_worktree(commit: str) -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="aifc-sal-v15-worktree-") as tmp:
        worktree = Path(tmp) / "repo"
        proc = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), commit],
            cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
        )
        if proc.returncode != 0:
            raise ScientificAssuranceLineageV15Error(
                "HISTORICAL_WORKTREE_CREATE_FAILED:" + proc.stdout.decode("utf-8", errors="replace")[-2000:]
            )
        try:
            yield worktree
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
            )


def _semantic_replay_artifact(commit: str, name: str, raw_zip: bytes, token: str, worktree: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="aifc-sal-v15-artifact-") as tmp:
        extracted = Path(tmp)
        _safe_extract_zip(raw_zip, extracted)
        if name.startswith("verifier-a-v04-ci-attestation-"):
            att = _find_unique(extracted, "verifier-ci-attestation-v2.json")
            side = _find_unique(extracted, "verifier-ci-attestation-v2.sha256.json")
            _run_semantic([
                sys.executable,
                str(worktree / "tools" / "verify_verifier_ci_attestation_v04.py"),
                "--attestation", str(att),
                "--artifact-dir", str(extracted),
                "--sidecar", str(side),
            ], worktree, token)
            return
        if name.startswith("verifier-a-v04-platform-receipt-"):
            receipt = _find_unique(extracted, "ci-platform-receipt.json")
            side = _find_unique(extracted, "ci-platform-receipt.sha256.json")
            _run_semantic([
                sys.executable,
                str(worktree / "tools" / "verify_ci_platform_receipt.py"),
                "--receipt", str(receipt),
                "--sidecar", str(side),
            ], worktree, token)
            return
        checker = None
        if name.startswith("sal-v12-conformance-"):
            checker = "tools/check_sal_conformance_v12.py"
        elif name.startswith("sal-v13-root-closure-"):
            checker = "tools/check_sal_root_closure_v13.py"
        elif name.startswith("sal-v14-lineage-activation-"):
            checker = "tools/check_sal_lineage_activation_v14.py"
        if checker is None:
            raise ScientificAssuranceLineageV15Error(f"HISTORICAL_ARTIFACT_SEMANTICS_UNKNOWN:{name}")
        txt_files = [p for p in extracted.rglob("*.txt") if p.is_file()]
        sha_files = [p for p in extracted.rglob("*.sha256") if p.is_file()]
        if len(txt_files) != 1 or len(sha_files) != 1:
            raise ScientificAssuranceLineageV15Error(f"SAL_ARTIFACT_REPORT_LAYOUT_INVALID:{name}")
        report_raw = txt_files[0].read_bytes()
        side_text = sha_files[0].read_text(encoding="utf-8", errors="strict").strip()
        declared = side_text.split()[0] if side_text else ""
        if declared != hashlib.sha256(report_raw).hexdigest():
            raise ScientificAssuranceLineageV15Error(f"SAL_ARTIFACT_REPORT_HASH_REBINDING:{name}")
        replayed = _run_semantic([sys.executable, str(worktree / checker)], worktree, token)
        if replayed != report_raw:
            raise ScientificAssuranceLineageV15Error(f"SAL_ARTIFACT_REPORT_SEMANTIC_MISMATCH:{name}")


def _semantic_replay_all(provenance: Mapping[str, Any], downloaded: Mapping[int, bytes], token: str) -> int:
    count = 0
    by_commit: dict[str, list[Mapping[str, Any]]] = {}
    for receipt in provenance.get("receipts", []):
        if not isinstance(receipt, Mapping):
            raise ScientificAssuranceLineageV15Error("SEMANTIC_REPLAY_RECEIPT_ROW_INVALID")
        by_commit.setdefault(str(receipt.get("tested_source_commit")), []).extend(
            [row for row in receipt.get("artifacts", []) if isinstance(row, Mapping)]
        )
    for commit, artifacts in by_commit.items():
        with _historical_worktree(commit) as worktree:
            for row in artifacts:
                artifact_id = int(row.get("artifact_id"))
                raw = downloaded.get(artifact_id)
                if raw is None:
                    raise ScientificAssuranceLineageV15Error(f"SEMANTIC_REPLAY_ARTIFACT_BYTES_MISSING:{artifact_id}")
                _semantic_replay_artifact(commit, str(row.get("name")), raw, token, worktree)
                count += 1
    return count


def verify_authority_closure_live(token: str | None = None) -> AuthorityClosureReport:
    local = verify_authority_closure_local()
    token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ScientificAssuranceLineageV15Error("SAL_V15_LIVE_REPLAY_TOKEN_REQUIRED")
    provenance = _read_bound_json(PROVENANCE_V2_PATH, PROVENANCE_V2_BLOB, PROVENANCE_V2_ID)
    base = f"https://api.github.com/repos/{REPOSITORY}"
    downloaded = _verify_live_provenance(
        provenance,
        lambda url: _github_json(url, token),
        lambda artifact_id: _download_artifact_zip(f"{base}/actions/artifacts/{artifact_id}/zip", token),
    )
    replayed = _semantic_replay_all(provenance, downloaded, token)
    if replayed != local.artifact_count:
        raise ScientificAssuranceLineageV15Error(
            f"HISTORICAL_ARTIFACT_SEMANTIC_REPLAY_COUNT_REBINDING:{replayed}:{local.artifact_count}"
        )
    return AuthorityClosureReport(
        local.provenance_receipt_content_binding,
        True,
        local.successor_registry_exact_delta,
        local.lineage_transition_profile_authority_anchor,
        True,
        local.receipt_count,
        local.workflow_count,
        local.artifact_count,
        False,
    )
