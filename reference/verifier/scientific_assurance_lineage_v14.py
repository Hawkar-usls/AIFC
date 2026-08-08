#!/usr/bin/env python3
"""Scientific Assurance Lineage v1.4: inductive normative lineage activation.

v1.3 remains historical. v1.4 adds two missing authority proofs:
1) an object claiming historical authority must be a member of the claimed Git tree;
2) a later-created authority receipt must have independently replayed provenance.

The predecessor authority root is the exact v2 registry already present in eeee61c.
The v3 registry is only a candidate output of the transition and cannot authorize
itself in the same transition.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping
import urllib.error
import urllib.request

from canonical import CanonicalizationError, loads_strict
from schema_runtime import RuntimeSchemaError, validate_protocol_object

REPO_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "Hawkar-usls/AIFC"
API_VERSION = "2022-11-28"

HISTORICAL_COMMIT = "7e58b47398fe585b24db6304ee6122871095d668"
PREDECESSOR_COMMIT = "eeee61c6143cde1bea64c643def6eaec461e7aa2"
PREDECESSOR_TREE = "2e939271d22d0a1906c93bd7e0fced77780aa88c"

ROOT_V1_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json"
ROOT_V1_BLOB = "0aec9d6ad0d54ce10d312d28a8cb0def1729f835"
ROOT_V2_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V2"
ROOT_V2_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json"
ROOT_V2_BLOB = "d2bb7f3917f8761836825a4e80f03c1e282fc37d"
ROOT_V3_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V3"
ROOT_V3_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v3.json"
ROOT_V3_BLOB = "2092e1a85692dbca2f6c640945ab6b6de224ebd1"

RECEIPT_V12_ID = "AIFC-SAL-V1.2-EXACT-MAIN-RECEIPT-7e58b47"
RECEIPT_V12_PATH = "conformance/AIFC-NORMATIVE-AUTHORITY-RECEIPT-7e58b47-v1.json"
RECEIPT_V12_BLOB = "49b54886f065ac42ee4ff22935112c60f44d4a6c"
RECEIPT_V13_ID = "AIFC-SAL-V1.3-EXACT-MAIN-RECEIPT-eeee61c"
RECEIPT_V13_PATH = "conformance/AIFC-NORMATIVE-AUTHORITY-RECEIPT-eeee61c-v2.json"
RECEIPT_V13_BLOB = "67803a0561ec24549b8b78719de586ab1865ff8e"
PROVENANCE_ID = "AIFC-SAL-AUTHORITY-RECEIPT-PROVENANCE-V1"
PROVENANCE_PATH = "conformance/AIFC-AUTHORITY-RECEIPT-PROVENANCE-v1.json"
PROVENANCE_BLOB = "bc6b1ff50e9729ea7c3d05828902b604d398028d"
TRANSITION_ID = "AIFC-SAL-LINEAGE-ACTIVATION-eeee61c-V1"
TRANSITION_PATH = "conformance/AIFC-NORMATIVE-LINEAGE-TRANSITION-v1.json"
TRANSITION_BLOB = "a88515f1de004c1d31b594b2f3938a7b649279f2"
SCHEMA_REGISTRY_V4_PATH = "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v4.json"
SCHEMA_REGISTRY_V4_BLOB = "4de28a045f8da0995ca0f7b07c051cce6f632881"
RELEASE_GATE_V10_PATH = "conformance/AIFC-RELEASE-GATE-v1.0.10-draft.json"
RELEASE_GATE_V10_BLOB = "ea75fcfa47ecc327fd25533f12437df2e7647154"
RELEASE_GATE_V11_PATH = "conformance/AIFC-RELEASE-GATE-v1.0.11-draft.json"
RELEASE_GATE_V11_BLOB = "dc1af9c927358865b3cd6830a8ca2eabb00ff09d"

ACTIVATED_IDS = frozenset({
    "AIFC-SCHEMA-IDENTITY-REGISTRY-V3",
    "AIFC-INHERITED-GATE-OBLIGATION-HASH-V1-IMPLEMENTATION-BINDING-V1",
    "AIFC-RELEASE-GATE-v1.0.10-draft",
})
NEW_FRONTIER_GATES = frozenset({
    "HISTORICAL_ROOT_COMMIT_MEMBERSHIP",
    "PREDECESSOR_ROOT_REGISTRY_MEMBERSHIP",
    "AUTHORITY_RECEIPT_PROVENANCE",
    "LINEAGE_TRANSITION_REPLAY",
    "SUCCESSOR_REGISTRY_NON_SELF_PROMOTION",
})
REQUIRED_REPLAYS = frozenset({
    "PREDECESSOR_COMMIT_TREE_MEMBERSHIP",
    "PREDECESSOR_ROOT_REGISTRY_MEMBERSHIP",
    "AUTHORITY_RECEIPT_PROVENANCE",
    "LINEAGE_TRANSITION_REPLAY",
    "SUCCESSOR_REGISTRY_NON_SELF_PROMOTION",
})


class ScientificAssuranceLineageV14Error(ValueError):
    pass


@dataclass(frozen=True)
class LineageActivationReport:
    historical_root_commit_membership: bool
    predecessor_root_registry_membership: bool
    authority_receipt_provenance: bool
    lineage_transition_replay: bool
    successor_registry_non_self_promotion: bool
    activated_artifact_ids: tuple[str, ...]
    predecessor_registry_id: str
    successor_registry_candidate_id: str


def git_blob_sha1_bytes(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()


def _strict_object(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        value = loads_strict(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise ScientificAssuranceLineageV14Error(f"LINEAGE_JSON_REJECTED:{label}:{exc}") from exc
    if not isinstance(value, Mapping):
        raise ScientificAssuranceLineageV14Error(f"LINEAGE_JSON_NOT_OBJECT:{label}")
    return value


def _read_bound_json(path_text: str, expected_blob: str, label: str) -> Mapping[str, Any]:
    path = (REPO_ROOT / path_text).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ScientificAssuranceLineageV14Error(f"LINEAGE_PATH_ESCAPE:{path_text}") from exc
    raw = path.read_bytes()
    actual = git_blob_sha1_bytes(raw)
    if actual != expected_blob:
        raise ScientificAssuranceLineageV14Error(
            f"LINEAGE_CONTENT_IDENTITY_MISMATCH:{label}:expected={expected_blob}:actual={actual}"
        )
    return _strict_object(raw, label)


def _validate(value: Mapping[str, Any], schema: str, label: str) -> None:
    try:
        validate_protocol_object(value, schema)
    except RuntimeSchemaError as exc:
        raise ScientificAssuranceLineageV14Error(f"LINEAGE_RUNTIME_SCHEMA_REJECTED:{label}:{exc}") from exc


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as exc:
        raise ScientificAssuranceLineageV14Error(
            f"GIT_EVIDENCE_UNAVAILABLE:{' '.join(args)}:{exc.output.strip()}"
        ) from exc


def git_tree_sha(commit: str) -> str:
    return _git("rev-parse", f"{commit}^{{tree}}")


def git_tree_blob(commit: str, relative_path: str) -> str:
    out = _git("ls-tree", commit, "--", relative_path)
    rows = [line for line in out.splitlines() if line.strip()]
    if len(rows) != 1:
        raise ScientificAssuranceLineageV14Error(
            f"HISTORICAL_TREE_PATH_MEMBERSHIP_MISSING_OR_AMBIGUOUS:{commit}:{relative_path}:{len(rows)}"
        )
    left, tab, path = rows[0].partition("\t")
    fields = left.split()
    if tab != "\t" or path != relative_path or len(fields) != 3 or fields[1] != "blob":
        raise ScientificAssuranceLineageV14Error(f"HISTORICAL_TREE_ENTRY_INVALID:{commit}:{relative_path}")
    return fields[2]


def require_git_membership(commit: str, relative_path: str, expected_blob: str, code: str) -> None:
    actual = git_tree_blob(commit, relative_path)
    if actual != expected_blob:
        raise ScientificAssuranceLineageV14Error(
            f"{code}:{commit}:{relative_path}:expected={expected_blob}:actual={actual}"
        )


def _record_index(registry: Mapping[str, Any], label: str) -> dict[str, Mapping[str, Any]]:
    rows = registry.get("records")
    if not isinstance(rows, list) or not rows:
        raise ScientificAssuranceLineageV14Error(f"ROOT_REGISTRY_RECORDS_INVALID:{label}")
    out: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("artifact_id"), str):
            raise ScientificAssuranceLineageV14Error(f"ROOT_REGISTRY_RECORD_INVALID:{label}")
        artifact_id = str(row["artifact_id"])
        if artifact_id in out:
            raise ScientificAssuranceLineageV14Error(f"ROOT_REGISTRY_DUPLICATE_ARTIFACT:{label}:{artifact_id}")
        out[artifact_id] = row
    return out


def _required_gate_ids(doc: Mapping[str, Any]) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageV14Error("REQUIRED_CHECKS_NOT_ARRAY")
    ids = [row.get("id") for row in rows if isinstance(row, Mapping) and row.get("required") is True]
    if not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids)):
        raise ScientificAssuranceLineageV14Error("REQUIRED_GATE_IDS_INVALID")
    return set(ids)


def _verify_schema_registry_v4() -> None:
    reg = _read_bound_json(SCHEMA_REGISTRY_V4_PATH, SCHEMA_REGISTRY_V4_BLOB, "schema-registry-v4")
    _validate(reg, "AIFC/schema-identity-registry/v4", "schema-registry-v4")
    rows = reg.get("records")
    if not isinstance(rows, list) or len(rows) != 5:
        raise ScientificAssuranceLineageV14Error("SAL_V14_SCHEMA_IDENTITY_COUNT_MISMATCH")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ScientificAssuranceLineageV14Error("SAL_V14_SCHEMA_IDENTITY_ROW_INVALID")
        path = str(row.get("source_path"))
        raw = (REPO_ROOT / path).read_bytes()
        if git_blob_sha1_bytes(raw) != row.get("git_blob_sha1"):
            raise ScientificAssuranceLineageV14Error(f"SAL_V14_SCHEMA_GIT_IDENTITY_MISMATCH:{path}")
        if hashlib.sha256(raw).hexdigest() != row.get("raw_schema_sha256"):
            raise ScientificAssuranceLineageV14Error(f"SAL_V14_SCHEMA_RAW_IDENTITY_MISMATCH:{path}")


def _verify_registry_transition(v2: Mapping[str, Any], v3: Mapping[str, Any], transition: Mapping[str, Any]) -> None:
    old = _record_index(v2, "v2")
    new = _record_index(v3, "v3")
    activated = transition.get("activated_artifact_ids")
    if not isinstance(activated, list) or frozenset(activated) != ACTIVATED_IDS:
        raise ScientificAssuranceLineageV14Error("LINEAGE_ACTIVATED_SET_REBINDING")
    if ROOT_V3_ID in ACTIVATED_IDS or ROOT_V3_ID in activated:
        raise ScientificAssuranceLineageV14Error("SUCCESSOR_REGISTRY_SELF_PROMOTION")
    if v3.get("registry_authority_status") != "SUCCESSOR_REGISTRY_CANDIDATE_REQUIRES_NEXT_LINEAGE_ATTESTATION":
        raise ScientificAssuranceLineageV14Error("SUCCESSOR_REGISTRY_AUTHORITY_STATUS_REBINDING")

    for artifact_id, old_row in old.items():
        new_row = new.get(artifact_id)
        if new_row is None:
            raise ScientificAssuranceLineageV14Error(f"LINEAGE_PREDECESSOR_RECORD_OMITTED:{artifact_id}")
        immutable = ("artifact_id", "kind", "expected_schema", "relative_path", "git_blob_sha1")
        if any(new_row.get(k) != old_row.get(k) for k in immutable):
            raise ScientificAssuranceLineageV14Error(f"LINEAGE_RECORD_CONTENT_REBINDING:{artifact_id}")
        if artifact_id in ACTIVATED_IDS:
            if old_row.get("authority_status") != "SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION":
                raise ScientificAssuranceLineageV14Error(f"LINEAGE_ACTIVATION_PRESTATE_INVALID:{artifact_id}")
            if new_row.get("authority_status") != "ATTESTED_SUCCESSOR_AT_COMMIT":
                raise ScientificAssuranceLineageV14Error(f"LINEAGE_ACTIVATION_POSTSTATE_INVALID:{artifact_id}")
            if new_row.get("authority_commit") != PREDECESSOR_COMMIT or new_row.get("authority_receipt_id") != RECEIPT_V13_ID:
                raise ScientificAssuranceLineageV14Error(f"LINEAGE_ACTIVATION_RECEIPT_BINDING_INVALID:{artifact_id}")
            require_git_membership(
                PREDECESSOR_COMMIT, str(new_row["relative_path"]), str(new_row["git_blob_sha1"]),
                "ACTIVATED_OBJECT_COMMIT_MEMBERSHIP_REBINDING",
            )
        else:
            for key in ("authority_status", "authority_commit", "authority_receipt_id"):
                if new_row.get(key) != old_row.get(key):
                    raise ScientificAssuranceLineageV14Error(f"LINEAGE_UNAUTHORIZED_AUTHORITY_REWRITE:{artifact_id}:{key}")

    for must_remain_candidate in ("AIFC-SCHEMA-IDENTITY-REGISTRY-V4", "AIFC-RELEASE-GATE-v1.0.11-draft"):
        row = new.get(must_remain_candidate)
        if row is None or row.get("authority_status") != "SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION":
            raise ScientificAssuranceLineageV14Error(f"NEXT_GENERATION_CANDIDATE_SELF_PROMOTION:{must_remain_candidate}")


def verify_lineage_activation_local() -> LineageActivationReport:
    transition = _read_bound_json(TRANSITION_PATH, TRANSITION_BLOB, TRANSITION_ID)
    _validate(transition, "AIFC/normative-lineage-transition/v1", TRANSITION_ID)
    v2 = _read_bound_json(ROOT_V2_PATH, ROOT_V2_BLOB, ROOT_V2_ID)
    _validate(v2, "AIFC/normative-assurance-root-registry/v2", ROOT_V2_ID)
    v3 = _read_bound_json(ROOT_V3_PATH, ROOT_V3_BLOB, ROOT_V3_ID)
    _validate(v3, "AIFC/normative-assurance-root-registry/v3", ROOT_V3_ID)
    receipt_v12 = _read_bound_json(RECEIPT_V12_PATH, RECEIPT_V12_BLOB, RECEIPT_V12_ID)
    _validate(receipt_v12, "AIFC/normative-authority-receipt/v1", RECEIPT_V12_ID)
    receipt_v13 = _read_bound_json(RECEIPT_V13_PATH, RECEIPT_V13_BLOB, RECEIPT_V13_ID)
    _validate(receipt_v13, "AIFC/normative-authority-receipt/v2", RECEIPT_V13_ID)
    provenance = _read_bound_json(PROVENANCE_PATH, PROVENANCE_BLOB, PROVENANCE_ID)
    _validate(provenance, "AIFC/authority-receipt-provenance/v1", PROVENANCE_ID)
    _verify_schema_registry_v4()

    if git_tree_sha(PREDECESSOR_COMMIT) != PREDECESSOR_TREE:
        raise ScientificAssuranceLineageV14Error("PREDECESSOR_COMMIT_TREE_SHA_REBINDING")
    require_git_membership(
        PREDECESSOR_COMMIT, ROOT_V2_PATH, ROOT_V2_BLOB, "PREDECESSOR_ROOT_REGISTRY_MEMBERSHIP_REBINDING"
    )
    require_git_membership(
        HISTORICAL_COMMIT, ROOT_V1_PATH, ROOT_V1_BLOB, "HISTORICAL_ROOT_REGISTRY_MEMBERSHIP_REBINDING"
    )
    anchor = transition.get("historical_anchor")
    if not isinstance(anchor, Mapping) or anchor.get("commit") != HISTORICAL_COMMIT:
        raise ScientificAssuranceLineageV14Error("HISTORICAL_ANCHOR_COMMIT_REBINDING")
    memberships = anchor.get("required_memberships")
    if not isinstance(memberships, list) or not memberships:
        raise ScientificAssuranceLineageV14Error("HISTORICAL_MEMBERSHIP_SET_INVALID")
    for item in memberships:
        if not isinstance(item, Mapping):
            raise ScientificAssuranceLineageV14Error("HISTORICAL_MEMBERSHIP_ITEM_INVALID")
        require_git_membership(
            HISTORICAL_COMMIT, str(item.get("relative_path")), str(item.get("git_blob_sha1")),
            "FALSE_HISTORICAL_TREE_MEMBERSHIP",
        )

    if receipt_v13.get("tested_source_commit") != PREDECESSOR_COMMIT or receipt_v13.get("tested_tree_sha") != PREDECESSOR_TREE:
        raise ScientificAssuranceLineageV14Error("ACTIVATION_RECEIPT_SOURCE_REBINDING")
    p_rows = provenance.get("receipts")
    if not isinstance(p_rows, list) or {r.get("receipt_id") for r in p_rows if isinstance(r, Mapping)} != {RECEIPT_V12_ID, RECEIPT_V13_ID}:
        raise ScientificAssuranceLineageV14Error("AUTHORITY_RECEIPT_PROVENANCE_SET_REBINDING")

    _verify_registry_transition(v2, v3, transition)

    gate10 = _read_bound_json(RELEASE_GATE_V10_PATH, RELEASE_GATE_V10_BLOB, "release-gate-v1.0.10")
    gate11 = _read_bound_json(RELEASE_GATE_V11_PATH, RELEASE_GATE_V11_BLOB, "release-gate-v1.0.11")
    old_ids, new_ids = _required_gate_ids(gate10), _required_gate_ids(gate11)
    if len(old_ids) != 78 or len(new_ids) != 83 or new_ids - old_ids != NEW_FRONTIER_GATES or not old_ids < new_ids:
        raise ScientificAssuranceLineageV14Error("SAL_RELEASE_GATE_78_TO_83_NOT_STRICT_ADDITIVE")

    required_replays = transition.get("required_replays")
    if not isinstance(required_replays, list) or set(required_replays) != REQUIRED_REPLAYS:
        raise ScientificAssuranceLineageV14Error("LINEAGE_REQUIRED_REPLAY_SET_REBINDING")

    return LineageActivationReport(
        True, True, False, True, True, tuple(sorted(ACTIVATED_IDS)), ROOT_V2_ID, ROOT_V3_ID
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _github_json(url: str, token: str) -> Mapping[str, Any]:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "AIFC-SAL-Lineage-v1.4",
    })
    with urllib.request.urlopen(req, timeout=60) as response:
        value = json.loads(response.read().decode("utf-8", errors="strict"))
    if not isinstance(value, Mapping):
        raise ScientificAssuranceLineageV14Error("GITHUB_API_RESPONSE_NOT_OBJECT")
    return value


def _download_artifact_zip(url: str, token: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "AIFC-SAL-Lineage-v1.4",
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
        raise ScientificAssuranceLineageV14Error("GITHUB_ARTIFACT_REDIRECT_MISSING")
    with urllib.request.urlopen(
        urllib.request.Request(location, headers={"User-Agent": "AIFC-SAL-Lineage-v1.4"}), timeout=60
    ) as response:
        return response.read()


def _verify_provenance_records(
    provenance: Mapping[str, Any],
    api_get: Callable[[str], Mapping[str, Any]],
    artifact_bytes: Callable[[int], bytes] | None = None,
) -> None:
    base = f"https://api.github.com/repos/{REPOSITORY}"
    rows = provenance.get("receipts")
    if not isinstance(rows, list) or not rows:
        raise ScientificAssuranceLineageV14Error("AUTHORITY_RECEIPT_PROVENANCE_ROWS_INVALID")
    for receipt in rows:
        if not isinstance(receipt, Mapping) or receipt.get("live_replay_required") is not True:
            raise ScientificAssuranceLineageV14Error("RETROACTIVE_AUTHORITY_RECEIPT_SELF_ASSERTION")
        commit = receipt.get("tested_source_commit")
        tree = receipt.get("tested_tree_sha")
        if not isinstance(commit, str) or not isinstance(tree, str):
            raise ScientificAssuranceLineageV14Error("AUTHORITY_RECEIPT_PROVENANCE_SOURCE_INVALID")
        if git_tree_sha(commit) != tree:
            raise ScientificAssuranceLineageV14Error(f"AUTHORITY_RECEIPT_PROVENANCE_TREE_REBINDING:{commit}")
        for expected in receipt.get("workflow_runs", []):
            if not isinstance(expected, Mapping):
                raise ScientificAssuranceLineageV14Error("AUTHORITY_RECEIPT_WORKFLOW_ROW_INVALID")
            run_id = int(expected["run_id"])
            run = api_get(f"{base}/actions/runs/{run_id}")
            if run.get("id") != run_id or run.get("name") != expected.get("workflow_name"):
                raise ScientificAssuranceLineageV14Error(f"AUTHORITY_RECEIPT_WORKFLOW_IDENTITY_REBINDING:{run_id}")
            if run.get("head_sha") != commit or run.get("status") != "completed" or run.get("conclusion") != expected.get("expected_conclusion"):
                raise ScientificAssuranceLineageV14Error(f"AUTHORITY_RECEIPT_WORKFLOW_PROVENANCE_REJECTED:{run_id}")
        for expected in receipt.get("artifacts", []):
            if not isinstance(expected, Mapping):
                raise ScientificAssuranceLineageV14Error("AUTHORITY_RECEIPT_ARTIFACT_ROW_INVALID")
            artifact_id = int(expected["artifact_id"])
            artifact = api_get(f"{base}/actions/artifacts/{artifact_id}")
            run = artifact.get("workflow_run") or {}
            if artifact.get("id") != artifact_id or artifact.get("name") != expected.get("name"):
                raise ScientificAssuranceLineageV14Error(f"AUTHORITY_RECEIPT_ARTIFACT_IDENTITY_REBINDING:{artifact_id}")
            if artifact.get("digest") != expected.get("digest") or artifact.get("expired") is not False or run.get("head_sha") != expected.get("head_sha"):
                raise ScientificAssuranceLineageV14Error(f"AUTHORITY_RECEIPT_ARTIFACT_PROVENANCE_REJECTED:{artifact_id}")
            if artifact_bytes is not None:
                raw = artifact_bytes(artifact_id)
                digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                if digest != expected.get("digest"):
                    raise ScientificAssuranceLineageV14Error(f"AUTHORITY_RECEIPT_ARTIFACT_BYTES_REBINDING:{artifact_id}")


def replay_authority_receipt_provenance_live(token: str | None = None) -> None:
    token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ScientificAssuranceLineageV14Error("AUTHORITY_RECEIPT_PROVENANCE_LIVE_REPLAY_TOKEN_REQUIRED")
    provenance = _read_bound_json(PROVENANCE_PATH, PROVENANCE_BLOB, PROVENANCE_ID)
    _validate(provenance, "AIFC/authority-receipt-provenance/v1", PROVENANCE_ID)
    base = f"https://api.github.com/repos/{REPOSITORY}"
    _verify_provenance_records(
        provenance,
        lambda url: _github_json(url, token),
        lambda artifact_id: _download_artifact_zip(f"{base}/actions/artifacts/{artifact_id}/zip", token),
    )


def verify_lineage_activation_live(token: str | None = None) -> LineageActivationReport:
    local = verify_lineage_activation_local()
    replay_authority_receipt_provenance_live(token)
    return LineageActivationReport(
        local.historical_root_commit_membership,
        local.predecessor_root_registry_membership,
        True,
        local.lineage_transition_replay,
        local.successor_registry_non_self_promotion,
        local.activated_artifact_ids,
        local.predecessor_registry_id,
        local.successor_registry_candidate_id,
    )
