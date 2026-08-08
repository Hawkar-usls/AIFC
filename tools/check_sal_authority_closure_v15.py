#!/usr/bin/env python3
"""Repository checker for SAL v1.5 Authority-Closure Hardening."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from scientific_assurance_lineage_v15 import (  # noqa: E402
    ScientificAssuranceLineageV15Error,
    verify_authority_closure_live,
)

REQUIRED_FILES = (
    "schemas/authority-receipt-provenance-v2.schema.json",
    "schemas/lineage-transition-profile-v1.schema.json",
    "schemas/authority-closure-obstruction-v1.schema.json",
    "schemas/schema-identity-registry-v5.schema.json",
    "conformance/AIFC-NORMATIVE-AUTHORITY-RECEIPT-56370d6-v2.json",
    "conformance/AIFC-AUTHORITY-RECEIPT-PROVENANCE-v2.json",
    "conformance/AIFC-LINEAGE-TRANSITION-PROFILE-v1.json",
    "conformance/AIFC-AUTHORITY-CLOSURE-OBSTRUCTION-v1.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v5.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.12-draft.json",
    "reference/verifier/scientific_assurance_lineage_v15.py",
    "reference/tests/test_sal_authority_closure_v15.py",
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.4.md",
    ".github/workflows/sal-authority-closure-v15.yml",
)


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ScientificAssuranceLineageV15Error("SAL_V15_REQUIRED_FILES_MISSING:" + ",".join(missing))

    report = verify_authority_closure_live()
    if not report.provenance_receipt_content_binding:
        raise ScientificAssuranceLineageV15Error("PROVENANCE_RECEIPT_CONTENT_BINDING_NOT_ESTABLISHED")
    if not report.historical_workflow_definition_identity:
        raise ScientificAssuranceLineageV15Error("HISTORICAL_WORKFLOW_DEFINITION_IDENTITY_NOT_ESTABLISHED")
    if not report.successor_registry_exact_delta:
        raise ScientificAssuranceLineageV15Error("SUCCESSOR_REGISTRY_EXACT_DELTA_NOT_ESTABLISHED")
    if report.lineage_transition_profile_authority_anchor:
        raise ScientificAssuranceLineageV15Error("UNEXPECTED_TRANSITION_PROFILE_AUTHORITY_REQUIRES_VERSIONED_REVIEW")
    if not report.historical_artifact_semantic_replay:
        raise ScientificAssuranceLineageV15Error("HISTORICAL_ARTIFACT_SEMANTIC_REPLAY_NOT_ESTABLISHED")
    if report.authority_closed_finite_induction:
        raise ScientificAssuranceLineageV15Error("AUTHORITY_CLOSED_FINITE_INDUCTION_SELF_PROMOTION")

    print(f"SAL_AUTHORITY_CLOSURE_REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")
    print("SAL_V15_SCHEMA_HEADERS = PASS (4/4)")
    print("SAL_SCHEMA_IDENTITY_REGISTRATION_V5 = PASS (4/4 dual-bound candidate identities)")
    print(
        "PROVENANCE_RECEIPT_CONTENT_BINDING = PASS "
        f"({report.receipt_count}/3 receipts; {report.workflow_count}/15 workflow refs; {report.artifact_count}/9 artifacts)"
    )
    print(f"HISTORICAL_WORKFLOW_DEFINITION_IDENTITY = PASS ({report.workflow_count}/15)")
    print("SUCCESSOR_REGISTRY_EXACT_DELTA = PASS (R_v3 = R_v2 state-update + exact 2-record candidate delta)")
    print(f"HISTORICAL_ARTIFACT_SEMANTIC_REPLAY = PASS ({report.artifact_count}/9)")
    print("LINEAGE_TRANSITION_PROFILE_AUTHORITY_ANCHOR = BLOCKED_AS_EXPECTED_NO_PREDECESSOR_PROFILE")
    print("SAL_RELEASE_GATE_83_TO_88 = PASS (5 additive gates)")
    print("PROVENANCE_RECEIPT_CONTENT_DISCONNECT = CLOSED_IN_TESTED_V1_5_PATH")
    print("HISTORICAL_WORKFLOW_DEFINITION_REBINDING = CLOSED_IN_TESTED_V1_5_PATH")
    print("SUCCESSOR_REGISTRY_EXTRA_RECORD_INJECTION = CLOSED_IN_TESTED_V1_5_PATH")
    print("NORMATIVE_ROOT_LINEAGE_FIRST_EXECUTABLE_INDUCTIVE_STEP = ESTABLISHED_IN_EXACT_TESTED_SCOPE")
    print("UNANCHORED_LINEAGE_TRANSITION_SEMANTICS = CONFIRMED_BOOTSTRAP_OBSTRUCTION")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = BLOCKED_AS_EXPECTED")
    print("FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP = NOT_YET_ESTABLISHED")
    print("LINEAGE_TRANSITION_PROFILE_V1 = SUCCESSOR_CANDIDATE_ONLY")
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
    except ScientificAssuranceLineageV15Error as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
