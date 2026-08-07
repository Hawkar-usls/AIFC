#!/usr/bin/env python3
"""Repository-level checks for AIFC Assurance Convergence v1.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from assurance_evidence_v1 import (  # noqa: E402
    ASSURANCE_EVIDENCE_HASH_PROFILE,
    ASSURANCE_PROTOCOL_SCHEMAS,
)
from assurance_monotonicity import (  # noqa: E402
    ADMISSION_ALLOWED_SUCCESSORS,
    compare_release_gate_sets,
    compare_schema_identity,
    required_gate_ids,
)
from canonical import load_json_strict  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402


NEW_V11_GATES = {
    "ADMISSION_AUTHORITY_PARTIAL_ORDER_VALID",
    "INHERITED_GATE_SET_DERIVATION",
    "GATE_LINEAGE_EVIDENCE_RESOLUTION",
    "VALIDATOR_SEMANTICS_CONTENT_BINDING",
}

EXPECTED_VALIDATOR_MANIFEST_RAW_SHA256 = "cfea30ba2ce6e8fac366718e5d23d581789eafd037cff17b3f61aacc1455a14e"
EXPECTED_SEMANTICS_ID = "AIFC_JSON_SCHEMA_D2020_12_STRICT_SOURCE_RUNTIME_V04_CONTENT_BOUND"
CONVERGENCE_REGISTRATION_COMMIT = "ba1cc627ec06355bb1054431b32e9f91fdd885a4"
SOURCE_BYTES_COMMIT = "6169db0af0d15b1fdf5c37674f869de5dcb51c3c"

REQUIRED = [
    "spec/ASSURANCE-MONOTONICITY-v1.1.md",
    "reference/verifier/assurance_evidence_v1.py",
    "reference/verifier/assurance_monotonicity.py",
    "reference/verifier/gate_lineage_verifier.py",
    "reference/tests/test_assurance_convergence.py",
    "reference/tests/test_gate_lineage_verifier.py",
    "schemas/admission-authority-order.schema.json",
    "schemas/assurance-monotonicity-record-v2.schema.json",
    "schemas/gate-definition.schema.json",
    "schemas/gate-strengthening-evidence.schema.json",
    "schemas/validator-semantics-manifest.schema.json",
    "schemas/schema-identity-record-v2.schema.json",
    "schemas/schema-identity-registry-v2.schema.json",
    "conformance/AIFC-ADMISSION-AUTHORITY-ORDER-v1.json",
    "conformance/AIFC-VALIDATOR-SEMANTICS-MANIFEST-v1.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v2.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.8-draft.json",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(rel: str):
    try:
        return load_json_strict(ROOT / rel)
    except Exception as exc:
        fail(f"cannot strictly parse {rel}: {exc}")


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        fail("missing convergence v1.1 files: " + ", ".join(missing))
    print(f"ASSURANCE_CONVERGENCE_V11_REQUIRED_FILES = PASS ({len(REQUIRED)}/{len(REQUIRED)})")

    previous = load("conformance/AIFC-RELEASE-GATE-v1.0.7-draft.json")
    current = load("conformance/AIFC-RELEASE-GATE-v1.0.8-draft.json")
    pred_ids = required_gate_ids(previous)
    curr_ids = required_gate_ids(current)
    if len(pred_ids) != 61:
        fail(f"expected 61 mandatory predecessor gates, got {len(pred_ids)}")
    if len(curr_ids) != 65:
        fail(f"expected 65 mandatory v1.1 gates, got {len(curr_ids)}")
    if curr_ids - pred_ids != NEW_V11_GATES:
        fail(f"unexpected v1.1 gate additions: {sorted(curr_ids-pred_ids)}")
    if pred_ids - curr_ids:
        fail(f"RELEASE_GATE_REGRESSION:{sorted(pred_ids-curr_ids)}")
    comparison = compare_release_gate_sets(previous, current)
    if comparison.status != "PASS":
        fail("release-gate monotonicity failed: " + ",".join(comparison.failure_codes))
    if current.get("supersedes_for_draft_evaluation") != "conformance/AIFC-RELEASE-GATE-v1.0.7-draft.json":
        fail("v1.0.8 release-gate predecessor binding invalid")
    if current.get("status") != "DRAFT_NOT_SATISFIED":
        fail("v1.0.8 release gate must remain DRAFT_NOT_SATISFIED")
    print("RELEASE_GATE_MONOTONICITY = PASS (61 inherited + 4 new; 0 removed)")

    order = load("conformance/AIFC-ADMISSION-AUTHORITY-ORDER-v1.json")
    validate_protocol_object(order, "AIFC/admission-authority-order/v1")
    frozen_order = {key: frozenset(value) for key, value in order["allowed_successor_outcomes"].items()}
    if frozen_order != ADMISSION_ALLOWED_SUCCESSORS:
        fail("admission partial-order code/table drift")
    miss = "FORWARD_NULL_CONSISTENT_MISS"
    candidate = "FORWARD_NULL_INCOMPATIBILITY_CANDIDATE"
    if candidate in frozen_order[miss]:
        fail("SAME_RANK_AUTHORITY_ESCALATION remains permitted")
    if miss in frozen_order[candidate]:
        fail("incomparable forward-null semantic rewrite remains permitted")
    print("ADMISSION_AUTHORITY_PARTIAL_ORDER_VALID = PASS")

    if ASSURANCE_EVIDENCE_HASH_PROFILE != "AIFC/assurance-evidence-hash/v1":
        fail("assurance evidence hash profile identity drift")
    expected_assurance_schemas = {
        "AIFC/gate-definition/v1",
        "AIFC/gate-strengthening-evidence/v1",
        "AIFC/gate-lineage-transition/v1",
    }
    if set(ASSURANCE_PROTOCOL_SCHEMAS) != expected_assurance_schemas:
        fail("assurance evidence hash schema-domain drift")
    historical_v02 = (VERIFIER / "canonical_v02.py").read_text(encoding="utf-8")
    for schema_id in sorted(expected_assurance_schemas):
        if schema_id in historical_v02:
            fail(f"HISTORICAL_HASH_DOMAIN_MUTATION:v0.2 unexpectedly contains {schema_id}")
    assurance_source = (VERIFIER / "assurance_evidence_v1.py").read_text(encoding="utf-8")
    for token in (
        "AIFC:ASSURANCE-EVIDENCE:v1",
        "assurance_protocol_hash_v1",
        "AssuranceEvidenceResolverV1",
    ):
        if token not in assurance_source:
            fail(f"assurance evidence domain implementation missing: {token}")
    print("ASSURANCE_EVIDENCE_DOMAIN_SEPARATION = PASS (historical v0.2 untouched)")

    manifest_path = ROOT / "conformance" / "AIFC-VALIDATOR-SEMANTICS-MANIFEST-v1.json"
    manifest = load("conformance/AIFC-VALIDATOR-SEMANTICS-MANIFEST-v1.json")
    validate_protocol_object(manifest, "AIFC/validator-semantics-manifest/v1")
    manifest_hash = raw_sha256(manifest_path)
    if manifest_hash != EXPECTED_VALIDATOR_MANIFEST_RAW_SHA256:
        fail(f"validator semantics manifest raw hash drift: {manifest_hash}")
    if manifest.get("semantics_id") != EXPECTED_SEMANTICS_ID:
        fail("validator semantics ID drift")
    for source in manifest.get("source_files", []):
        path = ROOT / source["path"]
        if git_blob_sha1(path) != source["git_blob_sha1"]:
            fail(f"VALIDATOR_IMPLEMENTATION_CHANGED_WITH_SAME_SEMANTICS_ID:GIT:{source['path']}")
        if raw_sha256(path) != source["raw_sha256"]:
            fail(f"VALIDATOR_IMPLEMENTATION_CHANGED_WITH_SAME_SEMANTICS_ID:SHA256:{source['path']}")
    lock = manifest["dependency_lock"]
    lock_path = ROOT / lock["path"]
    if git_blob_sha1(lock_path) != lock["git_blob_sha1"] or raw_sha256(lock_path) != lock["raw_sha256"]:
        fail("validator dependency lock content drift")
    lock_rows = [
        line.strip() for line in lock_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    manifest_rows = {
        f"{row['name']}=={row['version']} --hash=sha256:{row['wheel_sha256']}"
        for row in lock["distributions"]
    }
    if set(lock_rows) != manifest_rows or len(lock_rows) != len(manifest_rows):
        fail("validator dependency semantic manifest does not exactly match hash lock")
    for required_policy in (
        "LOCAL_REPOSITORY_REGISTRY_ONLY_NO_NETWORK",
        "REJECT",
        "UTF8_STRICT_NO_BOM",
    ):
        if required_policy not in set(str(v) for v in manifest["runtime"].values()):
            fail(f"validator semantics policy missing: {required_policy}")
    print("VALIDATOR_SEMANTICS_CONTENT_BINDING = PASS")

    old_registry = load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v1.json")
    registry = load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v2.json")
    validate_protocol_object(registry, "AIFC/schema-identity-registry/v2")
    if registry.get("admission_semantics_id") != EXPECTED_SEMANTICS_ID:
        fail("schema registry v2 semantics ID drift")
    if registry.get("admission_semantics_content_hash") != manifest_hash:
        fail("schema registry v2 semantics content hash drift")

    old_by_id = {row["schema_id"]: row for row in old_registry["records"]}
    new_by_id = {row["schema_id"]: row for row in registry["records"]}
    if set(old_by_id) != set(new_by_id):
        fail("schema registry v2 must preserve exactly the registered v1 identity set in this hardening")
    raw_mismatches: list[tuple[str, str, str]] = []
    for schema_id in sorted(new_by_id):
        old = old_by_id[schema_id]
        record = new_by_id[schema_id]
        path = ROOT / record["source_path"]
        actual_git = git_blob_sha1(path)
        actual_raw = raw_sha256(path)
        if record.get("git_blob_sha1") != old.get("source_content_id"):
            fail(f"v2 Git identity does not preserve v1 registered source for {schema_id}")
        if actual_git != record.get("git_blob_sha1"):
            fail(f"SAME_SCHEMA_ID_LANGUAGE_MUTATION:GIT_BLOB_CHANGED:{schema_id}")
        if actual_raw != record.get("raw_schema_sha256"):
            raw_mismatches.append((schema_id, str(record.get("raw_schema_sha256")), actual_raw))
        if record.get("admission_semantics_id") != EXPECTED_SEMANTICS_ID:
            fail(f"validator semantics ID rebinding for {schema_id}")
        if record.get("admission_semantics_content_hash") != manifest_hash:
            fail(f"validator semantics content rebinding for {schema_id}")
        if record.get("source_bytes_observed_at_commit") != SOURCE_BYTES_COMMIT:
            fail(f"source-bytes observation commit drift for {schema_id}")
        if record.get("registered_immutable_at_commit") != CONVERGENCE_REGISTRATION_COMMIT:
            fail(f"registration point drift for {schema_id}")
        if record.get("first_historical_appearance_status") != "NOT_ESTABLISHED":
            fail(f"historical first-appearance overclaim for {schema_id}")
        if record.get("first_historical_appearance_commit") is not None:
            fail(f"unproven historical first-appearance commit asserted for {schema_id}")

        identity = compare_schema_identity(
            record,
            current_schema_id=schema_id,
            current_dialect="https://json-schema.org/draft/2020-12/schema",
            current_git_blob_sha1=actual_git,
            current_raw_schema_sha256=actual_raw,
            current_admission_semantics_id=EXPECTED_SEMANTICS_ID,
            current_admission_semantics_content_hash=manifest_hash,
        )
        if identity.status != "PASS" and record.get("raw_schema_sha256") == actual_raw:
            fail(f"schema identity v2 comparator failed for {schema_id}: {identity.failure_codes}")

    if raw_mismatches:
        print("SCHEMA_RAW_SHA256_BOOTSTRAP = REQUIRED")
        for schema_id, recorded, actual in raw_mismatches:
            print(f"SCHEMA_RAW_SHA256_PROPOSAL {schema_id} recorded={recorded} actual={actual}")
        fail(f"schema registry v2 raw SHA-256 values not yet frozen ({len(raw_mismatches)} mismatches)")
    print(f"SCHEMA_IDENTIFIER_IMMUTABILITY = PASS_DUAL_HASH ({len(new_by_id)} identities)")
    print("FULL_HISTORICAL_SCHEMA_LANGUAGE_LINEAGE = NOT_ESTABLISHED")
    print("FULL_NORMATIVE_SCHEMA_GRAPH_COVERAGE = NOT_ESTABLISHED")

    monotonicity_source = (VERIFIER / "assurance_monotonicity.py").read_text(encoding="utf-8")
    signature_match = re.search(r"def compare_verifier_results\([\s\S]*?\) -> MonotonicityComparison:", monotonicity_source)
    if signature_match is None:
        fail("compare_verifier_results signature not found")
    if "inherited_gate_ids" in signature_match.group(0):
        fail("INHERITED_GATE_SET_OMISSION: comparator still trusts caller-supplied inherited_gate_ids")
    for token in (
        "derive_inherited_gate_obligations",
        "SAME_RANK_AUTHORITY_ESCALATION",
        "FAKE_GATE_STRENGTHENING_RECEIPT",
        "VALIDATOR_IMPLEMENTATION_CHANGED_WITH_SAME_SEMANTICS_ID",
    ):
        if token not in monotonicity_source:
            fail(f"v1.1 monotonicity hardening token missing: {token}")
    print("INHERITED_GATE_SET_DERIVATION = IMPLEMENTED")

    lineage_source = (VERIFIER / "gate_lineage_verifier.py").read_text(encoding="utf-8")
    for token in (
        "BOOLEAN_TRUTH_TABLE_IMPLICATION_V1",
        "GATE_STRENGTHENING_COUNTEREXAMPLE",
        "GATE_LINEAGE_EVIDENCE_RESOLUTION_FAILED",
        "STRENGTHENING_CONFIRMED",
    ):
        if token not in lineage_source:
            fail(f"gate-lineage proof replay token missing: {token}")
    print("GATE_LINEAGE_EVIDENCE_RESOLUTION = IMPLEMENTED_CANDIDATE")

    v06 = (VERIFIER / "full_admission_v06.py").read_text(encoding="utf-8")
    if "from full_admission_v03 import verify_replay_manifest as verify_v03" not in v06:
        fail("INHERITED_HARDENING_LAYER_OMISSION:v0.6 missing mandatory v0.3 import")
    if "result = verify_v03(manifest, resolver)" not in v06:
        fail("INHERITED_HARDENING_LAYER_OMISSION:v0.6 does not execute v0.3")
    print("CURRENT_V06_PREDECESSOR_COMPOSITION_GUARD = PASS")

    spec = (ROOT / "spec" / "ASSURANCE-MONOTONICITY-v1.1.md").read_text(encoding="utf-8")
    for phrase in (
        "The monotonicity checker must not trust the successor to define what was inherited.",
        "SAME_RANK_AUTHORITY_ESCALATION",
        "INHERITED_GATE_SET_OMISSION",
        "FAKE_GATE_STRENGTHENING_RECEIPT",
        "VALIDATOR_IMPLEMENTATION_CHANGED_WITH_SAME_SEMANTICS_ID",
        "REQUIRED ARCHITECTURE / NOT YET IMPLEMENTED",
    ):
        if phrase not in spec:
            fail(f"v1.1 normative assurance phrase missing: {phrase}")

    print("ASSURANCE_CONVERGENCE_V11 = IMPLEMENTED_CANDIDATE")
    print("REAL_SUCCESSOR_WRAPPED_REPLAY = NOT_YET_ESTABLISHED")
    print("CLEAN_V0_7_VERSIONED_ENVELOPE = REQUIRED_NOT_IMPLEMENTED")
    print("HISTORICAL_KEY_LIFECYCLE = BLOCKED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
