#!/usr/bin/env python3
"""AIFC Verifier A v0.3 self-audit repository checks."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from schema_runtime import validate_protocol_object  # noqa: E402

REQUIRED = [
    "reference/verifier/requirements.txt",
    "reference/verifier/schema_runtime.py",
    "reference/verifier/protocol_semantics_v03.py",
    "reference/verifier/full_admission_v03.py",
    "reference/verifier/aifc_verify_v03.py",
    "reference/tests/test_schema_runtime.py",
    "reference/tests/test_protocol_semantics_v03.py",
    "schemas/verifier-ci-attestation.schema.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.3-draft.json",
    "tools/build_verifier_ci_attestation.py",
    "tools/verify_verifier_ci_attestation.py",
]

NEW_V03_FROZEN_GATES = {
    "RUNTIME_JSON_SCHEMA_ADMISSION",
    "CI_PASS_PROVENANCE_BINDING",
    "TRIAL_CREATION_POLICY_REPLAY",
    "TERMINAL_SUBTYPE_SEMANTICS",
    "DECLARED_TRIAL_LEDGER_COVERAGE",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def load(rel: str):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse {rel}: {exc}")


def required_gate_ids(obj: dict) -> list[str]:
    return [row.get("id") for row in obj.get("required_checks", []) if row.get("required") is True]


def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    if missing:
        fail("missing self-audit files: " + ", ".join(missing))
    print(f"SELF_AUDIT_REQUIRED_FILES = PASS ({len(REQUIRED)}/{len(REQUIRED)})")

    replay = load("schemas/replay-package.schema.json")
    if "experiment_plan_quorum_certificate_hash" not in replay.get("required", []):
        fail("replay package drift: experiment_plan_quorum_certificate_hash not required")
    if "experiment_plan_quorum_certificate_hash" not in replay.get("properties", {}):
        fail("replay package drift: experiment_plan_quorum_certificate_hash property missing")
    print("VISIBLE_SCHEMA_CHECKER_PAIR = CONSISTENT")

    trial_policy = load("schemas/trial-creation-policy.schema.json")
    required = set(trial_policy.get("required", []))
    for field in ("declared_trial_count", "schedule_or_trigger_spec_hash"):
        if field not in required:
            fail(f"trial creation policy must require explicit {field}")
    if "allOf" not in trial_policy:
        fail("trial creation method-specific schema conditions missing")

    state = load("conformance/state-machine-v1.json")
    table = state.get("terminal_subtypes_by_state")
    if not isinstance(table, dict):
        fail("state machine missing terminal_subtypes_by_state")
    if "COMPLETED_HIT" in table.get("CREATED", []) or "COMPLETED_MISS" in table.get("CREATED", []):
        fail("CREATED must not directly complete as hit/miss")
    if "ABORTED_POST_TARGET_PRE_VERIFY" in table.get("CREATED", []):
        fail("CREATED must not use post-target abort subtype")
    if set(("COMPLETED_HIT", "COMPLETED_MISS")) - set(table.get("VERIFIED", [])):
        fail("VERIFIED must permit completed hit/miss terminal subtypes")
    print("TERMINAL_SUBTYPE_MACHINE_TABLE = PASS")

    previous_gate = load("conformance/AIFC-RELEASE-GATE-v1.0.2-draft.json")
    current_gate = load("conformance/AIFC-RELEASE-GATE-v1.0.3-draft.json")
    previous_ids = required_gate_ids(previous_gate)
    current_ids = required_gate_ids(current_gate)
    if len(previous_ids) != len(set(previous_ids)) or len(current_ids) != len(set(current_ids)):
        fail("duplicate frozen gate id")
    expected_current = set(previous_ids) | NEW_V03_FROZEN_GATES
    if set(current_ids) != expected_current:
        fail(
            f"v0.3 frozen gate drift missing={sorted(expected_current-set(current_ids))} "
            f"extra={sorted(set(current_ids)-expected_current)}"
        )
    if len(current_ids) != 44:
        fail(f"v0.3 frozen gate count must be 44, got {len(current_ids)}")
    if current_gate.get("status") != "DRAFT_NOT_SATISFIED":
        fail("v0.3 frozen gate must remain DRAFT_NOT_SATISFIED")
    if current_gate.get("supersedes_for_draft_evaluation") != "conformance/AIFC-RELEASE-GATE-v1.0.2-draft.json":
        fail("v0.3 frozen gate supersession chain invalid")
    print("SELF_AUDITING_FROZEN_RELEASE_GATE = BLOCKED_AS_EXPECTED (44 unmet evidence classes declared)")

    ci_schema = load("schemas/verifier-ci-attestation.schema.json")
    validate_protocol_object({
        "schema": "AIFC/verifier-ci-attestation/v1",
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.3.0-self-audit",
        "repository": "Hawkar-usls/AIFC",
        "tested_source_commit_sha": "0" * 40,
        "tested_tree_sha": "1" * 40,
        "workflow": {
            "path": ".github/workflows/verifier-self-audit-v03.yml",
            "raw_sha256": "2" * 64,
            "run_id": 1,
            "run_attempt": 1,
            "job_id": 1,
            "job_name": "Verifier A self-audit",
            "event_name": "push",
            "runner_os": "Linux",
            "python_version": "3.12.0"
        },
        "bound_source_sets": {
            "schemas": {"manifest_sha256": "3" * 64, "file_count": 1},
            "verifier_source": {"manifest_sha256": "4" * 64, "file_count": 1},
            "test_corpus": {"manifest_sha256": "5" * 64, "file_count": 1},
            "checkers": {"manifest_sha256": "6" * 64, "file_count": 1}
        },
        "reports": {
            "base_conformance": {"path": "base.txt", "raw_sha256": "7" * 64, "aifc_raw_evidence_hash": "8" * 64, "exit_code": 0},
            "preregistration_conformance": {"path": "prereg.txt", "raw_sha256": "d" * 64, "aifc_raw_evidence_hash": "e" * 64, "exit_code": 0},
            "self_audit_conformance": {"path": "self.txt", "raw_sha256": "9" * 64, "aifc_raw_evidence_hash": "a" * 64, "exit_code": 0},
            "unittest": {"path": "unit.txt", "raw_sha256": "b" * 64, "aifc_raw_evidence_hash": "c" * 64, "exit_code": 0, "test_count": 1}
        },
        "overall_status": "PASS",
        "claim_ceiling": {"implementation_a_pass": False, "aifc_v1_frozen": False, "physical_retrocausality": "NOT_OBSERVED"},
        "generated_at": "2026-08-07T00:00:00Z"
    }, "AIFC/verifier-ci-attestation/v1")
    if ci_schema.get("properties", {}).get("tested_source_commit_sha", {}).get("pattern") != "^[0-9a-f]{40}$":
        fail("CI attestation source commit binding drift")
    print("CI_ATTESTATION_SCHEMA = PASS")

    old_status = load("conformance/VERIFIER-A-REPLAY-v0.2.json")
    if old_status.get("status") != "HISTORICAL_CI_RECORD_NOT_CURRENT_TREE_ATTESTATION":
        fail("historical unbound v0.2 CI record still self-asserts current-tree PASS")
    if old_status.get("release_gate_effect", {}).get("VERIFIER_A_REPLAY_V0_2_CURRENT_TREE") != "NOT_ESTABLISHED":
        fail("v0.2 status must not establish current-tree replay PASS")
    print("DETACHED_CI_PASS_ATTESTATION = FAIL_CLOSED")

    semantics = (ROOT / "reference" / "verifier" / "protocol_semantics_v03.py").read_text(encoding="utf-8")
    for token in (
        "CREATED_OUTSIDE_FROZEN_SCHEDULE_OR_TRIGGER_NOT_REPLAYABLE",
        "IMPOSSIBLE_TERMINAL_SUBTYPE",
        "PREALLOCATED_CREATED_SLOT_SET_MISMATCH",
    ):
        if token not in semantics:
            fail(f"protocol semantic replay path missing: {token}")

    admission = (ROOT / "reference" / "verifier" / "full_admission_v03.py").read_text(encoding="utf-8")
    for token in (
        "RUNTIME_JSON_SCHEMA_ADMISSION",
        "DECLARED_TRIAL_LEDGER_COVERAGE",
        "COMPLETE_TRIAL_PUBLICATION",
    ):
        if token not in admission:
            fail(f"v0.3 admission gate missing: {token}")

    print("FULL_RUNTIME_JSON_SCHEMA_ADMISSION = IMPLEMENTED_CANDIDATE")
    print("TRIAL_CREATION_POLICY_REPLAY = IMPLEMENTED_PREALLOCATED_ONLY")
    print("IMPOSSIBLE_TERMINAL_SUBTYPE = REJECTED")
    print("CI_PASS_PROVENANCE_BINDING = IMPLEMENTED_CANDIDATE")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
