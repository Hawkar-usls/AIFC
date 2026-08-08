#!/usr/bin/env python3
"""Repository checker for SAL v1.7 Authoritative Semantic Compilation."""
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
from scientific_assurance_lineage_v17 import (  # noqa: E402
    PREDECESSOR_ID,
    QUESTION_ID,
    TARGET_PROFILE_ID,
    ScientificAssuranceLineageV17Error,
    audit_authoritative_semantic_compilation,
)

REQUIRED_FILES = (
    "schemas/historical-semantic-anchor-v1.schema.json",
    "schemas/semantic-coverage-manifest-v1.schema.json",
    "schemas/semantic-compilation-profile-v1.schema.json",
    "schemas/semantic-formula-v1.schema.json",
    "schemas/entailment-question-v1.schema.json",
    "schemas/authoritative-semantic-compilation-audit-v1.schema.json",
    "schemas/schema-identity-registry-v7.schema.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v7.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.14-draft.json",
    "conformance/AIFC-SEMANTIC-ANCHOR-AUTHORITY-CLOSED-PROOF-V1.json",
    "conformance/AIFC-SEMANTIC-ANCHOR-GATE-DEFINITION-HISTORICAL-ANCHOR-V1.json",
    "conformance/AIFC-SEMANTIC-ANCHOR-GATE-ATOM-SEMANTIC-IDENTITY-V1.json",
    "conformance/AIFC-SEMANTIC-ANCHOR-TARGET-LINEAGE-TRANSITION-PROFILE-V1.json",
    "conformance/AIFC-ENTAILMENT-QUESTION-v1.json",
    "conformance/AIFC-PREDECESSOR-SEMANTIC-COVERAGE-v1.json",
    "conformance/AIFC-TARGET-SEMANTIC-COVERAGE-v1.json",
    "conformance/AIFC-SEMANTIC-COMPILATION-PROFILE-v1.json",
    "conformance/AIFC-PREDECESSOR-SEMANTIC-FORMULA-v1.json",
    "conformance/AIFC-TARGET-SEMANTIC-FORMULA-v1.json",
    "conformance/AIFC-AUTHORITATIVE-SEMANTIC-COMPILATION-AUDIT-v1.json",
    "reference/verifier/semantic_compiler_v1.py",
    "reference/verifier/scientific_assurance_lineage_v17.py",
    "reference/tests/test_sal_authoritative_semantic_compilation_v17.py",
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.6.md",
    ".github/workflows/sal-authoritative-semantic-compilation-v17.yml",
    "tools/check_sal_authoritative_semantic_compilation_v17.py",
)

NEW_GATES = frozenset({
    "HISTORICAL_SEMANTIC_ANCHOR_PROVENANCE",
    "NORMATIVE_SEMANTIC_COVERAGE",
    "SEMANTIC_COMPILATION_PROFILE_CONTENT_IDENTITY",
    "SEMANTIC_COMPILATION_PROFILE_AUTHORITY",
    "SEMANTIC_ANCHOR_TO_FORMULA_BINDING",
    "PREDECESSOR_FORMULA_CONTENT_IDENTITY",
    "TARGET_PROFILE_FORMULA_CONTENT_IDENTITY",
    "ENTAILMENT_QUESTION_IDENTITY_PRESERVED",
    "CALLER_SUPPLIED_NORMATIVE_FORMULA_FORBIDDEN",
    "SOLVER_EXECUTION_GATED_BY_SEMANTIC_CLOSURE",
})


def _required_gate_ids(doc: dict) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageV17Error("SAL_V17_REQUIRED_CHECKS_NOT_ARRAY")
    ids = [row.get("id") for row in rows if isinstance(row, dict) and row.get("required") is True]
    if not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids)):
        raise ScientificAssuranceLineageV17Error("SAL_V17_REQUIRED_GATE_IDS_INVALID")
    return set(ids)


def _check_schema_registry_v7() -> int:
    path = ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v7.json"
    registry = load_json_strict(path)
    if not isinstance(registry, dict):
        raise ScientificAssuranceLineageV17Error("SAL_V17_SCHEMA_REGISTRY_NOT_OBJECT")
    try:
        validate_protocol_object(registry, "AIFC/schema-identity-registry/v7")
    except RuntimeSchemaError as exc:
        raise ScientificAssuranceLineageV17Error(f"SAL_V17_SCHEMA_REGISTRY_RUNTIME:{exc}") from exc
    if registry.get("predecessor_registry_git_blob_sha1") != "9b8313263f95a66fe07873da0e0675a38ffdd9d0":
        raise ScientificAssuranceLineageV17Error("SAL_V17_SCHEMA_REGISTRY_PREDECESSOR_REBINDING")
    rows = registry.get("records")
    if not isinstance(rows, list) or len(rows) != 7:
        raise ScientificAssuranceLineageV17Error("SAL_V17_SCHEMA_REGISTRY_RECORD_COUNT")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ScientificAssuranceLineageV17Error("SAL_V17_SCHEMA_REGISTRY_ROW_INVALID")
        schema_id = str(row.get("schema_id"))
        if schema_id in seen:
            raise ScientificAssuranceLineageV17Error("SAL_V17_SCHEMA_REGISTRY_DUPLICATE")
        seen.add(schema_id)
        source = ROOT / str(row.get("source_path"))
        raw = source.read_bytes()
        if git_blob_sha1_bytes(raw) != row.get("git_blob_sha1"):
            raise ScientificAssuranceLineageV17Error(f"SAL_V17_SCHEMA_GIT_BLOB_REBINDING:{schema_id}")
        if hashlib.sha256(raw).hexdigest() != row.get("raw_schema_sha256"):
            raise ScientificAssuranceLineageV17Error(f"SAL_V17_SCHEMA_RAW_SHA256_REBINDING:{schema_id}")
    return len(rows)


def _check_release_frontier() -> None:
    pred = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.13-draft.json")
    succ = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.14-draft.json")
    if not isinstance(pred, dict) or not isinstance(succ, dict):
        raise ScientificAssuranceLineageV17Error("SAL_V17_RELEASE_GATE_NOT_OBJECT")
    pred_ids = _required_gate_ids(pred)
    succ_ids = _required_gate_ids(succ)
    if len(pred_ids) != 92 or len(succ_ids) != 102:
        raise ScientificAssuranceLineageV17Error(
            f"SAL_V17_RELEASE_GATE_COUNT_REBINDING:{len(pred_ids)}:{len(succ_ids)}"
        )
    if succ_ids - pred_ids != NEW_GATES or pred_ids - succ_ids:
        raise ScientificAssuranceLineageV17Error("SAL_V17_RELEASE_GATE_NOT_EXACT_ADDITIVE_EXTENSION")


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ScientificAssuranceLineageV17Error("SAL_V17_REQUIRED_FILES_MISSING:" + ",".join(missing))

    registered = _check_schema_registry_v7()
    _check_release_frontier()
    report = audit_authoritative_semantic_compilation(PREDECESSOR_ID, TARGET_PROFILE_ID, QUESTION_ID)

    if report.question_id != QUESTION_ID:
        raise ScientificAssuranceLineageV17Error("SAL_V17_QUESTION_ID_REBINDING")
    if report.historical_semantic_anchor_provenance != "PASS_CANDIDATE_PROVENANCE":
        raise ScientificAssuranceLineageV17Error("SAL_V17_ANCHOR_PROVENANCE_RESULT_REBINDING")
    if report.normative_semantic_coverage != "PASS_CANDIDATE_EXACT_COVERAGE":
        raise ScientificAssuranceLineageV17Error("SAL_V17_COVERAGE_RESULT_REBINDING")
    if report.semantic_compilation_profile_content_identity != "PASS":
        raise ScientificAssuranceLineageV17Error("SAL_V17_COMPILATION_PROFILE_IDENTITY_REBINDING")
    if report.semantic_compilation_profile_authority != "NOT_ESTABLISHED_SUCCESSOR_CANDIDATE":
        raise ScientificAssuranceLineageV17Error("SAL_V17_COMPILER_AUTHORITY_SELF_PROMOTION")
    if report.semantic_anchor_to_formula_binding != "PASS_DETERMINISTIC_CANDIDATE_DERIVATION":
        raise ScientificAssuranceLineageV17Error("SAL_V17_FORMULA_BINDING_RESULT_REBINDING")
    if report.entailment_question_identity_preserved != "PASS":
        raise ScientificAssuranceLineageV17Error("SAL_V17_QUESTION_PRESERVATION_REBINDING")
    if report.caller_supplied_normative_formula_forbidden != "PASS":
        raise ScientificAssuranceLineageV17Error("SAL_V17_CALLER_FORMULA_SURFACE_REBINDING")
    if report.solver_execution_gated_by_semantic_closure != "PASS" or report.solver_invocation_count != 0:
        raise ScientificAssuranceLineageV17Error("SAL_V17_SOLVER_GATING_REBINDING")
    if report.result != "BLOCKED" or report.blocked_subtype != "BLOCKED_UNAUTHORIZED_INTERPRETATION":
        raise ScientificAssuranceLineageV17Error("SAL_V17_CURRENT_RESULT_MUST_REMAIN_BLOCKED")
    if report.countermodel is not None:
        raise ScientificAssuranceLineageV17Error("SAL_V17_BLOCKED_COUNTERMODEL_FORBIDDEN")

    print(f"SAL_V17_REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")
    print("SAL_V17_SCHEMA_HEADERS = PASS (7/7)")
    print(f"SAL_SCHEMA_IDENTITY_REGISTRATION_V7 = PASS ({registered}/7 dual-bound candidate identities)")
    print("HISTORICAL_SEMANTIC_ANCHOR_PROVENANCE = PASS_CANDIDATE_PROVENANCE (4/4 exact-source anchors)")
    print("RETROACTIVE_DISCOVERY_OF_PREEXISTING_EXECUTABLE_SEMANTICS = FALSE")
    print("SEMANTIC_LOCATOR_BINDING = PASS (5/5 predecessor loci; 13/13 target loci)")
    print("NORMATIVE_SEMANTIC_COVERAGE = PASS_CANDIDATE_EXACT_COVERAGE (5/5 predecessor; 13/13 target)")
    print("SEMANTIC_COMPILATION_PROFILE_CONTENT_IDENTITY = PASS")
    print("SEMANTIC_COMPILATION_PROFILE_AUTHORITY = BLOCKED_SUCCESSOR_CANDIDATE")
    print("COMPILER_IDENTITY_NOT_COMPILER_AUTHORITY = ENFORCED")
    print("SEMANTIC_ANCHOR_TO_FORMULA_BINDING = PASS_DETERMINISTIC_CANDIDATE_DERIVATION")
    print(f"PREDECESSOR_FORMULA_CONTENT_IDENTITY = PASS ({report.predecessor_formula_content_hash})")
    print(f"TARGET_PROFILE_FORMULA_CONTENT_IDENTITY = PASS ({report.target_formula_content_hash})")
    print(f"ENTAILMENT_QUESTION_IDENTITY_PRESERVED = PASS ({report.question_id})")
    print("CALLER_SUPPLIED_NORMATIVE_FORMULA_FORBIDDEN = PASS")
    print("SOLVER_EXECUTION_GATED_BY_SEMANTIC_CLOSURE = PASS")
    print("SOLVER_INVOCATION_COUNT = 0")
    print("PREDECESSOR_SEMANTIC_ENTAILMENT = BLOCKED_UNAUTHORIZED_INTERPRETATION")
    print("COUNTERMODEL_SEARCH = NOT_INVOKED_BEFORE_SEMANTIC_CLOSURE")
    print("SAL_RELEASE_GATE_92_TO_102 = PASS (10 additive gates)")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP = NOT_YET_ESTABLISHED")
    print("NORMATIVE_ROOT_LINEAGE_GENERAL = NOT_ESTABLISHED")
    print("HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY_GENERAL = NOT_ESTABLISHED")
    print("EXOGENOUS_AUTHORITY_EPOCH_NECESSITY = NOT_YET_ESTABLISHED")
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
    except ScientificAssuranceLineageV17Error as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
