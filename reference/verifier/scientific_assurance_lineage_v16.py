#!/usr/bin/env python3
"""SAL v1.6 Predecessor Semantic Entailment Audit.

This layer does not create a new authority epoch. It asks whether the already
authoritative predecessor semantics entail the candidate lineage transition
profile. The audit is explicitly three-valued:

- PROVED
- BLOCKED_UNANCHORED_SEMANTICS
- REFUTED_BY_COUNTERMODEL

Missing semantic anchors MUST NOT be interpreted as a countermodel.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from pathlib import Path
from typing import Any, Mapping

from canonical import CanonicalizationError, loads_strict
from schema_runtime import RuntimeSchemaError, validate_protocol_object
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes, git_tree_blob

REPO_ROOT = Path(__file__).resolve().parents[2]

BOOTSTRAP_COMMIT = "908de7afddcf9f72c98c2b3fb696a41be1e438e0"
HISTORICAL_COMMIT = "7e58b47398fe585b24db6304ee6122871095d668"
V13_MAIN_COMMIT = "eeee61c6143cde1bea64c643def6eaec461e7aa2"
V14_MAIN_COMMIT = "56370d60f43feca8b82871d30a0b71acf1409a2f"
V15_MAIN_COMMIT = "5afc09e9a965f8b20d0b07059f1ff753aad920b7"

ROOT_V1_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V1"
ROOT_V1_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json"
ROOT_V1_BLOB = "0aec9d6ad0d54ce10d312d28a8cb0def1729f835"

ROOT_V2_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V2"
ROOT_V2_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json"
ROOT_V2_BLOB = "d2bb7f3917f8761836825a4e80f03c1e282fc37d"

RELEASE_V08_ID = "AIFC-RELEASE-GATE-v1.0.8-draft"
RELEASE_V08_PATH = "conformance/AIFC-RELEASE-GATE-v1.0.8-draft.json"
RELEASE_V08_BLOB = "656bda0bae1d1af515a642f157149450c78d879e"

RELEASE_V09_ID = "AIFC-RELEASE-GATE-v1.0.9-draft"
RELEASE_V09_PATH = "conformance/AIFC-RELEASE-GATE-v1.0.9-draft.json"
RELEASE_V09_BLOB = "e46cfee9963e61a22bc25e4e68ac5f11781e8d47"

ADMISSION_ORDER_ID = "AIFC-ADMISSION-AUTHORITY-PARTIAL-ORDER-V1"
ADMISSION_ORDER_PATH = "conformance/AIFC-ADMISSION-AUTHORITY-ORDER-v1.json"
ADMISSION_ORDER_BLOB = "38eeb695caf781dcdc79115d4903c743db7311f9"

TARGET_PROFILE_ID = "AIFC-LINEAGE-TRANSITION-PROFILE-V1"
TARGET_PROFILE_PATH = "conformance/AIFC-LINEAGE-TRANSITION-PROFILE-v1.json"
TARGET_PROFILE_BLOB = "f096dbbb6d6382f58b3f2bbd3b7ad170b46d5e1b"

DEPENDENCY_LOCK_PATH = "reference/verifier/requirements.lock.txt"
DEPENDENCY_LOCK_BLOB = "1fb5b20d71b3eac742573fb3b4885537e6c512b7"
DEPENDENCY_LOCK_TESTED_COMMITS = (
    HISTORICAL_COMMIT,
    V13_MAIN_COMMIT,
    V14_MAIN_COMMIT,
    V15_MAIN_COMMIT,
)

REQUIRED_CHECK_IDS = frozenset({
    "AUTHORITY_CLOSED_PROOF",
    "GATE_DEFINITION_HISTORICAL_ANCHOR",
    "GATE_ATOM_SEMANTIC_IDENTITY",
})
REQUIRED_FORBIDDEN_SHORTCUTS = frozenset({
    "allowing a transition proof to create or select the normative semantics that constitute its own theorem",
    "allowing a normative root to self-authenticate through a descendant transition",
})
REQUIRED_SEMANTIC_ANCHOR_IDS = (
    "AIFC-SEMANTIC-ANCHOR-AUTHORITY-CLOSED-PROOF-V1",
    "AIFC-SEMANTIC-ANCHOR-GATE-DEFINITION-HISTORICAL-ANCHOR-V1",
    "AIFC-SEMANTIC-ANCHOR-GATE-ATOM-SEMANTIC-IDENTITY-V1",
)

ENTAILMENT_AUDIT_PATH = "conformance/AIFC-PREDECESSOR-SEMANTIC-ENTAILMENT-AUDIT-v1.json"
BOOTSTRAP_STATUS_PATH = "conformance/AIFC-BOOTSTRAP-AUTHORITY-BASE-CASE-STATUS-v1.json"
ENVIRONMENT_AUDIT_PATH = "conformance/AIFC-HISTORICAL-REPLAY-ENVIRONMENT-AUDIT-v1.json"


class ScientificAssuranceLineageV16Error(ValueError):
    pass


@dataclass(frozen=True)
class EntailmentResult:
    state: str
    countermodel: Mapping[str, bool] | None


@dataclass(frozen=True)
class PredecessorSemanticAuditReport:
    direct_predecessor_transition_profile_authority: str
    predecessor_anti_self_authentication_constraints: bool
    predecessor_semantic_entailment: str
    missing_semantic_anchor_ids: tuple[str, ...]
    bootstrap_authority_basis_status: str
    dependency_lock_identity_same: bool
    historical_replay_environment_identity_general: str


def _strict_object(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        value = loads_strict(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise ScientificAssuranceLineageV16Error(f"SAL_V16_JSON_REJECTED:{label}:{exc}") from exc
    if not isinstance(value, Mapping):
        raise ScientificAssuranceLineageV16Error(f"SAL_V16_JSON_NOT_OBJECT:{label}")
    return value


def _read_bound_json(path_text: str, expected_blob: str, label: str) -> Mapping[str, Any]:
    path = (REPO_ROOT / path_text).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ScientificAssuranceLineageV16Error(f"SAL_V16_PATH_ESCAPE:{path_text}") from exc
    raw = path.read_bytes()
    actual = git_blob_sha1_bytes(raw)
    if actual != expected_blob:
        raise ScientificAssuranceLineageV16Error(
            f"SAL_V16_CONTENT_IDENTITY_MISMATCH:{label}:expected={expected_blob}:actual={actual}"
        )
    return _strict_object(raw, label)


def _validate(value: Mapping[str, Any], schema: str, label: str) -> None:
    try:
        validate_protocol_object(value, schema)
    except RuntimeSchemaError as exc:
        raise ScientificAssuranceLineageV16Error(
            f"SAL_V16_RUNTIME_SCHEMA_REJECTED:{label}:{exc}"
        ) from exc


def _record_index(registry: Mapping[str, Any], label: str) -> dict[str, Mapping[str, Any]]:
    rows = registry.get("records")
    if not isinstance(rows, list) or not rows:
        raise ScientificAssuranceLineageV16Error(f"SAL_V16_ROOT_RECORDS_INVALID:{label}")
    out: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("artifact_id"), str):
            raise ScientificAssuranceLineageV16Error(f"SAL_V16_ROOT_RECORD_INVALID:{label}")
        artifact_id = str(row["artifact_id"])
        if artifact_id in out:
            raise ScientificAssuranceLineageV16Error(
                f"SAL_V16_ROOT_RECORD_DUPLICATE:{label}:{artifact_id}"
            )
        out[artifact_id] = row
    return out


def _required_gate_ids(doc: Mapping[str, Any]) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageV16Error("SAL_V16_REQUIRED_CHECKS_NOT_ARRAY")
    ids = {
        str(row.get("id"))
        for row in rows
        if isinstance(row, Mapping) and row.get("required") is True
    }
    return ids


def _formula_atoms(formula: Mapping[str, Any]) -> set[str]:
    op = formula.get("op")
    if op == "ATOM":
        atom = formula.get("id")
        if not isinstance(atom, str) or not atom:
            raise ScientificAssuranceLineageV16Error("ENTAILMENT_ATOM_INVALID")
        return {atom}
    if op == "NOT":
        arg = formula.get("arg")
        if not isinstance(arg, Mapping):
            raise ScientificAssuranceLineageV16Error("ENTAILMENT_NOT_ARG_INVALID")
        return _formula_atoms(arg)
    if op in {"AND", "OR"}:
        args = formula.get("args")
        if not isinstance(args, list) or not args:
            raise ScientificAssuranceLineageV16Error(f"ENTAILMENT_{op}_ARGS_INVALID")
        atoms: set[str] = set()
        for arg in args:
            if not isinstance(arg, Mapping):
                raise ScientificAssuranceLineageV16Error(f"ENTAILMENT_{op}_ARG_INVALID")
            atoms |= _formula_atoms(arg)
        return atoms
    raise ScientificAssuranceLineageV16Error(f"ENTAILMENT_OP_INVALID:{op}")


def _eval_formula(formula: Mapping[str, Any], assignment: Mapping[str, bool]) -> bool:
    op = formula.get("op")
    if op == "ATOM":
        return bool(assignment[str(formula["id"])])
    if op == "NOT":
        return not _eval_formula(formula["arg"], assignment)
    if op == "AND":
        return all(_eval_formula(arg, assignment) for arg in formula["args"])
    if op == "OR":
        return any(_eval_formula(arg, assignment) for arg in formula["args"])
    raise ScientificAssuranceLineageV16Error(f"ENTAILMENT_OP_INVALID:{op}")


def finite_propositional_entailment(
    premise: Mapping[str, Any],
    target: Mapping[str, Any],
    *,
    max_atoms: int = 16,
) -> EntailmentResult:
    atoms = sorted(_formula_atoms(premise) | _formula_atoms(target))
    if len(atoms) > max_atoms:
        raise ScientificAssuranceLineageV16Error(
            f"ENTAILMENT_ATOM_LIMIT_EXCEEDED:{len(atoms)}:{max_atoms}"
        )
    for values in itertools.product((False, True), repeat=len(atoms)):
        assignment = dict(zip(atoms, values, strict=True))
        if _eval_formula(premise, assignment) and not _eval_formula(target, assignment):
            return EntailmentResult("REFUTED_BY_COUNTERMODEL", assignment)
    return EntailmentResult("PROVED", None)


def classify_entailment(
    missing_semantic_anchor_ids: tuple[str, ...],
    *,
    premise: Mapping[str, Any] | None = None,
    target: Mapping[str, Any] | None = None,
) -> EntailmentResult:
    if missing_semantic_anchor_ids:
        return EntailmentResult("BLOCKED_UNANCHORED_SEMANTICS", None)
    if premise is None or target is None:
        raise ScientificAssuranceLineageV16Error("ANCHORED_ENTAILMENT_FORMULA_REQUIRED")
    return finite_propositional_entailment(premise, target)


def verify_no_normative_authority_ex_nihilo_instance(
    authoritative_nodes: set[str],
    authority_edges: set[tuple[str, str]],
) -> str:
    """Verify the base-case necessity on one finite authority graph instance.

    Edges are (predecessor, successor). This function does not claim novelty or
    replace the standard finite-DAG proof; it gives the SAL checker a concrete
    fail-closed graph invariant.
    """
    if not authoritative_nodes:
        return "VACUOUS_EMPTY_AUTHORITY_SET"
    for u, v in authority_edges:
        if u not in authoritative_nodes or v not in authoritative_nodes:
            raise ScientificAssuranceLineageV16Error("AUTHORITY_EDGE_OUTSIDE_NODE_SET")

    indegree = {node: 0 for node in authoritative_nodes}
    outgoing: dict[str, list[str]] = {node: [] for node in authoritative_nodes}
    for u, v in authority_edges:
        outgoing[u].append(v)
        indegree[v] += 1

    queue = [node for node, deg in indegree.items() if deg == 0]
    if not queue:
        raise ScientificAssuranceLineageV16Error("NO_NORMATIVE_AUTHORITY_EX_NIHILO:CYCLE_OR_NO_SOURCE")
    seen = 0
    work = list(queue)
    local = dict(indegree)
    while work:
        node = work.pop()
        seen += 1
        for nxt in outgoing[node]:
            local[nxt] -= 1
            if local[nxt] == 0:
                work.append(nxt)
    if seen != len(authoritative_nodes):
        raise ScientificAssuranceLineageV16Error("NO_NORMATIVE_AUTHORITY_EX_NIHILO:AUTHORITY_GRAPH_CYCLE")
    return "SOURCE_NODE_EXISTS"


def verify_predecessor_semantic_entailment_audit() -> PredecessorSemanticAuditReport:
    root_v2 = _read_bound_json(ROOT_V2_PATH, ROOT_V2_BLOB, ROOT_V2_ID)
    if root_v2.get("registry_id") != ROOT_V2_ID:
        raise ScientificAssuranceLineageV16Error("SAL_V16_ROOT_V2_ID_REBINDING")
    r2 = _record_index(root_v2, ROOT_V2_ID)

    release_record = r2.get(RELEASE_V09_ID)
    if release_record is None:
        raise ScientificAssuranceLineageV16Error("SAL_V16_AUTHORITATIVE_PREMISE_NOT_REGISTERED")
    if release_record.get("authority_status") != "ATTESTED_SUCCESSOR_AT_COMMIT":
        raise ScientificAssuranceLineageV16Error("SAL_V16_AUTHORITATIVE_PREMISE_STATUS_REBINDING")
    if release_record.get("git_blob_sha1") != RELEASE_V09_BLOB:
        raise ScientificAssuranceLineageV16Error("SAL_V16_AUTHORITATIVE_PREMISE_BLOB_REBINDING")

    release_v09 = _read_bound_json(RELEASE_V09_PATH, RELEASE_V09_BLOB, RELEASE_V09_ID)
    if not REQUIRED_CHECK_IDS.issubset(_required_gate_ids(release_v09)):
        raise ScientificAssuranceLineageV16Error("PREDECESSOR_TEXTUAL_REQUIRED_CHECKS_MISSING")
    shortcuts = release_v09.get("forbidden_shortcuts")
    if not isinstance(shortcuts, list) or not REQUIRED_FORBIDDEN_SHORTCUTS.issubset(set(shortcuts)):
        raise ScientificAssuranceLineageV16Error("PREDECESSOR_ANTI_SELF_AUTHENTICATION_TEXT_MISSING")

    direct_profile_records = [
        row for row in r2.values()
        if row.get("artifact_id") == TARGET_PROFILE_ID
        or row.get("kind") == "LINEAGE_TRANSITION_PROFILE"
        or row.get("expected_schema") == "AIFC/lineage-transition-profile/v1"
    ]
    if direct_profile_records:
        raise ScientificAssuranceLineageV16Error(
            "DIRECT_PREDECESSOR_TRANSITION_PROFILE_AUTHORITY_UNEXPECTEDLY_PRESENT"
        )

    missing = tuple(sorted(anchor for anchor in REQUIRED_SEMANTIC_ANCHOR_IDS if anchor not in r2))
    state = classify_entailment(missing).state
    if state != "BLOCKED_UNANCHORED_SEMANTICS":
        raise ScientificAssuranceLineageV16Error("SAL_V16_CURRENT_ENTAILMENT_STATE_NOT_BLOCKED")

    target_profile = _read_bound_json(TARGET_PROFILE_PATH, TARGET_PROFILE_BLOB, TARGET_PROFILE_ID)
    if target_profile.get("profile_id") != TARGET_PROFILE_ID:
        raise ScientificAssuranceLineageV16Error("SAL_V16_TARGET_PROFILE_ID_REBINDING")

    audit_obj = _strict_object((REPO_ROOT / ENTAILMENT_AUDIT_PATH).read_bytes(), "ENTAILMENT_AUDIT")
    _validate(audit_obj, "AIFC/predecessor-semantic-entailment-audit/v1", "ENTAILMENT_AUDIT")
    if audit_obj.get("predecessor_registry_git_blob_sha1") != ROOT_V2_BLOB:
        raise ScientificAssuranceLineageV16Error("ENTAILMENT_AUDIT_ROOT_REBINDING")
    if tuple(sorted(audit_obj.get("missing_semantic_anchor_ids", []))) != missing:
        raise ScientificAssuranceLineageV16Error("ENTAILMENT_AUDIT_MISSING_ANCHOR_SET_REBINDING")
    if audit_obj.get("result") != state or audit_obj.get("countermodel") is not None:
        raise ScientificAssuranceLineageV16Error("ENTAILMENT_AUDIT_RESULT_REBINDING")

    root_v1 = _read_bound_json(ROOT_V1_PATH, ROOT_V1_BLOB, ROOT_V1_ID)
    if root_v1.get("bootstrap_root_commit") != BOOTSTRAP_COMMIT:
        raise ScientificAssuranceLineageV16Error("BOOTSTRAP_DESIGNATION_COMMIT_REBINDING")
    r1 = _record_index(root_v1, ROOT_V1_ID)
    expected_bootstrap = {
        RELEASE_V08_ID: (RELEASE_V08_PATH, RELEASE_V08_BLOB),
        ADMISSION_ORDER_ID: (ADMISSION_ORDER_PATH, ADMISSION_ORDER_BLOB),
    }
    for artifact_id, (path, blob) in expected_bootstrap.items():
        row = r1.get(artifact_id)
        if row is None or row.get("authority_status") != "HISTORICAL_ROOT_AT_BOOTSTRAP_COMMIT":
            raise ScientificAssuranceLineageV16Error(f"BOOTSTRAP_DESIGNATED_OBJECT_STATUS:{artifact_id}")
        if row.get("git_blob_sha1") != blob:
            raise ScientificAssuranceLineageV16Error(f"BOOTSTRAP_DESIGNATED_OBJECT_BLOB:{artifact_id}")
        if git_tree_blob(BOOTSTRAP_COMMIT, path) != blob:
            raise ScientificAssuranceLineageV16Error(f"BOOTSTRAP_DESIGNATED_OBJECT_MEMBERSHIP:{artifact_id}")

    bootstrap_obj = _strict_object((REPO_ROOT / BOOTSTRAP_STATUS_PATH).read_bytes(), "BOOTSTRAP_STATUS")
    _validate(bootstrap_obj, "AIFC/bootstrap-authority-base-case-status/v1", "BOOTSTRAP_STATUS")
    if bootstrap_obj.get("authority_basis_status") != "IMPLICIT_NOT_YET_FIRST_CLASS":
        raise ScientificAssuranceLineageV16Error("BOOTSTRAP_AUTHORITY_BASE_CASE_SELF_PROMOTION")
    if bootstrap_obj.get("retroactive_discovery_of_preexisting_authority") is not False:
        raise ScientificAssuranceLineageV16Error("BOOTSTRAP_RETROACTIVE_AUTHORITY_REWRITE")
    if bootstrap_obj.get("normative_authority_claim") != "NOT_ESTABLISHED_BY_THIS_OBJECT":
        raise ScientificAssuranceLineageV16Error("BOOTSTRAP_STATUS_OBJECT_SELF_AUTHORIZATION")

    for commit in DEPENDENCY_LOCK_TESTED_COMMITS:
        if git_tree_blob(commit, DEPENDENCY_LOCK_PATH) != DEPENDENCY_LOCK_BLOB:
            raise ScientificAssuranceLineageV16Error(f"HISTORICAL_REPLAY_ENVIRONMENT_LOCK_DRIFT:{commit}")

    env_obj = _strict_object((REPO_ROOT / ENVIRONMENT_AUDIT_PATH).read_bytes(), "ENVIRONMENT_AUDIT")
    _validate(env_obj, "AIFC/historical-replay-environment-audit/v1", "ENVIRONMENT_AUDIT")
    if env_obj.get("same_dependency_lock_blob") is not True:
        raise ScientificAssuranceLineageV16Error("HISTORICAL_REPLAY_DEPENDENCY_LOCK_STATUS_REBINDING")
    if env_obj.get("historical_interpreter_identity_bound") is not False:
        raise ScientificAssuranceLineageV16Error("HISTORICAL_INTERPRETER_IDENTITY_SELF_PROMOTION")
    if env_obj.get("historical_platform_identity_bound") is not False:
        raise ScientificAssuranceLineageV16Error("HISTORICAL_PLATFORM_IDENTITY_SELF_PROMOTION")

    verify_no_normative_authority_ex_nihilo_instance(
        {"BOOTSTRAP_DESIGNATION", "R_V2_AUTHORITY"},
        {("BOOTSTRAP_DESIGNATION", "R_V2_AUTHORITY")},
    )

    return PredecessorSemanticAuditReport(
        direct_predecessor_transition_profile_authority="ABSENT_CONFIRMED",
        predecessor_anti_self_authentication_constraints=True,
        predecessor_semantic_entailment=state,
        missing_semantic_anchor_ids=missing,
        bootstrap_authority_basis_status="IMPLICIT_NOT_YET_FIRST_CLASS",
        dependency_lock_identity_same=True,
        historical_replay_environment_identity_general="NOT_ESTABLISHED",
    )
