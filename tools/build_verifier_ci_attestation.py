#!/usr/bin/env python3
"""Build an out-of-tree AIFC/verifier-ci-attestation/v1 artifact."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import canonical_json_bytes, raw_evidence_hash  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_set(paths: Iterable[Path]) -> dict:
    rows = []
    for path in sorted({p.resolve() for p in paths}):
        rel = path.relative_to(ROOT.resolve()).as_posix()
        rows.append({"path": rel, "raw_sha256": raw_sha(path)})
    payload = canonical_json_bytes({"schema": "AIFC/source-set-manifest/v1", "files": rows})
    digest = hashlib.sha256(b"AIFC:SOURCE_SET_MANIFEST:v1\x00" + payload).hexdigest()
    return {"manifest_sha256": digest, "file_count": len(rows)}


def report(path: Path, exit_code: int) -> dict:
    raw = path.read_bytes()
    return {
        "path": path.name,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "aifc_raw_evidence_hash": raw_evidence_hash(raw),
        "exit_code": exit_code,
    }


def read_exit_code(path: Path) -> int:
    text = path.read_text(encoding="utf-8").strip()
    value = int(text)
    if value < 0 or value > 255:
        raise ValueError(f"invalid exit code in {path}: {value}")
    return value


def test_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="strict")
    match = re.search(r"Ran\s+(\d+)\s+tests?", text)
    if not match:
        raise ValueError("unittest report missing 'Ran N tests' summary")
    return int(match.group(1))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workflow-path", required=True)
    p.add_argument("--base-report", required=True)
    p.add_argument("--base-exit", required=True)
    p.add_argument("--self-audit-report", required=True)
    p.add_argument("--self-audit-exit", required=True)
    p.add_argument("--unittest-report", required=True)
    p.add_argument("--unittest-exit", required=True)
    p.add_argument("--job-id", required=True, type=int)
    p.add_argument("--job-name", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()

    workflow = ROOT / args.workflow_path
    base_report = Path(args.base_report)
    self_report = Path(args.self_audit_report)
    unittest_report = Path(args.unittest_report)
    base_exit = read_exit_code(Path(args.base_exit))
    self_exit = read_exit_code(Path(args.self_audit_exit))
    unit_exit = read_exit_code(Path(args.unittest_exit))

    schemas = list((ROOT / "schemas").glob("*.schema.json"))
    verifier_source = list((ROOT / "reference" / "verifier").glob("*.py")) + [ROOT / "reference" / "verifier" / "requirements.txt"]
    tests = list((ROOT / "reference" / "tests").glob("test_*.py"))
    checkers = [
        ROOT / "tools" / "check_repo_conformance.py",
        ROOT / "tools" / "check_preregistration_conformance.py",
        ROOT / "tools" / "check_self_audit_conformance.py",
        ROOT / "tools" / "build_verifier_ci_attestation.py",
        ROOT / "tools" / "verify_verifier_ci_attestation.py",
    ]

    status = "PASS" if (base_exit, self_exit, unit_exit) == (0, 0, 0) else "FAIL"
    attestation = {
        "schema": "AIFC/verifier-ci-attestation/v1",
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.3.0-self-audit",
        "repository": "Hawkar-usls/AIFC",
        "tested_source_commit_sha": git("rev-parse", "HEAD"),
        "tested_tree_sha": git("rev-parse", "HEAD^{tree}"),
        "workflow": {
            "path": args.workflow_path,
            "raw_sha256": raw_sha(workflow),
            "run_id": int(os.environ["GITHUB_RUN_ID"]),
            "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
            "job_id": args.job_id,
            "job_name": args.job_name,
            "event_name": os.environ.get("GITHUB_EVENT_NAME", "unknown"),
            "runner_os": os.environ.get("RUNNER_OS", "unknown"),
            "python_version": sys.version.split()[0],
        },
        "bound_source_sets": {
            "schemas": source_set(schemas),
            "verifier_source": source_set(verifier_source),
            "test_corpus": source_set(tests),
            "checkers": source_set(checkers),
        },
        "reports": {
            "base_conformance": report(base_report, base_exit),
            "self_audit_conformance": report(self_report, self_exit),
            "unittest": {**report(unittest_report, unit_exit), "test_count": test_count(unittest_report)},
        },
        "overall_status": status,
        "claim_ceiling": {
            "implementation_a_pass": False,
            "aifc_v1_frozen": False,
            "physical_retrocausality": "NOT_OBSERVED",
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    validate_protocol_object(attestation, "AIFC/verifier-ci-attestation/v1")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "verifier-ci-attestation.json"
    out.write_bytes(canonical_json_bytes(attestation))
    raw = out.read_bytes()
    raw_digest = hashlib.sha256(raw).hexdigest()
    protocol_digest = hashlib.sha256(b"AIFC:VERIFIER_CI_ATTESTATION:v1\x00" + raw).hexdigest()
    sidecar = {
        "schema": "AIFC/verifier-ci-attestation-sidecar/v1",
        "raw_sha256": raw_digest,
        "protocol_content_hash": protocol_digest,
    }
    (out_dir / "verifier-ci-attestation.sha256.json").write_bytes(canonical_json_bytes(sidecar))
    print(f"CI_ATTESTATION_STATUS = {status}")
    print(f"TESTED_SOURCE_COMMIT_SHA = {attestation['tested_source_commit_sha']}")
    print(f"TESTED_TREE_SHA = {attestation['tested_tree_sha']}")
    print(f"TEST_COUNT = {attestation['reports']['unittest']['test_count']}")
    print(f"ATTESTATION_RAW_SHA256 = {raw_digest}")
    print(f"ATTESTATION_PROTOCOL_HASH = {protocol_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
