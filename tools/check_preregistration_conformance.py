#!/usr/bin/env python3
"""Supplemental AIFC v0.2 preregistration/replay conformance checks.

This checker is intentionally additive to tools/check_repo_conformance.py while
PR #5 is still a draft. It verifies the newest experiment-plan preregistration,
entropy-policy and content-addressed replay contracts without rewriting a moving
base checker snapshot.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NEW_REQUIRED_FILES = [
    "schemas/entropy-policy.schema.json",
    "schemas/experiment-plan-receipt.schema.json",
    "schemas/experiment-plan-quorum.schema.json",
    "schemas/experiment-plan.schema.json",
    "schemas/trial-ledger-event.schema.json",
    "schemas/replay-package.schema.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.2-draft.json",
    "reference/verifier/admission.py",
    "reference/verifier/canonical_v02.py",
    "reference/verifier/resolver_v02.py",
    "reference/verifier/preregistration_v02.py",
    "reference/verifier/full_admission_v02.py",
    "reference/verifier/aifc_verify_v02.py",
    "reference/tests/test_admission.py",
    "reference/tests/test_preregistration_v02.py",
]

EXPECTED_GATE_IDS = {
    "SPEC_SCHEMA_VALID",
    "STATE_MACHINE_VALID",
    "EXPERIMENT_PLAN_VALID",
    "EXPERIMENT_PLAN_CERTIFIED_BEFORE_CREATED",
    "TRIAL_CREATION_POLICY_VALID",
    "TRIAL_LEDGER_CONTINUITY",
    "LEDGER_GENESIS_SENTINEL_VALID",
    "CANDIDATE_SET_RECOMPUTED",
    "CANDIDATE_GENERATION_PROVENANCE_VALID",
    "POST_CREATED_OPERATOR_CHOICE_EXCLUDED",
    "PRE_TARGET_CONDITIONING_VIEW_VALID",
    "TARGET_SELECTOR_PROFILE_VALID",
    "TARGET_DERIVATION_PROFILE_VALID",
    "TARGET_DERIVATION_BYTE_REPLAY",
    "ENTROPY_POLICY_VALID",
    "ENTROPY_PROFILE_VALID",
    "CANONICAL_RATIONAL_VALID",
    "EVIDENCE_RESOLVER_PASS",
    "CAUSAL_MODEL_VALID",
    "CAUSAL_EVIDENCE_RESOLUTION",
    "WITNESS_LIFECYCLE_VALID",
    "WITNESS_FAILURE_DOMAIN_INDEPENDENCE",
    "REGISTRY_TRANSITION_VALID",
    "STATISTICAL_PLAN_VALID",
    "STATISTICAL_ENGINE_REPLAY",
    "PUBLICATION_MANIFEST_VALID",
    "COMPLETE_TRIAL_PUBLICATION",
    "CITATION_ZENODO_METADATA_SYNC",
    "ALL_HONEST_VECTORS_PASS",
    "ALL_ATTACK_VECTORS_EXPECTED_REJECTION",
    "IMPLEMENTATION_A_PASS",
    "IMPLEMENTATION_B_PASS",
    "BYTE_IDENTICAL_CANONICALIZATION",
    "FAIL_OPEN_ZERO",
    "RELEASE_ASSET_CHOREOGRAPHY_VALID",
    "RELEASE_MANIFEST_PROOF_CARRYING",
    "RELEASE_MANIFEST_EVIDENCE_RESOLUTION",
    "TARGET_SOURCE_CRYPTOGRAPHIC_PROOF",
    "EXTERNAL_BENCH_EVIDENCE_ROOTED_OUTSIDE_GENESIS",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(rel: str):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse {rel}: {exc}")


def require_required(obj: dict, fields: tuple[str, ...], label: str) -> None:
    required = set(obj.get("required", []))
    missing = [f for f in fields if f not in required]
    if missing:
        fail(f"{label}: required fields missing: {missing}")


def main() -> int:
    missing = [p for p in NEW_REQUIRED_FILES if not (ROOT / p).is_file()]
    if missing:
        fail("new preregistration/replay files missing: " + ", ".join(missing))
    print(f"PREREG_REQUIRED_FILES = PASS ({len(NEW_REQUIRED_FILES)}/{len(NEW_REQUIRED_FILES)})")

    for rel in (
        "schemas/entropy-policy.schema.json",
        "schemas/experiment-plan-receipt.schema.json",
        "schemas/experiment-plan-quorum.schema.json",
    ):
        obj = load(rel)
        if obj.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            fail(f"{rel}: wrong schema dialect")
        if obj.get("type") != "object" or obj.get("additionalProperties") is not False:
            fail(f"{rel}: must be closed top-level object")
    print("PREREG_NEW_SCHEMA_HEADERS = PASS (3/3)")

    plan = load("schemas/experiment-plan.schema.json")
    require_required(plan, ("entropy_policy_hash", "initial_witness_registry_hash", "frozen_before_first_created"), "experiment plan")

    entropy_policy = load("schemas/entropy-policy.schema.json")
    require_required(entropy_policy, (
        "source_id",
        "source_protocol_version",
        "allowed_derivation_methods",
        "required_external_evidence_types",
        "post_target_method_selection_forbidden",
        "frozen_before_first_created",
    ), "entropy policy")
    if entropy_policy["properties"]["post_target_method_selection_forbidden"].get("const") is not True:
        fail("entropy policy must forbid post-target method selection")

    plan_receipt = load("schemas/experiment-plan-receipt.schema.json")
    if "trial_index" in plan_receipt.get("properties", {}):
        fail("experiment-plan receipt must be experiment-scoped, not trial-scoped")
    if plan_receipt["properties"]["logical_position"].get("const") != "EXPERIMENT_PLAN_FROZEN":
        fail("experiment-plan receipt logical position drift")

    plan_quorum = load("schemas/experiment-plan-quorum.schema.json")
    if "trial_index" in plan_quorum.get("properties", {}):
        fail("experiment-plan quorum must be experiment-scoped, not trial-scoped")
    if plan_quorum["properties"]["receipts"].get("items", {}).get("$ref") != "experiment-plan-receipt.schema.json":
        fail("experiment-plan quorum must type receipts via experiment-plan-receipt")

    ledger = load("schemas/trial-ledger-event.schema.json")
    require_required(ledger, ("prerequisite_certificate_hash",), "trial ledger event")
    ledger_text = (ROOT / "schemas/trial-ledger-event.schema.json").read_text(encoding="utf-8")
    if "For CREATED" not in ledger_text or "experiment-plan" not in ledger_text:
        fail("CREATED prerequisite semantics missing from ledger schema description")

    replay = load("schemas/replay-package.schema.json")
    require_required(replay, ("experiment_plan_quorum_certificate_hash",), "replay package")

    gate = load("conformance/AIFC-RELEASE-GATE-v1.0.2-draft.json")
    ids = [row.get("id") for row in gate.get("required_checks", []) if row.get("required") is True]
    if len(ids) != len(set(ids)):
        fail("duplicate release gate id")
    if set(ids) != EXPECTED_GATE_IDS:
        fail(f"superseding gate drift missing={sorted(EXPECTED_GATE_IDS-set(ids))} extra={sorted(set(ids)-EXPECTED_GATE_IDS)}")
    if gate.get("status") != "DRAFT_NOT_SATISFIED":
        fail("superseding draft gate must remain DRAFT_NOT_SATISFIED")
    print(f"PREREG_FROZEN_RELEASE_GATE = BLOCKED_AS_EXPECTED ({len(ids)} unmet evidence classes declared)")

    canonical_v02 = (ROOT / "reference/verifier/canonical_v02.py").read_text(encoding="utf-8")
    for token in ("AIFC:EXPERIMENT_PLAN_RECEIPT:v1", "AIFC:EXPERIMENT_PLAN_QUORUM:v1"):
        if token not in canonical_v02:
            fail(f"canonical_v02 missing domain separator: {token}")

    prereg = (ROOT / "reference/verifier/preregistration_v02.py").read_text(encoding="utf-8")
    for token in (
        "EXPERIMENT_PLAN_NOT_CERTIFIED_BEFORE_CREATED",
        "PLAN_QUORUM_FAULT_MODEL_REBINDING",
        "PLAN_QUORUM_SAME_FAILURE_DOMAIN_SYBIL",
        "PLAN_RECEIPT_EXPERIMENT_REBINDING",
    ):
        if token not in prereg:
            fail(f"preregistration verifier missing fail-closed path: {token}")

    full = (ROOT / "reference/verifier/full_admission_v02.py").read_text(encoding="utf-8")
    if "verify_plan_preregistration" not in full or "verify_after_preregistration" not in full:
        fail("top-level v0.2 admission composition missing")

    print("EXPERIMENT_PLAN_PREREGISTRATION_CONTRACT = PASS")
    print("ENTROPY_POLICY_CONTRACT = PASS")
    print("AIFC_V1_FROZEN = FALSE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
