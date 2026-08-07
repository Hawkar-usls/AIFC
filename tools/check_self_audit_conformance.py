#!/usr/bin/env python3
"""AIFC Verifier A v0.4 environment self-audit repository checks."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import load_json_strict  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402

ACTIVE_WORKFLOW = ".github/workflows/verifier-self-audit-v03.yml"

REQUIRED = [
    "reference/verifier/requirements.txt",
    "reference/verifier/requirements.lock.txt",
    "reference/verifier/schema_runtime.py",
    "reference/verifier/protocol_semantics_v03.py",
    "reference/verifier/full_admission_v03.py",
    "reference/verifier/aifc_verify_v03.py",
    "reference/verifier/aifc_verify_v04.py",
    "reference/tests/test_schema_runtime.py",
    "reference/tests/test_protocol_semantics_v03.py",
    "reference/tests/test_ci_attestation_v04.py",
    "reference/tests/test_cli_exit_v04.py",
    "schemas/verifier-ci-attestation.schema.json",
    "schemas/verifier-ci-attestation-v2.schema.json",
    "schemas/execution-environment-manifest.schema.json",
    "schemas/ci-platform-receipt.schema.json",
    "schemas/cli-exit-taxonomy.schema.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.3-draft.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.4-draft.json",
    "conformance/CLI-EXIT-TAXONOMY-v1.json",
    "tools/build_execution_environment_manifest.py",
    "tools/build_verifier_ci_attestation_v04.py",
    "tools/verify_verifier_ci_attestation_v04.py",
    "tools/build_ci_platform_receipt.py",
    "tools/verify_ci_platform_receipt.py",
    ACTIVE_WORKFLOW,
]

NEW_V04_FROZEN_GATES = {
    "CI_REPORT_SEMANTIC_RECOMPUTE",
    "CI_PLATFORM_PROVENANCE_BINDING",
    "EXECUTION_ENVIRONMENT_BINDING",
    "SCHEMA_SOURCE_STRICTNESS",
    "CLI_ADMISSION_EXIT_SEMANTICS",
}

PINNED_ACTIONS = {
    "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def load(rel: str):
    try:
        return load_json_strict(ROOT / rel)
    except Exception as exc:
        fail(f"cannot strictly parse {rel}: {exc}")


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

    previous_gate = load("conformance/AIFC-RELEASE-GATE-v1.0.3-draft.json")
    current_gate = load("conformance/AIFC-RELEASE-GATE-v1.0.4-draft.json")
    previous_ids = required_gate_ids(previous_gate)
    current_ids = required_gate_ids(current_gate)
    if len(previous_ids) != len(set(previous_ids)) or len(current_ids) != len(set(current_ids)):
        fail("duplicate frozen gate id")
    expected_current = set(previous_ids) | NEW_V04_FROZEN_GATES
    if set(current_ids) != expected_current:
        fail(
            f"v0.4 frozen gate drift missing={sorted(expected_current-set(current_ids))} "
            f"extra={sorted(set(current_ids)-expected_current)}"
        )
    if len(previous_ids) != 44:
        fail(f"v0.3 predecessor gate count must be 44, got {len(previous_ids)}")
    if len(current_ids) != 49:
        fail(f"v0.4 frozen gate count must be 49, got {len(current_ids)}")
    if current_gate.get("status") != "DRAFT_NOT_SATISFIED":
        fail("v0.4 frozen gate must remain DRAFT_NOT_SATISFIED")
    if current_gate.get("supersedes_for_draft_evaluation") != "conformance/AIFC-RELEASE-GATE-v1.0.3-draft.json":
        fail("v0.4 frozen gate supersession chain invalid")
    print("ENVIRONMENT_SELF_AUDITING_FROZEN_RELEASE_GATE = BLOCKED_AS_EXPECTED (49 unmet evidence classes declared)")

    taxonomy = load("conformance/CLI-EXIT-TAXONOMY-v1.json")
    validate_protocol_object(taxonomy, "AIFC/cli-exit-taxonomy/v1")
    expected_codes = {
        "INVALIDATED_EVIDENCE": 2,
        "NOT_ADMITTED": 3,
        "STRUCTURAL_MATCH_ONLY": 4,
        "FORWARD_NULL_CONSISTENT_MISS": 0,
        "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE": 0,
    }
    if taxonomy.get("terminal_grade_exit_codes") != expected_codes:
        fail("CLI exit taxonomy mapping drift")
    if "MUST_PARSE_AND_VALIDATE_THE_VERIFIER_RESULT_JSON" not in taxonomy.get("external_automation_rule", ""):
        fail("CLI external automation rule missing")
    print("CLI_ADMISSION_EXIT_SEMANTICS = PASS")

    schema_runtime = (ROOT / "reference/verifier/schema_runtime.py").read_text(encoding="utf-8")
    for token in ("SCHEMA_DUPLICATE_KEY", "AMBIGUOUS_SCHEMA_SOURCE", "load_schema_source_strict"):
        if token not in schema_runtime:
            fail(f"schema-source strictness path missing: {token}")
    print("SCHEMA_SOURCE_STRICTNESS = IMPLEMENTED_CANDIDATE")

    lock_lines = [
        line.strip() for line in (ROOT / "reference/verifier/requirements.lock.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(lock_lines) != 6:
        fail(f"dependency lock must contain six exact runtime distributions, got {len(lock_lines)}")
    for line in lock_lines:
        if not re.match(r"^[A-Za-z0-9_.-]+==[^ ]+ --hash=sha256:[0-9a-f]{64}$", line):
            fail(f"dependency lock row is not exact+hashed: {line}")
    print("VERIFIER_DEPENDENCY_GRAPH_HASH_LOCK = PASS (6/6)")

    workflow = (ROOT / ACTIVE_WORKFLOW).read_text(encoding="utf-8")
    if "AIFC Verifier Environment Self-Audit v0.4" not in workflow:
        fail("active historical workflow locator does not identify v0.4 semantics")
    if "@v" in workflow:
        fail("mutable GitHub Action major tag found in active v0.4 verifier workflow")
    for repo, sha in PINNED_ACTIONS.items():
        if f"uses: {repo}@{sha}" not in workflow:
            fail(f"pinned action missing from v0.4 workflow: {repo}@{sha}")
    if "--require-hashes" not in workflow or "--only-binary=:all:" not in workflow:
        fail("v0.4 workflow does not enforce hashed binary dependency lock")
    if "--workflow-path .github/workflows/verifier-self-audit-v03.yml" not in workflow:
        fail("v0.4 attestation is not bound to the active workflow locator")
    print("EXECUTION_ENVIRONMENT_WORKFLOW_PINS = PASS")

    v2_schema = load("schemas/verifier-ci-attestation-v2.schema.json")
    if v2_schema.get("properties", {}).get("schema", {}).get("const") != "AIFC/verifier-ci-attestation/v2":
        fail("CI attestation v2 schema identity drift")
    workflow_const = v2_schema.get("properties", {}).get("workflow", {}).get("properties", {}).get("path", {}).get("const")
    if workflow_const != ACTIVE_WORKFLOW:
        fail(f"CI attestation v2 workflow path drift: {workflow_const!r}")
    env_schema = load("schemas/execution-environment-manifest.schema.json")
    if env_schema.get("properties", {}).get("schema", {}).get("const") != "AIFC/execution-environment-manifest/v1":
        fail("execution environment schema identity drift")
    platform_schema = load("schemas/ci-platform-receipt.schema.json")
    if platform_schema.get("properties", {}).get("schema", {}).get("const") != "AIFC/ci-platform-receipt/v1":
        fail("CI platform receipt schema identity drift")
    print("CI_ATTESTATION_V2_AND_PLATFORM_SCHEMAS = PASS")

    verifier_v04 = (ROOT / "tools/verify_verifier_ci_attestation_v04.py").read_text(encoding="utf-8")
    for token in (
        "CI_EXIT_CODE_REBINDING",
        "CI_TEST_COUNT_REBINDING",
        "SAME_TREE_DIFFERENT_EXECUTION_ENVIRONMENT",
        "DETACHED_CI_PASS_ATTESTATION",
    ):
        if token not in verifier_v04:
            fail(f"v0.4 CI verifier attack path missing: {token}")
    platform_verifier = (ROOT / "tools/verify_ci_platform_receipt.py").read_text(encoding="utf-8")
    for token in (
        "CI_PLATFORM_JOB_NOT_SUCCESS",
        "CI_PLATFORM_ARTIFACT_DIGEST_REBINDING",
        "CI_PLATFORM_ARTIFACT_ATTESTATION_RAW_REBINDING",
    ):
        if token not in platform_verifier:
            fail(f"platform receipt attack path missing: {token}")
    print("CI_REPORT_SEMANTIC_RECOMPUTE = IMPLEMENTED_CANDIDATE")
    print("CI_PLATFORM_PROVENANCE_BINDING = IMPLEMENTED_CANDIDATE_POST_UPLOAD")
    print("EXECUTION_ENVIRONMENT_BINDING = IMPLEMENTED_CANDIDATE")

    old_status = load("conformance/VERIFIER-A-REPLAY-v0.2.json")
    if old_status.get("status") != "HISTORICAL_CI_RECORD_NOT_CURRENT_TREE_ATTESTATION":
        fail("historical unbound v0.2 CI record still self-asserts current-tree PASS")
    if old_status.get("release_gate_effect", {}).get("VERIFIER_A_REPLAY_V0_2_CURRENT_TREE") != "NOT_ESTABLISHED":
        fail("v0.2 status must not establish current-tree replay PASS")
    print("DETACHED_CI_PASS_ATTESTATION = FAIL_CLOSED")

    semantics = (ROOT / "reference/verifier/protocol_semantics_v03.py").read_text(encoding="utf-8")
    for token in (
        "CREATED_OUTSIDE_FROZEN_SCHEDULE_OR_TRIGGER_NOT_REPLAYABLE",
        "IMPOSSIBLE_TERMINAL_SUBTYPE",
        "PREALLOCATED_CREATED_SLOT_SET_MISMATCH",
    ):
        if token not in semantics:
            fail(f"protocol semantic replay path missing: {token}")

    admission = (ROOT / "reference/verifier/full_admission_v03.py").read_text(encoding="utf-8")
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
