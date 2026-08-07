#!/usr/bin/env python3
"""Verify an AIFC CI attestation against the exact checked-out source tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import canonical_json_bytes, raw_evidence_hash  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402


class AttestationRejected(ValueError):
    pass


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_set(paths: list[Path]) -> dict:
    rows = []
    for path in sorted({p.resolve() for p in paths}):
        rows.append({"path": path.relative_to(ROOT.resolve()).as_posix(), "raw_sha256": raw_sha(path)})
    payload = canonical_json_bytes({"schema": "AIFC/source-set-manifest/v1", "files": rows})
    return {
        "manifest_sha256": hashlib.sha256(b"AIFC:SOURCE_SET_MANIFEST:v1\x00" + payload).hexdigest(),
        "file_count": len(rows),
    }


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AttestationRejected(code)


def verify_report(row: dict, artifact_dir: Path) -> None:
    path = artifact_dir / row["path"]
    require(path.is_file(), f"CI_REPORT_MISSING:{row['path']}")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == row["raw_sha256"], f"CI_REPORT_RAW_HASH_MISMATCH:{row['path']}")
    require(raw_evidence_hash(raw) == row["aifc_raw_evidence_hash"], f"CI_REPORT_AIFC_HASH_MISMATCH:{row['path']}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--attestation", required=True)
    p.add_argument("--artifact-dir", required=True)
    p.add_argument("--sidecar")
    args = p.parse_args()

    artifact_dir = Path(args.artifact_dir)
    attestation_path = Path(args.attestation)
    att = json.loads(attestation_path.read_text(encoding="utf-8"))
    validate_protocol_object(att, "AIFC/verifier-ci-attestation/v1")

    require(att["tested_source_commit_sha"] == git("rev-parse", "HEAD"), "DETACHED_CI_PASS_ATTESTATION:SOURCE_COMMIT")
    require(att["tested_tree_sha"] == git("rev-parse", "HEAD^{tree}"), "DETACHED_CI_PASS_ATTESTATION:TREE")

    workflow_path = ROOT / att["workflow"]["path"]
    require(workflow_path.is_file(), "ATTESTED_WORKFLOW_FILE_MISSING")
    require(raw_sha(workflow_path) == att["workflow"]["raw_sha256"], "DETACHED_CI_PASS_ATTESTATION:WORKFLOW_HASH")

    expected_sets = {
        "schemas": source_set(list((ROOT / "schemas").glob("*.schema.json"))),
        "verifier_source": source_set(list((ROOT / "reference" / "verifier").glob("*.py")) + [ROOT / "reference" / "verifier" / "requirements.txt"]),
        "test_corpus": source_set(list((ROOT / "reference" / "tests").glob("test_*.py"))),
        "checkers": source_set([
            ROOT / "tools" / "check_repo_conformance.py",
            ROOT / "tools" / "check_preregistration_conformance.py",
            ROOT / "tools" / "check_self_audit_conformance.py",
            ROOT / "tools" / "build_verifier_ci_attestation.py",
            ROOT / "tools" / "verify_verifier_ci_attestation.py",
        ]),
    }
    for name, expected in expected_sets.items():
        require(att["bound_source_sets"][name] == expected, f"DETACHED_CI_PASS_ATTESTATION:{name.upper()}_SET")

    for key in ("base_conformance", "preregistration_conformance", "self_audit_conformance", "unittest"):
        verify_report(att["reports"][key], artifact_dir)

    exits = [
        att["reports"]["base_conformance"]["exit_code"],
        att["reports"]["preregistration_conformance"]["exit_code"],
        att["reports"]["self_audit_conformance"]["exit_code"],
        att["reports"]["unittest"]["exit_code"],
    ]
    expected_status = "PASS" if exits == [0, 0, 0, 0] else "FAIL"
    require(att["overall_status"] == expected_status, "CI_ATTESTATION_STATUS_REPORT_MISMATCH")

    raw = attestation_path.read_bytes()
    if args.sidecar:
        side = json.loads(Path(args.sidecar).read_text(encoding="utf-8"))
        require(side.get("raw_sha256") == hashlib.sha256(raw).hexdigest(), "CI_ATTESTATION_SIDECAR_RAW_HASH_MISMATCH")
        expected_protocol = hashlib.sha256(b"AIFC:VERIFIER_CI_ATTESTATION:v1\x00" + raw).hexdigest()
        require(side.get("protocol_content_hash") == expected_protocol, "CI_ATTESTATION_SIDECAR_PROTOCOL_HASH_MISMATCH")

    print(f"CI_ATTESTATION = {att['overall_status']}")
    print(f"TESTED_SOURCE_COMMIT_SHA = {att['tested_source_commit_sha']}")
    print(f"TESTED_TREE_SHA = {att['tested_tree_sha']}")
    print(f"WORKFLOW_RUN_ID = {att['workflow']['run_id']}")
    print(f"WORKFLOW_JOB_ID = {att['workflow']['job_id']}")
    print(f"UNIT_TEST_COUNT = {att['reports']['unittest']['test_count']}")
    print("DETACHED_CI_PASS_ATTESTATION = REJECTED_BY_BINDING_CHECKS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AttestationRejected as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
