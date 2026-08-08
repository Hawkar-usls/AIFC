#!/usr/bin/env python3
"""Repository checker for SAL v1.6 Predecessor Semantic Entailment Audit."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import load_json_strict  # noqa: E402
from schema_runtime import RuntimeSchemaError, validate_protocol_object  # noqa: E402
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes  # noqa: E402
from scientific_assurance_lineage_v16 import (  # noqa: E402
    ScientificAssuranceLineageV16Error,
    verify_predecessor_semantic_entailment_audit,
)

REQUIRED_FILES = (
    "schemas/predecessor-semantic-entailment-audit-v1.schema.json",
    "schemas/bootstrap-authority-base-case-status-v1.schema.json",
    "schemas/historical-replay-environment-audit-v1.schema.json",
    "schemas/schema-identity-registry-v6.schema.json",
    "conformance/AIFC-PREDECESSOR-SEMANTIC-ENTAILMENT-AUDIT-v1.json",
    "conformance/AIFC-BOOTSTRAP-AUTHORITY-BASE-CASE-STATUS-v1.json",
    "conformance/AIFC-HISTORICAL-REPLAY-ENVIRONMENT-AUDIT-v1.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v6.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.13-draft.json",
    "reference/verifier/scientific_assurance_lineage_v16.py",
    "reference/tests/test_sal_predecessor_semantic_entailment_v16.py",
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.5.md",
    ".github/workflows/sal-predecessor-entailment-v16.yml",
    "tools/check_sal_predecessor_entailment_v16.py",
)

NEW_GATES = frozenset({
    "PREDECESSOR_SEMANTIC_ENTAILMENT_AUDIT",
    "PREDECESSOR_SEMANTIC_ANCHOR_COVERAGE",
    "BOOTSTRAP_AUTHORITY_BASE_CASE_EXPLICITNESS",
    "HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY",
})


def _required_gate_ids(doc: dict) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageV16Error("SAL_V16_REQUIRED_CHECKS_NOT_ARRAY")
    ids = [row.get("id") for row in rows if isinstance(row, dict) and row.get("required") is True]
    if not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids)):
        raise ScientificAssuranceLineageV16Error("SAL_V16_REQUIRED_GATE_IDS_INVALID")
    return set(ids)


def _check_schema_registry_v6() -> int:
    path = ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v6.json"
    registry = load_json_strict(path)
    if not isinstance(registry, dict):
        raise ScientificAssuranceLineageV16Error("SAL_V16_SCHEMA_REGISTRY_NOT_OBJECT")
    try:
        validate_protocol_object(registry, "AIFC/schema-identity-registry/v6")
    except RuntimeSchemaError as exc:
        raise ScientificAssuranceLineageV16Error(f"SAL_V16_SCHEMA_REGISTRY_RUNTIME:{exc}") from exc
    if registry.get("predecessor_registry_git_blob_sha1") != "709331f8b59496aac799142ab2311b3abe6353d8":
        raise ScientificAssuranceLineageV16Error("SAL_V16_SCHEMA_REGISTRY_PREDECESSOR_REBINDING")

    rows = registry.get("records")
    if not isinstance(rows, list) or len(rows) != 4:
        raise ScientificAssuranceLineageV16Error("SAL_V16_SCHEMA_REGISTRY_RECORD_COUNT")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ScientificAssuranceLineageV16Error("SAL_V16_SCHEMA_REGISTRY_ROW_INVALID")
        schema_id = str(row.get("schema_id"))
        if schema_id in seen:
            raise ScientificAssuranceLineageV16Error("SAL_V16_SCHEMA_REGISTRY_DUPLICATE")
        seen.add(schema_id)
        source = ROOT / str(row.get("source_path"))
        raw = source.read_bytes()
        if git_blob_sha1_bytes(raw) != row.get("git_blob_sha1"):
            raise ScientificAssuranceLineageV16Error(f"SAL_V16_SCHEMA_GIT_BLOB_REBINDING:{schema_id}")
        if hashlib.sha256(raw).hexdigest() != row.get("raw_schema_sha256"):
            raise ScientificAssuranceLineageV16Error(f"SAL_V16_SCHEMA_RAW_SHA256_REBINDING:{schema_id}")
    return len(rows)


def _check_release_frontier() -> None:
    pred = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.12-draft.json")
    succ = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.13-draft.json")
    if not isinstance(pred, dict) or not isinstance(succ, dict):
        raise ScientificAssuranceLineageV16Error("SAL_V16_RELEASE_GATE_NOT_OBJECT")
    pred_ids = _required_gate_ids(pred)
    succ_ids = _required_gate_ids(succ)
    if len(pred_ids) != 88 or len(succ_ids) != 92:
        raise ScientificAssuranceLineageV16Error(
            f"SAL_V16_RELEASE_GATE_COUNT_REBINDING:{len(pred_ids)}:{len(succ_ids)}"
        )
    if succ_ids - pred_ids != NEW_GATES or pred_ids - succ_ids:
        raise ScientificAssuranceLineageV16Error("SAL_V16_RELEASE_GATE_NOT_EXACT_ADDITIVE_EXTENSION")


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ScientificAssuranceLineageV16Error("SAL_V16_REQUIRED_FILES_MISSING:" + ",".join(missing))

    registered = _check_schema_registry_v6()
    _check_release_frontier()
    report = verify_predecessor_semantic_entailment_audit()

    if report.direct_predecessor_transition_profile_authority != "ABSENT_CONFIRMED":
        raise ScientificAssuranceLineageV16Error("SAL_V16_DIRECT_PROFILE_AUTHORITY_RESULT_REBINDING")
    if not report.predecessor_anti_self_authentication_constraints:
        raise ScientificAssuranceLineageV16Error("SAL_V16_PREDECESSOR_CONSTRAINT_RESULT_REBINDING")
    if report.predecessor_semantic_entailment != "BLOCKED_UNANCHORED_SEMANTICS":
        raise ScientificAssuranceLineageV16Error("SAL_V16_ENTAILMENT_RESULT_REBINDING")
    if len(report.missing_semantic_anchor_ids) != 3:
        raise ScientificAssuranceLineageV16Error("SAL_V16_MISSING_ANCHOR_COUNT_REBINDING")
    if report.bootstrap_authority_basis_status != "IMPLICIT_NOT_YET_FIRST_CLASS":
        raise ScientificAssuranceLineageV16Error("SAL_V16_BOOTSTRAP_STATUS_REBINDING")
    if not report.dependency_lock_identity_same:
        raise ScientificAssuranceLineageV16Error("SAL_V16_DEPENDENCY_LOCK_CONTINUITY_REBINDING")
    if report.historical_replay_environment_identity_general != "NOT_ESTABLISHED":
        raise ScientificAssuranceLineageV16Error("SAL_V16_HISTORICAL_ENVIRONMENT_SELF_PROMOTION")

    print(f"SAL_PREDECESSOR_ENTAILMENT_REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")
    print("SAL_V16_SCHEMA_HEADERS = PASS (4/4)")
    print(f"SAL_SCHEMA_IDENTITY_REGISTRATION_V6 = PASS ({registered}/4 dual-bound candidate identities)")
    print("DIRECT_PREDECESSOR_TRANSITION_PROFILE_AUTHORITY = ABSENT_CONFIRMED")
    print("PREDECESSOR_ANTI_SELF_AUTHENTICATION_CONSTRAINTS = PRESENT_CONFIRMED")
    print("PREDECESSOR_SEMANTIC_ENTAILMENT = BLOCKED_UNANCHORED_SEMANTICS")
    print("MISSING_PREDECESSOR_SEMANTIC_ANCHORS = 3/3 IDENTIFIED")
    for anchor in report.missing_semantic_anchor_ids:
        print(f"MISSING_SEMANTIC_ANCHOR = {anchor}")
    print("AUTHORITATIVE_TEXT_IDENTITY_NOT_EXECUTABLE_SEMANTIC_IDENTITY = ENFORCED")
    print("EXISTING_BOOTSTRAP_ROOT_DESIGNATION = 908de7afddcf9f72c98c2b3fb696a41be1e438e0")
    print("BOOTSTRAP_ROOT_EXTERNAL_AUTHORITY_BASIS = IMPLICIT_NOT_YET_FIRST_CLASS")
    print("RETROACTIVE_DISCOVERY_OF_PREEXISTING_AUTHORITY = FALSE")
    print("EXTERNAL_BOOTSTRAP_RATIFICATION = NOT_PERFORMED")
    print("NO_NORMATIVE_AUTHORITY_EX_NIHILO = LEMMA_CANDIDATE_UNDER_EXPLICIT_DAG_ASSUMPTIONS")
    print("HISTORICAL_DEPENDENCY_LOCK_IDENTITY = SAME_BLOB_CONFIRMED_FOR_4_OF_4_TESTED_COMMITS")
    print("HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY_GENERAL = NOT_ESTABLISHED")
    print("SAL_RELEASE_GATE_88_TO_92 = PASS (4 additive gates)")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP = NOT_YET_ESTABLISHED")
    print("EXOGENOUS_AUTHORITY_EPOCH_NECESSITY = NOT_YET_ESTABLISHED")
    print("NORMATIVE_ROOT_LINEAGE_GENERAL = NOT_ESTABLISHED")
    print("GATE_DEFINITION_HISTORICAL_ANCHOR = NOT_ESTABLISHED")
    print("GATE_ATOM_SEMANTIC_IDENTITY = NOT_ESTABLISHED")
    print("AUTHORITY_CLOSED_PROOF_GENERAL = NOT_ESTABLISHED")
    print("REAL_SUCCESSOR_WRAPPED_REPLAY = NOT_YET_ESTABLISHED")
    print("HISTORICAL_KEY_LIFECYCLE = BLOCKED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScientificAssuranceLineageV16Error as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
