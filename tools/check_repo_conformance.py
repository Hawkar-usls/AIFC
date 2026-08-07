#!/usr/bin/env python3
"""AIFC repository-level draft conformance checks.

This is not the scientific verifier. It checks that the repository contains the
machine-readable protocol objects required for the draft and that metadata does
not silently diverge before release.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "CITATION.cff",
    ".zenodo.json",
    "spec/AIFC-SPEC-v1.0-draft.md",
    "spec/STATE_MACHINE.md",
    "spec/CANONICALIZATION.md",
    "spec/WITNESS_LIFECYCLE.md",
    "spec/TIME_AND_ORDERING.md",
    "docs/TRIAL_LEDGER.md",
    "docs/ENTROPY_EVIDENCE.md",
    "schemas/trial-ledger-event.schema.json",
    "schemas/entropy-profile.schema.json",
    "schemas/causal-model.schema.json",
    "schemas/witness-registry.schema.json",
    "conformance/state-machine-v1.json",
    "conformance/AIFC-RELEASE-GATE-v1.json",
]

SCHEMA_FILES = [
    "schemas/trial-ledger-event.schema.json",
    "schemas/entropy-profile.schema.json",
    "schemas/causal-model.schema.json",
    "schemas/witness-registry.schema.json",
]

EXPECTED_SCHEMA_IDS = {
    "schemas/trial-ledger-event.schema.json": "https://github.com/Hawkar-usls/AIFC/schemas/trial-ledger-event.schema.json",
    "schemas/entropy-profile.schema.json": "https://github.com/Hawkar-usls/AIFC/schemas/entropy-profile.schema.json",
    "schemas/causal-model.schema.json": "https://github.com/Hawkar-usls/AIFC/schemas/causal-model.schema.json",
    "schemas/witness-registry.schema.json": "https://github.com/Hawkar-usls/AIFC/schemas/witness-registry.schema.json",
}


def die(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def load_json(rel: str):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"cannot parse {rel}: {exc}")


def cff_scalar(text: str, key: str) -> str:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*(?:\"([^\"]*)\"|'([^']*)'|([^\n#]+))\s*$", text)
    if not m:
        die(f"missing CFF scalar {key}")
    return next(x for x in m.groups() if x is not None).strip()


def check_required_files() -> None:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).is_file()]
    if missing:
        die("missing required files: " + ", ".join(missing))
    print(f"REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")


def check_schema_headers() -> None:
    for rel in SCHEMA_FILES:
        obj = load_json(rel)
        if obj.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            die(f"{rel}: wrong JSON Schema dialect")
        if obj.get("$id") != EXPECTED_SCHEMA_IDS[rel]:
            die(f"{rel}: unexpected $id")
        if obj.get("type") != "object" or obj.get("additionalProperties") is not False:
            die(f"{rel}: hash-critical top-level schema must be closed object")
    print(f"SCHEMA_HEADERS = PASS ({len(SCHEMA_FILES)}/{len(SCHEMA_FILES)})")


def check_state_machine() -> None:
    sm = load_json("conformance/state-machine-v1.json")
    if sm.get("schema") != "AIFC/state-machine/v1":
        die("state machine schema mismatch")
    normal = [tuple(x) for x in sm.get("normal_transitions", [])]
    expected = [
        (None, "CREATED"),
        ("CREATED", "PRE_RETURN_FROZEN"),
        ("PRE_RETURN_FROZEN", "QUORUM_CERTIFIED"),
        ("QUORUM_CERTIFIED", "TARGET_ARMED"),
        ("TARGET_ARMED", "TARGET_OBSERVED"),
        ("TARGET_OBSERVED", "VERIFIED"),
        ("VERIFIED", "TERMINAL"),
    ]
    if normal != expected:
        die("normal state transition chain drift")
    if not sm.get("forbidden", {}).get("silent_trial_deletion"):
        die("silent trial deletion must be forbidden")
    if not sm.get("forbidden", {}).get("candidate_before_created_certified"):
        die("candidate-before-created must be forbidden")
    print("STATE_MACHINE = PASS")


def check_release_gate() -> None:
    gate = load_json("conformance/AIFC-RELEASE-GATE-v1.json")
    ids = [x.get("id") for x in gate.get("required_checks", []) if x.get("required") is True]
    needed = {
        "SPEC_SCHEMA_VALID",
        "STATE_MACHINE_VALID",
        "TRIAL_LEDGER_CONTINUITY",
        "ENTROPY_PROFILE_VALID",
        "CAUSAL_MODEL_VALID",
        "WITNESS_LIFECYCLE_VALID",
        "CITATION_ZENODO_METADATA_SYNC",
        "ALL_HONEST_VECTORS_PASS",
        "ALL_ATTACK_VECTORS_EXPECTED_REJECTION",
        "IMPLEMENTATION_A_PASS",
        "IMPLEMENTATION_B_PASS",
        "BYTE_IDENTICAL_CANONICALIZATION",
        "FAIL_OPEN_ZERO",
        "COMPLETE_TRIAL_PUBLICATION",
        "EXTERNAL_BENCH_EVIDENCE_ROOTED_OUTSIDE_GENESIS",
    }
    if set(ids) != needed:
        die("release gate required-check set drift")
    if gate.get("status") != "DRAFT_NOT_SATISFIED":
        die("draft repository must not self-assert frozen conformance")
    print(f"FROZEN_RELEASE_GATE = BLOCKED_AS_EXPECTED ({len(ids)} unmet evidence classes declared)")


def check_metadata_sync() -> None:
    z = load_json(".zenodo.json")
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    cff_title = cff_scalar(cff, "title")
    cff_version = cff_scalar(cff, "version")
    cff_license = cff_scalar(cff, "license")
    if z.get("title") != cff_title:
        die("CITATION.cff and .zenodo.json title mismatch")
    if str(z.get("version")) != cff_version:
        die("CITATION.cff and .zenodo.json version mismatch")
    if z.get("license") != cff_license:
        die("CITATION.cff and .zenodo.json license mismatch")
    creators = z.get("creators") or []
    if not creators or creators[0].get("name") != "Agapov, Alexander":
        die("unexpected Zenodo creator identity")
    print("CITATION_ZENODO_METADATA_SYNC = PASS")


def main() -> int:
    check_required_files()
    check_schema_headers()
    check_state_machine()
    check_release_gate()
    check_metadata_sync()
    print("DRAFT_REPOSITORY_CONFORMANCE = PASS")
    print("AIFC_V1_FROZEN = FALSE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
