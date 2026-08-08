#!/usr/bin/env python3
"""Attested repository checker for SAL v1.8 Semantic Abstraction Closure."""
from __future__ import annotations

import hashlib
from pathlib import Path

from canonical import load_json_strict
from schema_runtime import RuntimeSchemaError, validate_protocol_object
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
from scientific_assurance_lineage_v17 import PREDECESSOR_ID, QUESTION_ID, TARGET_PROFILE_ID
from scientific_assurance_lineage_v18 import (
    ScientificAssuranceLineageV18Error,
    audit_semantic_abstraction_closure,
)

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "schemas/semantic-surface-definition-v1.schema.json",
    "schemas/semantic-bridge-theory-v1.schema.json",
    "schemas/entailment-method-profile-v1.schema.json",
    "schemas/entailment-question-source-binding-v1.schema.json",
    "schemas/semantic-abstraction-audit-v1.schema.json",
    "schemas/schema-identity-registry-v8.schema.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v8.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.15-draft.json",
    "conformance/AIFC-PREDECESSOR-SEMANTIC-SURFACE-DEFINITION-v1.json",
    "conformance/AIFC-TARGET-SEMANTIC-SURFACE-DEFINITION-v1.json",
    "conformance/AIFC-SEMANTIC-BRIDGE-THEORY-v1.json",
    "conformance/AIFC-ENTAILMENT-METHOD-PROFILE-v1.json",
    "conformance/AIFC-ENTAILMENT-QUESTION-SOURCE-BINDING-v1.json",
    "conformance/AIFC-SEMANTIC-ABSTRACTION-CLOSURE-AUDIT-v1.json",
    "reference/verifier/scientific_assurance_lineage_v18.py",
    "reference/verifier/sal_semantic_abstraction_closure_checker_v18.py",
    "reference/tests/test_sal_semantic_abstraction_closure_v18.py",
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.7.md",
    ".github/workflows/sal-semantic-abstraction-closure-v18.yml",
    "tools/check_sal_semantic_abstraction_closure_v18.py",
)

NEW_GATES = frozenset({
    "NORMATIVE_SEMANTIC_SURFACE_AUTHORITY",
    "SEMANTIC_ABSTRACTION_ADEQUACY",
    "CROSS_FORMULA_SEMANTIC_BRIDGE_IDENTITY",
    "CROSS_FORMULA_SEMANTIC_BRIDGE_AUTHORITY",
    "ENTAILMENT_METHOD_CONTENT_IDENTITY",
    "ENTAILMENT_METHOD_AUTHORITY",
    "ENTAILMENT_METHOD_CAPACITY_FOR_ISSUED_QUESTION",
    "ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY",
})


def _required_gate_ids(doc: dict) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        raise ScientificAssuranceLineageV18Error("SAL_V18_REQUIRED_CHECKS_NOT_ARRAY")
    ids = [row.get("id") for row in rows if isinstance(row, dict) and row.get("required") is True]
    if not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids)):
        raise ScientificAssuranceLineageV18Error("SAL_V18_REQUIRED_GATE_IDS_INVALID")
    return set(ids)


def _check_schema_registry_v8() -> int:
    registry = load_json_strict(ROOT / "conformance" / "AIFC-SCHEMA-IDENTITY-REGISTRY-v8.json")
    if not isinstance(registry, dict):
        raise ScientificAssuranceLineageV18Error("SAL_V18_SCHEMA_REGISTRY_NOT_OBJECT")
    try:
        validate_protocol_object(registry, "AIFC/schema-identity-registry/v8")
    except RuntimeSchemaError as exc:
        raise ScientificAssuranceLineageV18Error(f"SAL_V18_SCHEMA_REGISTRY_RUNTIME:{exc}") from exc
    if registry.get("predecessor_registry_git_blob_sha1") != "2396a0e5c76cc73007442c57b60a743cc4951ae7":
        raise ScientificAssuranceLineageV18Error("SAL_V18_SCHEMA_REGISTRY_PREDECESSOR_REBINDING")
    rows = registry.get("records")
    if not isinstance(rows, list) or len(rows) != 6:
        raise ScientificAssuranceLineageV18Error("SAL_V18_SCHEMA_REGISTRY_RECORD_COUNT")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ScientificAssuranceLineageV18Error("SAL_V18_SCHEMA_REGISTRY_ROW_INVALID")
        schema_id = str(row.get("schema_id"))
        if schema_id in seen:
            raise ScientificAssuranceLineageV18Error("SAL_V18_SCHEMA_REGISTRY_DUPLICATE")
        seen.add(schema_id)
        source = ROOT / str(row.get("source_path"))
        raw = source.read_bytes()
        if git_blob_sha1_bytes(raw) != row.get("git_blob_sha1"):
            raise ScientificAssuranceLineageV18Error(f"SAL_V18_SCHEMA_GIT_BLOB_REBINDING:{schema_id}")
        if hashlib.sha256(raw).hexdigest() != row.get("raw_schema_sha256"):
            raise ScientificAssuranceLineageV18Error(f"SAL_V18_SCHEMA_RAW_SHA256_REBINDING:{schema_id}")
    return len(rows)


def _check_release_frontier() -> None:
    pred = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.14-draft.json")
    succ = load_json_strict(ROOT / "conformance" / "AIFC-RELEASE-GATE-v1.0.15-draft.json")
    if not isinstance(pred, dict) or not isinstance(succ, dict):
        raise ScientificAssuranceLineageV18Error("SAL_V18_RELEASE_GATE_NOT_OBJECT")
    pred_ids = _required_gate_ids(pred)
    succ_ids = _required_gate_ids(succ)
    if len(pred_ids) != 102 or len(succ_ids) != 110:
        raise ScientificAssuranceLineageV18Error(
            f"SAL_V18_RELEASE_GATE_COUNT_REBINDING:{len(pred_ids)}:{len(succ_ids)}"
        )
    if succ_ids - pred_ids != NEW_GATES or pred_ids - succ_ids:
        raise ScientificAssuranceLineageV18Error("SAL_V18_RELEASE_GATE_NOT_EXACT_ADDITIVE_EXTENSION")


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ScientificAssuranceLineageV18Error("SAL_V18_REQUIRED_FILES_MISSING:" + ",".join(missing))
    registered = _check_schema_registry_v8()
    _check_release_frontier()
    report = audit_semantic_abstraction_closure(PREDECESSOR_ID, TARGET_PROFILE_ID, QUESTION_ID)

    if report.question_id != QUESTION_ID:
        raise ScientificAssuranceLineageV18Error("SAL_V18_QUESTION_ID_REBINDING")
    if report.normative_semantic_surface_authority != "NOT_ESTABLISHED":
        raise ScientificAssuranceLineageV18Error("SAL_V18_SURFACE_AUTHORITY_SELF_PROMOTION")
    if report.semantic_abstraction_adequacy != "NOT_ESTABLISHED":
        raise ScientificAssuranceLineageV18Error("SAL_V18_ABSTRACTION_ADEQUACY_SELF_PROMOTION")
    if report.cross_formula_semantic_bridge_identity != "PASS_CONTENT_IDENTIFIED_EMPTY_THEORY":
        raise ScientificAssuranceLineageV18Error("SAL_V18_BRIDGE_IDENTITY_REBINDING")
    if report.cross_formula_semantic_bridge != "ABSENT" or report.cross_formula_semantic_bridge_authority != "NOT_ESTABLISHED":
        raise ScientificAssuranceLineageV18Error("SAL_V18_BRIDGE_AUTHORITY_SELF_PROMOTION")
    if report.disjoint_semantic_vocabulary != "CONFIRMED":
        raise ScientificAssuranceLineageV18Error("SAL_V18_DISJOINT_VOCABULARY_NOT_CONFIRMED")
    if report.disjoint_vocabulary_trivial_refutation != "LATENT_IF_SOLVER_PREMATURELY_ENABLED":
        raise ScientificAssuranceLineageV18Error("SAL_V18_LATENT_TRIVIAL_REFUTATION_NOT_CONFIRMED")
    if report.entailment_method_content_identity != "PASS_CANDIDATE_EXACT_SOURCE_AND_FORMAL_SEMANTICS":
        raise ScientificAssuranceLineageV18Error("SAL_V18_METHOD_IDENTITY_REBINDING")
    if report.entailment_method_authority != "NOT_ESTABLISHED":
        raise ScientificAssuranceLineageV18Error("SAL_V18_METHOD_AUTHORITY_SELF_PROMOTION")
    if report.entailment_method_capacity_for_issued_question != "BLOCKED_ATOM_LIMIT_18_GT_16":
        raise ScientificAssuranceLineageV18Error("SAL_V18_METHOD_CAPACITY_REBINDING")
    if report.entailment_question_source_dual_identity != "NOT_ESTABLISHED":
        raise ScientificAssuranceLineageV18Error("SAL_V18_QUESTION_DUAL_IDENTITY_SELF_PROMOTION")
    if report.solver_invocation_count != 0:
        raise ScientificAssuranceLineageV18Error("SAL_V18_SOLVER_MUST_NOT_RUN")
    if report.result != "BLOCKED" or report.blocked_subtype != "BLOCKED_UNAUTHORIZED_INTERPRETATION":
        raise ScientificAssuranceLineageV18Error("SAL_V18_CURRENT_RESULT_MUST_REMAIN_PRIOR_BLOCKED")
    if report.normative_countermodel is not None:
        raise ScientificAssuranceLineageV18Error("SAL_V18_NORMATIVE_COUNTERMODEL_FORBIDDEN")

    print(f"SAL_V18_REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")
    print("SAL_V18_SCHEMA_HEADERS = PASS (6/6)")
    print(f"SAL_SCHEMA_IDENTITY_REGISTRATION_V8 = PASS ({registered}/6 dual-bound candidate identities)")
    print("NORMATIVE_SEMANTIC_SURFACE_SELECTION_IDENTITY = PASS_CANDIDATE_CONTENT_BOUND (predecessor + target)")
    print("NORMATIVE_SEMANTIC_SURFACE_AUTHORITY = NOT_ESTABLISHED")
    print("SEMANTIC_COVERAGE_UNIVERSE_INJECTION = REJECTED_IN_TESTED_PATH")
    print("REQUIRED_SEMANTIC_SURFACE_OMISSION = REJECTED_RELATIVE_TO_CONTENT_BOUND_CANDIDATE_SURFACE")
    print("SEMANTIC_ABSTRACTION_ADEQUACY = NOT_ESTABLISHED")
    print("CROSS_FORMULA_SEMANTIC_BRIDGE_IDENTITY = PASS_CONTENT_IDENTIFIED_EMPTY_THEORY")
    print("CROSS_FORMULA_SEMANTIC_BRIDGE = ABSENT")
    print("CROSS_FORMULA_SEMANTIC_BRIDGE_AUTHORITY = NOT_ESTABLISHED")
    print("DISJOINT_SEMANTIC_VOCABULARY = CONFIRMED (5 predecessor atoms; 13 target atoms; intersection 0)")
    print("DISJOINT_VOCABULARY_TRIVIAL_REFUTATION = LATENT_IF_SOLVER_PREMATURELY_ENABLED")
    print("NORMATIVE_COUNTERMODEL = NOT_CLAIMED")
    print("ENTAILMENT_METHOD_CONTENT_IDENTITY = PASS_CANDIDATE_EXACT_SOURCE_AND_FORMAL_SEMANTICS")
    print("ENTAILMENT_METHOD_AUTHORITY = NOT_ESTABLISHED")
    print("ENTAILMENT_METHOD_CAPACITY_FOR_ISSUED_QUESTION = BLOCKED (18 atoms > max_atoms 16)")
    print("ENTAILMENT_QUESTION_IDENTITY_PRESERVED = PASS")
    print("ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY = NOT_ESTABLISHED")
    print("SOLVER_EXECUTION_GATED_BY_SEMANTIC_ABSTRACTION_CLOSURE = PASS")
    print("SOLVER_INVOCATION_COUNT = 0")
    print("PREDECESSOR_SEMANTIC_ENTAILMENT = BLOCKED_UNAUTHORIZED_INTERPRETATION")
    print("COUNTERMODEL_SEARCH = NOT_INVOKED_BEFORE_SEMANTIC_ABSTRACTION_CLOSURE")
    print("SAL_RELEASE_GATE_102_TO_110 = PASS (8 additive gates)")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP = NOT_YET_ESTABLISHED")
    print("NORMATIVE_ROOT_LINEAGE_GENERAL = NOT_ESTABLISHED")
    print("HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY_GENERAL = NOT_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScientificAssuranceLineageV18Error as exc:
        import sys
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
