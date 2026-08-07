#!/usr/bin/env python3
"""Repository-level conformance checker for SAL v1.3 Root Closure."""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from schema_runtime import validate_protocol_object  # noqa: E402
from scientific_assurance_lineage_v13 import (  # noqa: E402
    AUTHORITY_RECEIPT_ID,
    NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
    NORMATIVE_ROOT_REGISTRY_PATH,
    PREDECESSOR_EXACT_MAIN_COMMIT,
    NormativeRootClosureError,
    RootClosedNormativeRepositoryResolver,
    _load_authority_receipt,
    build_assurance_monotonicity_record_v4,
    compare_verifier_results_root_closed,
    git_blob_sha1_bytes,
)

V12_SCHEMAS = [
    "schemas/assurance-hash-profile-manifest.schema.json",
    "schemas/inherited-gate-hash-profile.schema.json",
    "schemas/normative-assurance-root-registry.schema.json",
    "schemas/inherited-gate-obligation-set.schema.json",
    "schemas/assurance-monotonicity-record-v3.schema.json",
]
V13_SCHEMAS = [
    "schemas/normative-authority-receipt.schema.json",
    "schemas/normative-assurance-root-registry-v2.schema.json",
    "schemas/schema-identity-registry-v3.schema.json",
    "schemas/inherited-gate-hash-implementation-binding.schema.json",
    "schemas/assurance-monotonicity-record-v4.schema.json",
]
ALL_SAL_SCHEMAS = V12_SCHEMAS + V13_SCHEMAS

REQUIRED_FILES = [
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.1.md",
    "reference/verifier/scientific_assurance_lineage.py",
    "reference/verifier/scientific_assurance_lineage_v13.py",
    "reference/verifier/inherited_gate_hash_v1.py",
    "reference/tests/test_sal_root_closure_v13.py",
    "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json",
    "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json",
    "conformance/AIFC-NORMATIVE-AUTHORITY-RECEIPT-7e58b47-v1.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v2.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v3.json",
    "conformance/AIFC-INHERITED-GATE-HASH-PROFILE-v1.json",
    "conformance/AIFC-INHERITED-GATE-HASH-IMPLEMENTATION-BINDING-v1.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.9-draft.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.10-draft.json",
] + ALL_SAL_SCHEMAS

NEW_GATES = {
    "NORMATIVE_ROOT_REGISTRY_CONTENT_IDENTITY",
    "NORMATIVE_RESOLVER_PROVENANCE",
    "AUTHORITY_STATUS_TRANSITION_ENFORCED",
    "SAL_SCHEMA_IDENTITY_REGISTRATION",
    "INHERITED_HASH_PROFILE_IMPLEMENTATION_BINDING",
}


def die(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(rel: str):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"cannot parse {rel}: {exc}")


def required_ids(doc: dict) -> set[str]:
    rows = doc.get("required_checks")
    if not isinstance(rows, list):
        die("required_checks is not an array")
    ids = [r.get("id") for r in rows if isinstance(r, dict) and r.get("required") is True]
    if not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids)):
        die("invalid or duplicate required gate IDs")
    return set(ids)


def check_files_and_schema_headers() -> None:
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).is_file()]
    if missing:
        die("missing root-closure files: " + ", ".join(missing))
    for rel in ALL_SAL_SCHEMAS:
        obj = load(rel)
        if obj.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            die(f"{rel}: wrong dialect")
        if obj.get("$id") != f"https://github.com/Hawkar-usls/AIFC/{rel}":
            die(f"{rel}: wrong $id")
        if obj.get("type") != "object" or obj.get("additionalProperties") is not False:
            die(f"{rel}: top level must be a closed object")
    print(f"SAL_ROOT_CLOSURE_REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")
    print(f"SAL_V13_SCHEMA_HEADERS = PASS ({len(ALL_SAL_SCHEMAS)}/{len(ALL_SAL_SCHEMAS)})")


def check_schema_identity_registry() -> None:
    registry = load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v3.json")
    validate_protocol_object(registry, "AIFC/schema-identity-registry/v3")
    if registry.get("predecessor_registry_git_blob_sha1") != "bb7ef880d9fced16ee42ea266d1f97409457877b":
        die("schema identity registry v2 predecessor rebinding")
    records = registry.get("records")
    if not isinstance(records, list) or len(records) != 10:
        die("schema identity registry v3 must contain exact ten-record SAL delta")
    seen = set()
    for row in records:
        schema_id = row["schema_id"]
        if schema_id in seen:
            die(f"duplicate schema registration: {schema_id}")
        seen.add(schema_id)
        raw = (ROOT / row["source_path"]).read_bytes()
        if git_blob_sha1_bytes(raw) != row["git_blob_sha1"]:
            die(f"schema git blob mismatch: {schema_id}")
        if hashlib.sha256(raw).hexdigest() != row["raw_schema_sha256"]:
            die(f"schema raw sha256 mismatch: {schema_id}")
    print("SAL_SCHEMA_IDENTITY_REGISTRATION = PASS (10/10 dual-bound)")


def check_root_identity_and_resolver_provenance() -> None:
    raw = (ROOT / NORMATIVE_ROOT_REGISTRY_PATH).read_bytes()
    if git_blob_sha1_bytes(raw) != NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1:
        die("normative root registry v2 content identity mismatch")
    params = inspect.signature(compare_verifier_results_root_closed).parameters
    for forbidden in ("normative_resolver", "registry", "registry_path", "repository_root", "root"):
        if forbidden in params:
            die(f"root-closed comparator still accepts caller authority surface: {forbidden}")
    try:
        RootClosedNormativeRepositoryResolver(ROOT, {})
    except TypeError as exc:
        if "CALLER_SUPPLIED_ROOT_REGISTRY_FORBIDDEN" not in str(exc):
            die(f"unexpected direct-resolver rejection: {exc}")
    else:
        die("direct resolver construction unexpectedly allowed")
    RootClosedNormativeRepositoryResolver.from_repository_authority()
    print("NORMATIVE_ROOT_REGISTRY_CONTENT_IDENTITY = PASS")
    print("NORMATIVE_RESOLVER_PROVENANCE = PASS")


def check_authority_status_transition() -> None:
    receipt = _load_authority_receipt(AUTHORITY_RECEIPT_ID, PREDECESSOR_EXACT_MAIN_COMMIT)
    if receipt.get("unit_test_count") != 165:
        die("v1.2 exact authority receipt test-count rebinding")
    resolver = RootClosedNormativeRepositoryResolver.from_repository_authority()
    attested = resolver.resolve("AIFC-RELEASE-GATE-v1.0.9-draft", "RELEASE_GATE")
    if attested.authority_receipt_id != AUTHORITY_RECEIPT_ID:
        die("attested successor did not resolve through exact authority receipt")
    try:
        resolver.resolve("AIFC-RELEASE-GATE-v1.0.10-draft", "RELEASE_GATE")
    except NormativeRootClosureError as exc:
        if "UNATTESTED_SUCCESSOR_NORMATIVE_PROMOTION" not in str(exc):
            die(f"wrong candidate rejection: {exc}")
    else:
        die("unattested successor was promoted to normative")
    print("AUTHORITY_STATUS_TRANSITION_ENFORCED = PASS")


def check_inherited_hash_binding() -> None:
    binding = load("conformance/AIFC-INHERITED-GATE-HASH-IMPLEMENTATION-BINDING-v1.json")
    validate_protocol_object(binding, "AIFC/inherited-gate-hash-implementation-binding/v1")
    if binding.get("source_observed_at_commit") != "7f3f3662dd99bfb2baec7f91d2c39ec61631898c":
        die("inherited hash source observation commit invalid")
    for key in ("canonicalization_source", "hash_implementation_source"):
        src = binding[key]
        if git_blob_sha1_bytes((ROOT / src["path"]).read_bytes()) != src["git_blob_sha1"]:
            die(f"inherited hash source drift: {key}")
    print("INHERITED_HASH_PROFILE_IMPLEMENTATION_BINDING = PASS")


def check_release_frontier_and_comparator() -> None:
    previous = load("conformance/AIFC-RELEASE-GATE-v1.0.9-draft.json")
    current = load("conformance/AIFC-RELEASE-GATE-v1.0.10-draft.json")
    pred, succ = required_ids(previous), required_ids(current)
    if len(pred) != 73 or len(succ) != 78 or pred - succ or succ - pred != NEW_GATES:
        die(f"v1.3 release frontier mismatch: {len(pred)} -> {len(succ)} delta={sorted(succ-pred)}")
    if current.get("status") != "DRAFT_NOT_SATISFIED":
        die("v1.0.10 release gate must remain DRAFT_NOT_SATISFIED")
    comparison = compare_verifier_results_root_closed(
        {"terminal_grade": "NOT_ADMITTED", "gate_results": {}},
        {"terminal_grade": "NOT_ADMITTED", "gate_results": {}},
        predecessor_release_gate_id="AIFC-RELEASE-GATE-v1.0.8-draft",
        successor_release_gate_id="AIFC-RELEASE-GATE-v1.0.9-draft",
    )
    if comparison.status != "PASS":
        die("root-closed replay failed: " + ", ".join(comparison.failure_codes))
    record = build_assurance_monotonicity_record_v4(
        comparison,
        predecessor_verifier="AIFC-Verifier-A-v0.6",
        successor_verifier="AIFC-Verifier-A-v0.7-candidate",
        predecessor_release_gate_id="AIFC-RELEASE-GATE-v1.0.8-draft",
        successor_release_gate_id="AIFC-RELEASE-GATE-v1.0.9-draft",
    )
    validate_protocol_object(record, "AIFC/assurance-monotonicity-record/v4")
    print("SAL_RELEASE_GATE_73_TO_78 = PASS")
    print("ROOT_CLOSED_MONOTONICITY_RECORD_V4 = PASS")


def main() -> int:
    check_files_and_schema_headers()
    check_schema_identity_registry()
    check_root_identity_and_resolver_provenance()
    check_authority_status_transition()
    check_inherited_hash_binding()
    check_release_frontier_and_comparator()
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_3_ROOT_CLOSURE = PASS")
    print("NORMATIVE_ROOT_LINEAGE_GENERAL = NOT_ESTABLISHED")
    print("V1_0_10_NORMATIVE_PROMOTION = BLOCKED_PENDING_EXACT_COMMIT_ATTESTATION")
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
    raise SystemExit(main())
