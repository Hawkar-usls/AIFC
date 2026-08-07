#!/usr/bin/env python3
"""Repository-level conformance checker for Scientific Assurance Lineage v1.2.

This checker is intentionally additive. It does not rewrite the historical base
repository checker or historical v1.1 assurance checker. It verifies the new SAL
surface, runtime schemas, normative-root bindings, hash-profile identities and
65 -> 73 release-frontier extension.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from schema_runtime import RuntimeSchemaError, validate_protocol_object  # noqa: E402
from scientific_assurance_lineage import (  # noqa: E402
    ADMISSION_ORDER_ARTIFACT_ID,
    INHERITED_GATE_HASH_PROFILE_ID,
    NORMATIVE_ROOT_REGISTRY_ID,
    SAL_BOOTSTRAP_ROOT_COMMIT,
    NormativeRepositoryResolver,
    compare_verifier_results_anchored,
    inherited_gate_obligation_hash_v1,
)


SAL_SCHEMA_FILES = [
    "schemas/assurance-hash-profile-manifest.schema.json",
    "schemas/inherited-gate-hash-profile.schema.json",
    "schemas/normative-assurance-root-registry.schema.json",
    "schemas/inherited-gate-obligation-set.schema.json",
    "schemas/assurance-monotonicity-record-v3.schema.json",
]

SAL_REQUIRED_FILES = [
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.1.md",
    "docs/SCIENTIFIC_ASSURANCE_LINEAGE_RELATED_WORK.md",
    "reference/verifier/scientific_assurance_lineage.py",
    "reference/tests/test_scientific_assurance_lineage.py",
    "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json",
    "conformance/AIFC-ASSURANCE-HASH-PROFILE-MANIFEST-v1.json",
    "conformance/AIFC-INHERITED-GATE-HASH-PROFILE-v1.json",
    "conformance/AIFC-PROOF-ANCHORING-FRONTIER-v1.2.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.8-draft.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.9-draft.json",
] + SAL_SCHEMA_FILES

V12_NEW_GATES = {
    "NORMATIVE_RELEASE_GATE_IDENTITY",
    "NORMATIVE_ROOT_LINEAGE_VALID",
    "ADMISSION_ORDER_PROFILE_CONTENT_IDENTITY",
    "INHERITED_GATE_SET_DOMAIN_IDENTITY",
    "ASSURANCE_HASH_PROFILE_CONTENT_IDENTITY",
    "GATE_DEFINITION_HISTORICAL_ANCHOR",
    "GATE_ATOM_SEMANTIC_IDENTITY",
    "AUTHORITY_CLOSED_PROOF",
}


def die(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(rel: str):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"cannot parse {rel}: {exc}")


def required_gate_ids(doc: dict) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        die("release gate required_checks is not an array")
    ids = [row.get("id") for row in rows if isinstance(row, dict) and row.get("required") is True]
    if not all(isinstance(item, str) and item for item in ids):
        die("release gate contains invalid required gate ID")
    if len(ids) != len(set(ids)):
        die("release gate contains duplicate required gate ID")
    return set(ids)


def check_required_files() -> None:
    missing = [rel for rel in SAL_REQUIRED_FILES if not (ROOT / rel).is_file()]
    if missing:
        die("missing SAL files: " + ", ".join(missing))
    print(f"SAL_REQUIRED_FILES = PASS ({len(SAL_REQUIRED_FILES)}/{len(SAL_REQUIRED_FILES)})")


def check_schema_headers() -> None:
    for rel in SAL_SCHEMA_FILES:
        obj = load_json(rel)
        expected_id = f"https://github.com/Hawkar-usls/AIFC/{rel}"
        if obj.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            die(f"{rel}: wrong JSON Schema dialect")
        if obj.get("$id") != expected_id:
            die(f"{rel}: unexpected $id")
        if obj.get("type") != "object" or obj.get("additionalProperties") is not False:
            die(f"{rel}: SAL top-level schema must be a closed object")
    print(f"SAL_SCHEMA_HEADERS = PASS ({len(SAL_SCHEMA_FILES)}/{len(SAL_SCHEMA_FILES)})")


def check_runtime_schema_admission() -> None:
    registry = load_json("conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json")
    assurance_profile = load_json("conformance/AIFC-ASSURANCE-HASH-PROFILE-MANIFEST-v1.json")
    inherited_profile = load_json("conformance/AIFC-INHERITED-GATE-HASH-PROFILE-v1.json")
    try:
        validate_protocol_object(registry, "AIFC/normative-assurance-root-registry/v1")
        validate_protocol_object(assurance_profile, "AIFC/assurance-hash-profile-manifest/v1")
        validate_protocol_object(inherited_profile, "AIFC/inherited-gate-hash-profile/v1")
        validate_protocol_object(
            {
                "schema": "AIFC/assurance-monotonicity-record/v3",
                "predecessor_verifier": "AIFC-Verifier-A-v0.6",
                "successor_verifier": "AIFC-Verifier-A-v0.7-candidate",
                "fixture_hash": "1" * 64,
                "wrapped_fixture_hash": "2" * 64,
                "normative_root_registry_id": NORMATIVE_ROOT_REGISTRY_ID,
                "bootstrap_root_commit": SAL_BOOTSTRAP_ROOT_COMMIT,
                "predecessor_release_gate_id": "AIFC-RELEASE-GATE-v1.0.8-draft",
                "predecessor_release_gate_git_blob_sha1": "1" * 40,
                "successor_release_gate_id": "AIFC-RELEASE-GATE-v1.0.9-draft",
                "successor_release_gate_git_blob_sha1": "2" * 40,
                "predecessor_outcome": "NOT_ADMITTED",
                "successor_outcome": "NOT_ADMITTED",
                "admission_order_id": ADMISSION_ORDER_ARTIFACT_ID,
                "admission_order_git_blob_sha1": "3" * 40,
                "inherited_gate_hash_profile_id": INHERITED_GATE_HASH_PROFILE_ID,
                "inherited_gate_set_hash": "4" * 64,
                "gate_replacement_authority_status": "NOT_REQUIRED_ADDITIVE_ONLY",
                "monotonicity_result": "PASS",
                "failure_codes": [],
            },
            "AIFC/assurance-monotonicity-record/v3",
        )
        inherited_gate_obligation_hash_v1(
            {
                "schema": "AIFC/inherited-gate-obligation-set/v1",
                "hash_profile_id": INHERITED_GATE_HASH_PROFILE_ID,
                "predecessor_release_gate_id": "P",
                "predecessor_release_gate_git_blob_sha1": "1" * 40,
                "successor_release_gate_id": "S",
                "successor_release_gate_git_blob_sha1": "2" * 40,
                "obligations": [
                    {
                        "predecessor_gate_id": "KEEP_GATE",
                        "successor_gate_ids": ["KEEP_GATE"],
                        "transition_hash": None,
                    }
                ],
            }
        )
    except (RuntimeSchemaError, ValueError) as exc:
        die(f"SAL runtime schema admission failed: {exc}")
    print("SAL_RUNTIME_SCHEMA_ADMISSION = PASS")


def check_release_frontier() -> None:
    previous = load_json("conformance/AIFC-RELEASE-GATE-v1.0.8-draft.json")
    current = load_json("conformance/AIFC-RELEASE-GATE-v1.0.9-draft.json")
    pred = required_gate_ids(previous)
    succ = required_gate_ids(current)
    if len(pred) != 65 or len(succ) != 73:
        die(f"unexpected release gate counts: {len(pred)} -> {len(succ)}")
    if pred - succ:
        die("v1.2 release gate removed inherited requirements: " + ", ".join(sorted(pred - succ)))
    if succ - pred != V12_NEW_GATES:
        die("v1.2 release gate delta is not the exact eight-gate proof-anchoring extension")
    if current.get("status") != "DRAFT_NOT_SATISFIED":
        die("v1.2 release gate must remain DRAFT_NOT_SATISFIED")
    print("SAL_RELEASE_GATE_65_TO_73 = PASS")


def check_normative_resolution() -> None:
    resolver = NormativeRepositoryResolver.from_file(ROOT)
    predecessor = resolver.resolve("AIFC-RELEASE-GATE-v1.0.8-draft", "RELEASE_GATE")
    successor = resolver.resolve("AIFC-RELEASE-GATE-v1.0.9-draft", "RELEASE_GATE")
    order = resolver.resolve(ADMISSION_ORDER_ARTIFACT_ID, "ADMISSION_ORDER")
    resolver.resolve("AIFC/assurance-evidence-hash/v1", "ASSURANCE_HASH_PROFILE")
    resolver.resolve(INHERITED_GATE_HASH_PROFILE_ID, "INHERITED_GATE_HASH_PROFILE")
    if predecessor.git_blob_sha1 != "656bda0bae1d1af515a642f157149450c78d879e":
        die("historical v1.0.8 release root rebinding")
    if order.git_blob_sha1 != "38eeb695caf781dcdc79115d4903c743db7311f9":
        die("historical admission-order root rebinding")
    comparison = compare_verifier_results_anchored(
        {"terminal_grade": "NOT_ADMITTED", "gate_results": {}},
        {"terminal_grade": "NOT_ADMITTED", "gate_results": {}},
        predecessor_release_gate_id="AIFC-RELEASE-GATE-v1.0.8-draft",
        successor_release_gate_id="AIFC-RELEASE-GATE-v1.0.9-draft",
        normative_resolver=resolver,
    )
    if comparison.status != "PASS":
        die("anchored additive comparison failed: " + ", ".join(comparison.failure_codes))
    if successor.git_blob_sha1 != comparison.successor_release_gate_git_blob_sha1:
        die("successor release identity not propagated into comparison")
    print("SAL_NORMATIVE_RESOLUTION = PASS")


def main() -> int:
    check_required_files()
    check_schema_headers()
    check_runtime_schema_admission()
    check_release_frontier()
    check_normative_resolution()
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_2_CONFORMANCE = PASS")
    print("GATE_DEFINITION_HISTORICAL_ANCHOR = NOT_ESTABLISHED")
    print("GATE_ATOM_SEMANTIC_IDENTITY = NOT_ESTABLISHED")
    print("AUTHORITY_CLOSED_PROOF_GENERAL = NOT_ESTABLISHED")
    print("ASSURANCE_LINEAGE_SOUNDNESS = THEOREM_TARGET_NOT_YET_PROVED")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
