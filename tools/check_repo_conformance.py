#!/usr/bin/env python3
"""AIFC repository-level draft conformance checks.

This is not the scientific verifier. It checks that the repository contains the
machine-readable protocol objects required for the draft and that key hardening
contracts cannot silently drift before release.
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
    "docs/CAUSAL_MODEL.md",
    "schemas/hard-witness.schema.json",
    "schemas/pre-return-certificate.schema.json",
    "schemas/trial-ledger-event.schema.json",
    "schemas/candidate-generation-profile.schema.json",
    "schemas/entropy-profile.schema.json",
    "schemas/target-derivation-profile.schema.json",
    "schemas/causal-model.schema.json",
    "schemas/witness-registry.schema.json",
    "schemas/witness-receipt.schema.json",
    "schemas/quorum-certificate.schema.json",
    "schemas/registry-transition-certificate.schema.json",
    "schemas/target-evidence.schema.json",
    "schemas/evidence-bundle.schema.json",
    "schemas/verifier-result.schema.json",
    "schemas/release-manifest.schema.json",
    "conformance/state-machine-v1.json",
    "conformance/AIFC-RELEASE-GATE-v1.json",
]

SCHEMA_FILES = [p for p in REQUIRED_FILES if p.startswith("schemas/")]
EXPECTED_SCHEMA_IDS = {rel: f"https://github.com/Hawkar-usls/AIFC/{rel}" for rel in SCHEMA_FILES}


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
            die(f"{rel}: hash-critical top-level schema must be a closed object")
    print(f"SCHEMA_HEADERS = PASS ({len(SCHEMA_FILES)}/{len(SCHEMA_FILES)})")


def check_hardening_contracts() -> None:
    entropy = load_json("schemas/entropy-profile.schema.json")
    rat = entropy["properties"]["point_probability_upper_bound"]["properties"]
    if rat["numerator_dec"].get("pattern") != r"^(0|[1-9][0-9]*)$":
        die("canonical rational numerator grammar drift")
    if rat["denominator_dec"].get("pattern") != r"^[1-9][0-9]*$":
        die("canonical rational denominator grammar drift")
    if "target_derivation_profile_hash" not in entropy.get("required", []):
        die("entropy profile must bind target derivation profile")

    quorum = load_json("schemas/quorum-certificate.schema.json")
    receipt_items = quorum["properties"]["receipts"].get("items", {})
    if receipt_items.get("$ref") != "witness-receipt.schema.json":
        die("quorum receipts must $ref witness-receipt schema")

    target = load_json("schemas/target-evidence.schema.json")
    for key in ("target_derivation_profile_hash", "raw_source_object_hash"):
        if key not in target.get("required", []):
            die(f"target evidence missing required binding: {key}")

    pre = load_json("schemas/pre-return-certificate.schema.json")
    for key in ("candidate_generation_profile_hash", "target_derivation_profile_hash"):
        if key not in pre.get("required", []):
            die(f"PRE_RETURN missing frozen binding: {key}")

    registry = load_json("schemas/witness-registry.schema.json")
    if "transition_certificate_hash" not in registry.get("properties", {}):
        die("witness registry missing transition certificate binding")

    transition = load_json("schemas/registry-transition-certificate.schema.json")
    for key in ("old_registry_authorization", "new_registry_acceptance"):
        if key not in transition.get("required", []):
            die(f"registry transition missing joint certificate side: {key}")

    release_manifest = load_json("schemas/release-manifest.schema.json")
    if "gate_results" not in release_manifest.get("required", []):
        die("release manifest must carry per-gate results")

    ledger_doc = (ROOT / "docs/TRIAL_LEDGER.md").read_text(encoding="utf-8")
    if "AIFC:EXPERIMENT_GENESIS:v1" not in ledger_doc:
        die("ledger genesis sentinel rule missing")

    print("HARDENING_CONTRACTS = PASS")


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
    forbidden = sm.get("forbidden", {})
    for key in (
        "silent_trial_deletion",
        "candidate_before_created_certified",
        "target_before_quorum_certified",
        "target_selection_after_observing_target",
        "terminal_to_nonterminal",
        "state_skip_without_terminal_abort",
    ):
        if forbidden.get(key) is not True:
            die(f"state-machine forbidden rule missing: {key}")
    print("STATE_MACHINE = PASS")


def check_release_gate() -> None:
    gate = load_json("conformance/AIFC-RELEASE-GATE-v1.json")
    ids = [x.get("id") for x in gate.get("required_checks", []) if x.get("required") is True]
    needed = {
        "SPEC_SCHEMA_VALID",
        "STATE_MACHINE_VALID",
        "TRIAL_LEDGER_CONTINUITY",
        "LEDGER_GENESIS_SENTINEL_VALID",
        "CANDIDATE_GENERATION_PROVENANCE_VALID",
        "ENTROPY_PROFILE_VALID",
        "CANONICAL_RATIONAL_VALID",
        "TARGET_DERIVATION_PROFILE_VALID",
        "CAUSAL_MODEL_VALID",
        "WITNESS_LIFECYCLE_VALID",
        "REGISTRY_TRANSITION_VALID",
        "CITATION_ZENODO_METADATA_SYNC",
        "ALL_HONEST_VECTORS_PASS",
        "ALL_ATTACK_VECTORS_EXPECTED_REJECTION",
        "IMPLEMENTATION_A_PASS",
        "IMPLEMENTATION_B_PASS",
        "BYTE_IDENTICAL_CANONICALIZATION",
        "FAIL_OPEN_ZERO",
        "COMPLETE_TRIAL_PUBLICATION",
        "RELEASE_MANIFEST_PROOF_CARRYING",
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
    check_hardening_contracts()
    check_state_machine()
    check_release_gate()
    check_metadata_sync()
    print("DRAFT_REPOSITORY_CONFORMANCE = PASS")
    print("AIFC_V1_FROZEN = FALSE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
