#!/usr/bin/env python3
"""Repository-level conformance checks for AIFC assurance convergence.

Exit zero means the convergence contracts are internally consistent in this source
snapshot. It does NOT mean the global frozen gates are satisfied and does not claim
future successor monotonicity before a successor corpus has actually been replayed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from assurance_monotonicity import compare_release_gate_sets, required_gate_ids  # noqa: E402
from canonical import load_json_strict  # noqa: E402


NEW_GATES = {
    "VERIFIER_ADMISSION_MONOTONICITY",
    "RELEASE_GATE_MONOTONICITY",
    "SCHEMA_IDENTIFIER_IMMUTABILITY",
    "NORMATIVE_PROFILE_LINEAGE_VALID",
    "SIGNATURE_PREIMAGE_RESOLVER_DERIVED_REPLAY",
}

REQUIRED = [
    "spec/ASSURANCE-MONOTONICITY-v1.md",
    "reference/verifier/assurance_monotonicity.py",
    "reference/tests/test_assurance_convergence.py",
    "schemas/assurance-monotonicity-record.schema.json",
    "schemas/gate-lineage-transition.schema.json",
    "schemas/schema-identity-record.schema.json",
    "schemas/schema-identity-registry.schema.json",
    "schemas/normative-profile-lineage.schema.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v1.json",
    "conformance/AIFC-NORMATIVE-PROFILE-LINEAGE-v1.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.7-draft.json",
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


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        fail("missing convergence files: " + ", ".join(missing))
    print(f"ASSURANCE_CONVERGENCE_REQUIRED_FILES = PASS ({len(REQUIRED)}/{len(REQUIRED)})")

    previous = load("conformance/AIFC-RELEASE-GATE-v1.0.6-draft.json")
    current = load("conformance/AIFC-RELEASE-GATE-v1.0.7-draft.json")
    pred_ids = required_gate_ids(previous)
    curr_ids = required_gate_ids(current)
    if len(pred_ids) != 56:
        fail(f"expected 56 mandatory predecessor gates, got {len(pred_ids)}")
    if len(curr_ids) != 61:
        fail(f"expected 61 mandatory convergence gates, got {len(curr_ids)}")
    if curr_ids - pred_ids != NEW_GATES:
        fail(f"unexpected convergence additions: {sorted(curr_ids-pred_ids)}")
    if pred_ids - curr_ids:
        fail(f"RELEASE_GATE_REGRESSION:{sorted(pred_ids-curr_ids)}")
    comparison = compare_release_gate_sets(previous, current)
    if comparison.status != "PASS":
        fail("release-gate monotonicity failed: " + ",".join(comparison.failure_codes))
    if current.get("status") != "DRAFT_NOT_SATISFIED":
        fail("convergence gate must remain DRAFT_NOT_SATISFIED")
    print("RELEASE_GATE_MONOTONICITY = PASS (56 inherited + 5 new; 0 removed)")

    registry = load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v1.json")
    semantics_id = registry.get("validation_semantics_id")
    if semantics_id != "AIFC_JSON_SCHEMA_D2020_12_STRICT_SOURCE_RUNTIME_V03":
        fail(f"schema validation semantics identity drift: {semantics_id!r}")
    seen: set[str] = set()
    for record in registry.get("records", []):
        schema_id = record.get("schema_id")
        if not isinstance(schema_id, str) or schema_id in seen:
            fail(f"duplicate/invalid issued schema id: {schema_id!r}")
        seen.add(schema_id)
        if record.get("source_content_algorithm") != "GIT_BLOB_SHA1":
            fail(f"unsupported initial schema source algorithm for {schema_id}")
        path = ROOT / str(record.get("source_path"))
        if not path.is_file():
            fail(f"issued schema source missing: {path}")
        actual = git_blob_sha1(path)
        if actual != record.get("source_content_id"):
            fail(f"SAME_SCHEMA_ID_LANGUAGE_MUTATION:{schema_id}:{record.get('source_content_id')}:{actual}")
        if record.get("admission_semantics_version") != semantics_id:
            fail(f"schema validator semantics rebinding: {schema_id}")
    if len(seen) < 10:
        fail("initial issued schema registry must cover the critical signature/quorum connected graph")
    print(f"SCHEMA_IDENTIFIER_IMMUTABILITY = PASS_FOR_REGISTERED_ISSUED_GRAPH ({len(seen)} identities)")
    print("SCHEMA_GRAPH_FULL_V1_FREEZE_COVERAGE = REQUIRED_NOT_YET_CLAIMED")

    lineage = load("conformance/AIFC-NORMATIVE-PROFILE-LINEAGE-v1.json")
    records = lineage.get("records", [])
    if len(records) != 1:
        fail("signature preimage lineage must initially contain exactly the issued v1 profile")
    record = records[0]
    if record.get("profile_id") != "AIFC-ED25519-DIRECT-TYPED-V1":
        fail("issued signature profile identity drift")
    if record.get("framing_id") != "TAG_U8_LENGTH_U64BE_V1":
        fail("issued signature framing identity drift")
    if record.get("status") != "HISTORICALLY_ISSUED_TESTED_SCOPE":
        fail("issued signature profile status drift")
    if record.get("successor_profile_id") is not None:
        fail("a successor profile must not be invented without explicit lineage evidence")
    print("NORMATIVE_PROFILE_LINEAGE_VALID = PASS_FOR_ISSUED_V1_HISTORY")

    v06 = (VERIFIER / "full_admission_v06.py").read_text(encoding="utf-8")
    if "from full_admission_v03 import verify_replay_manifest as verify_v03" not in v06:
        fail("INHERITED_HARDENING_LAYER_OMISSION:v0.6 missing mandatory v0.3 import")
    if "result = verify_v03(manifest, resolver)" not in v06:
        fail("INHERITED_HARDENING_LAYER_OMISSION:v0.6 does not execute v0.3")
    if "from full_admission_v02 import" in v06:
        fail("INHERITED_HARDENING_LAYER_OMISSION:v0.6 bypasses v0.3 via v0.2 import")
    print("CURRENT_V06_PREDECESSOR_COMPOSITION_GUARD = PASS")

    spec = (ROOT / "spec" / "ASSURANCE-MONOTONICITY-v1.md").read_text(encoding="utf-8")
    for phrase in (
        "A newer verifier MUST NOT forget a rejection learned by a mandatory predecessor.",
        "Assurance must be monotone unless the weakening itself carries proof.",
        "INHERITED_HARDENING_LAYER_OMISSION",
        "RELEASE_GATE_REGRESSION",
        "SAME_SCHEMA_ID_LANGUAGE_MUTATION",
    ):
        if phrase not in spec:
            fail(f"normative assurance invariant missing phrase: {phrase}")

    print("VERIFIER_ADMISSION_MONOTONICITY_ENGINE = IMPLEMENTED")
    print("VERIFIER_ADMISSION_MONOTONICITY_NEXT_SUCCESSOR = REQUIRES_REAL_WRAPPED_FIXTURE_REPLAY")
    print("SIGNATURE_PREIMAGE_RESOLVER_DERIVED_REPLAY = REQUIRED_NEW_PROFILE_VERSION_NOT_RETROACTIVE_PASS")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
